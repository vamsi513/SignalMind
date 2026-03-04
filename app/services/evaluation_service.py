import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

from app.core.config import get_settings
from app.db.models import Incident, ModelEvaluation
from app.db.session import SessionLocal
from app.ml.classical import predict_risk, train_risk_model
from app.ml.sequence import score_sequences, train_sequence_model
from app.schemas.evaluation import ModelEvaluationRead
from app.services.dataset_context import describe_dataset_scope


def _load_dataframe(session) -> pd.DataFrame:
    incidents = session.query(Incident).order_by(Incident.event_ts.asc()).all()
    rows = [
        {
            "id": incident.id,
            "event_ts": incident.event_ts,
            "failed_logins": incident.failed_logins,
            "geo_distance_km": incident.geo_distance_km,
            "off_hours_access": incident.off_hours_access,
            "privileged_action": incident.privileged_action,
            "bytes_out_mb": incident.bytes_out_mb,
            "distinct_ports_touched": incident.distinct_ports_touched,
            "process_entropy": incident.process_entropy,
            "lateral_movement_score": incident.lateral_movement_score,
            "source_reputation": incident.source_reputation,
            "label_high_risk": incident.label_high_risk,
        }
        for incident in incidents
    ]
    return pd.DataFrame(rows)


def evaluate_models(dataset_name: str = "incident-db") -> ModelEvaluationRead:
    settings = get_settings()
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    classical_model_path = Path(settings.artifact_dir) / f"risk_model_eval_{timestamp}.joblib"
    sequence_model_path = Path(settings.artifact_dir) / f"sequence_eval_{timestamp}.pt"
    artifact_path = Path(settings.artifact_dir) / f"evaluation_{timestamp}.json"

    with SessionLocal() as session:
        incidents = session.query(Incident).order_by(Incident.event_ts.asc()).all()
        df = _load_dataframe(session)
        if df.empty or df["label_high_risk"].nunique() < 2:
            raise ValueError("Need labeled incident data with at least two classes for evaluation.")

        train_df, test_df = train_test_split(
            df, test_size=0.25, random_state=settings.random_seed, stratify=df["label_high_risk"]
        )
        chrono_df = df.sort_values("event_ts").reset_index(drop=True)
        split_idx = max(int(len(chrono_df) * 0.75), 1)
        anomaly_train_df = chrono_df.iloc[:split_idx]
        anomaly_test_df = chrono_df.iloc[split_idx:]
        if anomaly_test_df.empty:
            anomaly_test_df = chrono_df.iloc[-1:].copy()

        train_risk_model(train_df, classical_model_path)
        train_sequence_model(anomaly_train_df, sequence_model_path)

        risk_scores = np.array(predict_risk(classical_model_path, test_df))
        predicted_labels = (risk_scores >= 0.5).astype(int)
        anomaly_scores = np.array(score_sequences(sequence_model_path, anomaly_test_df))
        y_true = test_df["label_high_risk"].to_numpy()
        anomaly_true = anomaly_test_df["label_high_risk"].to_numpy()

        metrics = {
            "dataset_name": describe_dataset_scope(incidents),
            "sample_count": int(len(df)),
            "classical_auc": float(roc_auc_score(y_true, risk_scores)),
            "classical_precision": float(precision_score(y_true, predicted_labels, zero_division=0)),
            "classical_recall": float(recall_score(y_true, predicted_labels, zero_division=0)),
            "classical_f1": float(f1_score(y_true, predicted_labels, zero_division=0)),
            "anomaly_mean_normal": float(anomaly_scores[anomaly_true == 0].mean()) if np.any(anomaly_true == 0) else 0.0,
            "anomaly_mean_high_risk": float(anomaly_scores[anomaly_true == 1].mean()) if np.any(anomaly_true == 1) else 0.0,
            "artifact_path": str(artifact_path),
        }

        artifact_path.write_text(json.dumps(metrics, indent=2))
        record = ModelEvaluation(**metrics)
        session.add(record)
        session.commit()
        session.refresh(record)
        return ModelEvaluationRead.model_validate(record)


def latest_evaluations(limit: int = 10) -> list[ModelEvaluationRead]:
    with SessionLocal() as session:
        rows = (
            session.query(ModelEvaluation)
            .order_by(ModelEvaluation.created_at.desc())
            .limit(limit)
            .all()
        )
        return [ModelEvaluationRead.model_validate(row) for row in rows]
