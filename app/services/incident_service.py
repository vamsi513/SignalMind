from pathlib import Path
from typing import Optional

import pandas as pd

from app.core.config import get_settings
from app.db.models import Incident, Runbook
from app.db.session import SessionLocal
from app.llm.briefing import build_fallback_decision, build_incident_prompt, render_incident_brief
from app.llm.provider import get_decision_provider
from app.ml.classical import explain_risk, predict_risk, train_risk_model
from app.ml.sequence import score_sequences, train_sequence_model
from app.retrieval.similarity import retrieve_similar
from app.schemas.incident import IncidentBriefResponse, IncidentRead, ModelTrainingResponse
from app.services.dataset_context import describe_dataset_scope


def _incident_to_schema(incident: Incident) -> IncidentRead:
    return IncidentRead.model_validate(incident)


def list_incidents(limit: int = 50) -> list[IncidentRead]:
    with SessionLocal() as session:
        incidents = session.query(Incident).order_by(Incident.event_ts.desc()).limit(limit).all()
        return [_incident_to_schema(incident) for incident in incidents]


def get_incident(incident_id: int) -> Optional[IncidentRead]:
    with SessionLocal() as session:
        incident = session.get(Incident, incident_id)
        return _incident_to_schema(incident) if incident else None


def _load_dataframe(session) -> pd.DataFrame:
    incidents = session.query(Incident).order_by(Incident.event_ts.asc()).all()
    rows = [
        {
            "id": incident.id,
            "event_ts": incident.event_ts,
            "user_id": incident.user_id,
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


def train_models() -> ModelTrainingResponse:
    settings = get_settings()
    classical_model_path = Path(settings.artifact_dir) / "risk_model.joblib"
    sequence_model_path = Path(settings.artifact_dir) / "sequence_autoencoder.pt"

    with SessionLocal() as session:
        df = _load_dataframe(session)
        if df.empty:
            raise ValueError("No incidents found. Bootstrap demo data first.")

        train_risk_model(df, classical_model_path)
        train_sequence_model(df, sequence_model_path)
        risk_scores = predict_risk(classical_model_path, df)
        risk_explanations = explain_risk(classical_model_path, df)
        anomaly_scores = score_sequences(sequence_model_path, df)

        incidents = session.query(Incident).order_by(Incident.event_ts.asc()).all()
        for incident, risk_score, anomaly_score, risk_explanation in zip(
            incidents, risk_scores, anomaly_scores, risk_explanations
        ):
            incident.risk_score = risk_score
            incident.anomaly_score = anomaly_score
            incident.risk_explanation = risk_explanation
        session.commit()

    return ModelTrainingResponse(
        incidents_used=len(df),
        classical_model_path=str(classical_model_path),
        sequence_model_path=str(sequence_model_path),
        dataset_name=describe_dataset_scope(incidents),
    )


def generate_incident_brief(incident_id: int) -> IncidentBriefResponse:
    with SessionLocal() as session:
        incident = session.get(Incident, incident_id)
        if not incident:
            raise ValueError("Incident not found")

        peers = session.query(Incident).filter(Incident.id != incident.id).all()
        peer_corpus = [f"{item.title}. {item.summary}" for item in peers]
        peer_labels = [f"#{item.id} {item.title}" for item in peers]
        similar_incidents = retrieve_similar(
            query=f"{incident.title}. {incident.summary}",
            corpus=peer_corpus,
            labels=peer_labels,
            top_k=3,
        )

        runbooks = session.query(Runbook).all()
        runbook_hits = retrieve_similar(
            query=f"{incident.attack_family} {incident.summary}",
            corpus=[item.content for item in runbooks],
            labels=[item.name for item in runbooks],
            top_k=2,
        )

        incident_schema = _incident_to_schema(incident)
        similar_labels = [item.label for item in similar_incidents]
        runbook_labels = [item.label for item in runbook_hits]
        prompt = build_incident_prompt(incident_schema, similar_labels, runbook_labels)
        fallback_decision = build_fallback_decision(incident_schema, similar_labels, runbook_labels)
        provider = get_decision_provider(get_settings().llm_provider)
        decision = provider.generate(prompt, fallback_decision)
        brief = render_incident_brief(incident_schema, similar_labels, runbook_labels)

        return IncidentBriefResponse(
            incident_id=incident.id,
            risk_score=incident.risk_score,
            anomaly_score=incident.anomaly_score,
            risk_explanation=incident.risk_explanation,
            similar_incidents=similar_labels,
            recommended_runbooks=runbook_labels,
            decision=decision,
            brief=brief,
        )
