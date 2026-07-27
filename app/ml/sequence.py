from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import StandardScaler
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from app.ml.features import FEATURE_COLUMNS


class LSTMAutoencoder(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 32):
        super().__init__()
        self.encoder = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        self.decoder = nn.LSTM(hidden_dim, hidden_dim, batch_first=True)
        self.output = nn.Linear(hidden_dim, input_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        encoded, _ = self.encoder(x)
        decoded, _ = self.decoder(encoded)
        return self.output(decoded)


def _build_sequences_per_entity(
    df: pd.DataFrame, values: np.ndarray, window_size: int = 5
) -> tuple[np.ndarray, np.ndarray]:
    """Build one sequence per row, using only that row's own entity history.

    Rows are grouped by user_id (each user's events form their own timeline)
    and sorted by event_ts within the group. Each row's sequence is the
    window_size most recent events for that user ending at that row, with
    the start of a user's history front-padded by repeating their first
    event. This keeps every window's temporal context confined to a single
    entity, rather than splicing together unrelated users' events just
    because they happen to be adjacent in the full chronological table.

    Returns (sequences, row_positions) where row_positions[i] is the
    positional index into `values` that sequences[i] ends on and should
    be attributed to.
    """
    sequences = []
    row_positions = []
    for _, group in df.groupby("user_id", sort=False):
        order = group.sort_values("event_ts").index.to_numpy()
        entity_values = values[order]
        front_pad = np.repeat(entity_values[0][None, :], window_size - 1, axis=0)
        padded = np.concatenate([front_pad, entity_values], axis=0)
        for i in range(len(entity_values)):
            sequences.append(padded[i : i + window_size])
            row_positions.append(order[i])
    return np.stack(sequences), np.array(row_positions)


def train_sequence_model(df: pd.DataFrame, output_path: Path, epochs: int = 30) -> Path:
    """Train an LSTM autoencoder as a per-user normal-behavior model.

    Trains only on non-anomalous rows (label_high_risk == 0) so the model
    learns to reconstruct normal behavior well; high-risk rows it never
    sees during training should reconstruct poorly, making reconstruction
    error a usable anomaly signal. Sequences are built per user_id (see
    _build_sequences_per_entity) so a window never mixes events from
    different users. Features are standardized first since raw scales
    vary by orders of magnitude (e.g. geo_distance_km vs binary flags),
    which otherwise makes the MSE loss ignore the smaller-scale (often
    most informative) features entirely.
    """
    if "label_high_risk" in df.columns:
        normal_df = df[df["label_high_risk"] == 0]
        if len(normal_df) >= 5:
            df = normal_df
    df = df.reset_index(drop=True)

    scaler = StandardScaler()
    scaled = scaler.fit_transform(df[FEATURE_COLUMNS]).astype(np.float32)

    sequences, _ = _build_sequences_per_entity(df, scaled)

    model = LSTMAutoencoder(input_dim=len(FEATURE_COLUMNS))
    dataset = TensorDataset(torch.tensor(sequences))
    loader = DataLoader(dataset, batch_size=32, shuffle=True)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.MSELoss()
    model.train()

    for _ in range(epochs):
        for (batch,) in loader:
            optimizer.zero_grad()
            reconstruction = model(batch)
            loss = criterion(reconstruction, batch)
            loss.backward()
            optimizer.step()

    torch.save(model.state_dict(), output_path)
    meta = {"window_size": 5, "input_dim": len(FEATURE_COLUMNS), "scaler": scaler}
    joblib.dump(meta, output_path.with_suffix(".meta.pkl"))
    return output_path


def score_sequences(model_path: Path, df: pd.DataFrame) -> list[float]:
    meta = joblib.load(model_path.with_suffix(".meta.pkl"))
    window_size = meta["window_size"]
    scaler: StandardScaler = meta["scaler"]
    model = LSTMAutoencoder(input_dim=meta["input_dim"])
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()

    df = df.reset_index(drop=True)
    scaled = scaler.transform(df[FEATURE_COLUMNS]).astype(np.float32)
    sequences, row_positions = _build_sequences_per_entity(df, scaled, window_size=window_size)

    tensor = torch.tensor(sequences)
    with torch.no_grad():
        reconstruction = model(tensor)
        errors = torch.mean((reconstruction - tensor) ** 2, dim=(1, 2)).numpy()

    scores = np.zeros(len(df), dtype=np.float32)
    scores[row_positions] = errors
    return [float(value) for value in scores]
