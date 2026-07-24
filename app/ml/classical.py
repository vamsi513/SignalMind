from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, IsolationForest
from sklearn.inspection import permutation_importance
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.ml.features import FEATURE_COLUMNS


def train_risk_model(df: pd.DataFrame, output_path: Path) -> Path:
    X = df[FEATURE_COLUMNS]
    y = df["label_high_risk"]
    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("model", HistGradientBoostingClassifier(max_depth=6, random_state=42)),
        ]
    )
    pipeline.fit(X, y)
    importances = permutation_importance(
        pipeline,
        X,
        y,
        n_repeats=5,
        random_state=42,
        scoring="roc_auc",
    )
    payload = {
        "pipeline": pipeline,
        "feature_importances": {
            feature: float(score)
            for feature, score in zip(FEATURE_COLUMNS, importances.importances_mean)
        },
        "feature_baseline": {
            feature: float(X[feature].mean())
            for feature in FEATURE_COLUMNS
        },
    }
    joblib.dump(payload, output_path)
    return output_path


def predict_risk(model_path: Path, df: pd.DataFrame) -> list[float]:
    payload = joblib.load(model_path)
    model = payload["pipeline"]
    proba = model.predict_proba(df[FEATURE_COLUMNS])[:, 1]
    return [float(score) for score in proba]


def explain_risk(model_path: Path, df: pd.DataFrame, top_k: int = 3) -> list[str]:
    payload: dict[str, Any] = joblib.load(model_path)
    importances = payload["feature_importances"]
    baselines = payload["feature_baseline"]

    explanations = []
    for _, row in df[FEATURE_COLUMNS].iterrows():
        contributions = []
        for feature in FEATURE_COLUMNS:
            direction = -1.0 if feature == "source_reputation" else 1.0
            delta = float(row[feature]) - float(baselines[feature])
            contribution = direction * delta * max(importances.get(feature, 0.0), 0.0)
            contributions.append((feature, contribution, float(row[feature]), float(baselines[feature])))

        ranked = sorted(contributions, key=lambda item: abs(item[1]), reverse=True)[:top_k]
        explanation = "; ".join(
            f"{feature}={value:.2f} vs baseline {baseline:.2f}"
            for feature, _, value, baseline in ranked
        )
        explanations.append(explanation)
    return explanations


def train_isolation_forest(df: pd.DataFrame, output_path: Path) -> Path:
    """Train an unsupervised IsolationForest anomaly detector.

    Unlike train_risk_model (a supervised HistGradientBoostingClassifier),
    this fits on features only -- no label_high_risk column is used during
    training, matching how isolation forests are actually meant to be used.
    """
    X = df[FEATURE_COLUMNS]
    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("model", IsolationForest(n_estimators=200, contamination="auto", random_state=42)),
        ]
    )
    pipeline.fit(X)
    joblib.dump(pipeline, output_path)
    return output_path


def score_isolation_forest(model_path: Path, df: pd.DataFrame) -> list[float]:
    """Return anomaly scores in [0, 1], where higher means more anomalous.

    IsolationForest.score_samples returns higher values for inliers and
    lower (more negative) values for outliers, so the sign is flipped to
    match this module's "higher = riskier" convention used elsewhere
    (predict_risk, dashboard risk scores).
    """
    pipeline = joblib.load(model_path)
    raw_scores = pipeline.score_samples(df[FEATURE_COLUMNS])
    anomaly_scores = -raw_scores
    lo, hi = anomaly_scores.min(), anomaly_scores.max()
    if hi - lo < 1e-9:
        return [0.0 for _ in anomaly_scores]
    normalized = (anomaly_scores - lo) / (hi - lo)
    return [float(score) for score in normalized]
