from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_ts: Mapped[datetime] = mapped_column(DateTime, index=True)
    source_ip: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    asset_id: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(Text)
    severity_label: Mapped[str] = mapped_column(String(32), index=True)
    attack_family: Mapped[str] = mapped_column(String(64), index=True)
    failed_logins: Mapped[int] = mapped_column(Integer)
    geo_distance_km: Mapped[float] = mapped_column(Float)
    off_hours_access: Mapped[int] = mapped_column(Integer)
    privileged_action: Mapped[int] = mapped_column(Integer)
    bytes_out_mb: Mapped[float] = mapped_column(Float)
    distinct_ports_touched: Mapped[int] = mapped_column(Integer)
    process_entropy: Mapped[float] = mapped_column(Float)
    lateral_movement_score: Mapped[float] = mapped_column(Float)
    source_reputation: Mapped[float] = mapped_column(Float)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    anomaly_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_explanation: Mapped[str] = mapped_column(Text, default="")
    label_high_risk: Mapped[int] = mapped_column(Integer, index=True)


class Runbook(Base):
    __tablename__ = "runbooks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    content: Mapped[str] = mapped_column(Text)


class ModelEvaluation(Base):
    __tablename__ = "model_evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, index=True, default=datetime.utcnow)
    dataset_name: Mapped[str] = mapped_column(String(128), index=True)
    sample_count: Mapped[int] = mapped_column(Integer)
    classical_auc: Mapped[float] = mapped_column(Float)
    classical_precision: Mapped[float] = mapped_column(Float)
    classical_recall: Mapped[float] = mapped_column(Float)
    classical_f1: Mapped[float] = mapped_column(Float)
    anomaly_mean_normal: Mapped[float] = mapped_column(Float)
    anomaly_mean_high_risk: Mapped[float] = mapped_column(Float)
    artifact_path: Mapped[str] = mapped_column(String(255))
