from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
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


def _build_sequences(df: pd.DataFrame, window_size: int = 5) -> np.ndarray:
    values = df[FEATURE_COLUMNS].to_numpy(dtype=np.float32)
    if len(values) < window_size:
        padding = np.repeat(values[-1][None, :], window_size - len(values), axis=0)
        values = np.concatenate([values, padding], axis=0)
    sequences = []
    for idx in range(len(values) - window_size + 1):
        sequences.append(values[idx : idx + window_size])
    return np.stack(sequences)


def train_sequence_model(df: pd.DataFrame, output_path: Path, epochs: int = 8) -> Path:
    model = LSTMAutoencoder(input_dim=len(FEATURE_COLUMNS))
    sequences = _build_sequences(df)
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
    meta = {"window_size": 5, "input_dim": len(FEATURE_COLUMNS)}
    joblib.dump(meta, output_path.with_suffix(".meta.pkl"))
    return output_path


def score_sequences(model_path: Path, df: pd.DataFrame) -> list[float]:
    meta = joblib.load(model_path.with_suffix(".meta.pkl"))
    window_size = meta["window_size"]
    model = LSTMAutoencoder(input_dim=meta["input_dim"])
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()

    sequences = _build_sequences(df, window_size=window_size)
    tensor = torch.tensor(sequences)
    with torch.no_grad():
        reconstruction = model(tensor)
        errors = torch.mean((reconstruction - tensor) ** 2, dim=(1, 2)).numpy()

    padded = [float(errors[0])] * (window_size - 1) + [float(value) for value in errors]
    return padded[: len(df)]

