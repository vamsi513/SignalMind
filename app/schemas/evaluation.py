from datetime import datetime

from pydantic import BaseModel


class ModelEvaluationRead(BaseModel):
    id: int
    created_at: datetime
    dataset_name: str
    sample_count: int
    classical_auc: float
    classical_precision: float
    classical_recall: float
    classical_f1: float
    anomaly_mean_normal: float
    anomaly_mean_high_risk: float
    artifact_path: str

    model_config = {"from_attributes": True}

