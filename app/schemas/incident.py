from datetime import datetime

from pydantic import BaseModel


class EvidenceItem(BaseModel):
    kind: str
    detail: str


class RecommendedAction(BaseModel):
    priority: str
    title: str
    rationale: str


class IncidentDecision(BaseModel):
    summary: str
    severity_rationale: str
    confidence: str
    evidence: list[EvidenceItem]
    recommended_actions: list[RecommendedAction]
    investigation_questions: list[str]


class IncidentRead(BaseModel):
    id: int
    event_ts: datetime
    title: str
    summary: str
    severity_label: str
    attack_family: str
    source_ip: str
    user_id: str
    asset_id: str
    failed_logins: int
    geo_distance_km: float
    off_hours_access: int
    privileged_action: int
    bytes_out_mb: float
    distinct_ports_touched: int
    process_entropy: float
    lateral_movement_score: float
    source_reputation: float
    risk_score: float
    anomaly_score: float
    risk_explanation: str
    label_high_risk: int

    model_config = {"from_attributes": True}


class BootstrapResponse(BaseModel):
    incidents_created: int
    runbooks_created: int


class ModelTrainingResponse(BaseModel):
    incidents_used: int
    classical_model_path: str
    sequence_model_path: str
    dataset_name: str


class IncidentBriefResponse(BaseModel):
    incident_id: int
    risk_score: float
    anomaly_score: float
    risk_explanation: str
    similar_incidents: list[str]
    recommended_runbooks: list[str]
    decision: IncidentDecision
    brief: str
