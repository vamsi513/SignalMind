from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from app.db.models import Incident
from app.db.session import SessionLocal


CANONICAL_COLUMNS = {
    "failed_logins": ["failed_logins", "ct_srv_src", "ct_dst_ltm", "num_failed_logins"],
    "geo_distance_km": ["geo_distance_km", "ct_dst_src_ltm", "dur", "service_entropy"],
    "off_hours_access": ["off_hours_access", "is_ftp_login", "is_sm_ips_ports"],
    "privileged_action": ["privileged_action", "ct_ftp_cmd", "su_attempted"],
    "bytes_out_mb": ["bytes_out_mb", "sbytes", "src_bytes"],
    "distinct_ports_touched": ["distinct_ports_touched", "ct_dst_sport_ltm", "dst_port_count"],
    "process_entropy": ["process_entropy", "sttl", "dttl", "entropy"],
    "lateral_movement_score": ["lateral_movement_score", "ct_src_dport_ltm", "same_srv_rate"],
    "source_reputation": ["source_reputation", "sinpkt", "src_reputation"],
}


def _select_series(df: pd.DataFrame, candidates: list[str], default: float = 0.0) -> pd.Series:
    for name in candidates:
        if name in df.columns:
            return pd.to_numeric(df[name], errors="coerce").fillna(default)
    return pd.Series([default] * len(df))


def _scaled(series: pd.Series, upper_bound: float, minimum: float = 0.0, maximum: float = 1.0) -> pd.Series:
    clipped = series.clip(lower=0)
    if upper_bound <= 0:
        return pd.Series([minimum] * len(series))
    values = (clipped / upper_bound).clip(lower=minimum, upper=maximum)
    return values


def _severity_from_risk(risk: float) -> str:
    if risk >= 0.82:
        return "critical"
    if risk >= 0.62:
        return "high"
    if risk >= 0.38:
        return "medium"
    return "low"


def _infer_attack_family(row: pd.Series) -> str:
    text = " ".join(str(value).lower() for value in row.tolist())
    if "worm" in text or "backdoor" in text:
        return "malware-execution"
    if "dos" in text or "fuzz" in text or "recon" in text:
        return "lateral-movement"
    if "exploit" in text or "shellcode" in text:
        return "privilege-escalation"
    if "generic" in text or "analysis" in text:
        return "credential-abuse"
    return "data-exfiltration"


def _infer_label(df: pd.DataFrame) -> pd.Series:
    for column in ["label_high_risk", "label", "attack_cat", "class", "binary_label"]:
        if column not in df.columns:
            continue
        values = df[column].astype(str).str.lower()
        return values.apply(
            lambda value: 0
            if value in {"0", "normal", "benign", "false"}
            else 1
        )
    return pd.Series([0] * len(df))


def normalize_public_cyber_df(df: pd.DataFrame) -> pd.DataFrame:
    normalized = pd.DataFrame()
    normalized["failed_logins"] = _select_series(df, CANONICAL_COLUMNS["failed_logins"]).round().astype(int)
    normalized["geo_distance_km"] = _scaled(
        _select_series(df, CANONICAL_COLUMNS["geo_distance_km"]), upper_bound=5000, maximum=5000
    ) * 5000
    normalized["off_hours_access"] = (
        _select_series(df, CANONICAL_COLUMNS["off_hours_access"]).gt(0).astype(int)
    )
    normalized["privileged_action"] = (
        _select_series(df, CANONICAL_COLUMNS["privileged_action"]).gt(0).astype(int)
    )
    normalized["bytes_out_mb"] = _scaled(
        _select_series(df, CANONICAL_COLUMNS["bytes_out_mb"]), upper_bound=1_000_000, maximum=1
    ) * 1500
    normalized["distinct_ports_touched"] = _select_series(
        df, CANONICAL_COLUMNS["distinct_ports_touched"]
    ).clip(lower=1, upper=100).round().astype(int)
    normalized["process_entropy"] = (
        _scaled(_select_series(df, CANONICAL_COLUMNS["process_entropy"]), upper_bound=255) * 8.5
    ).clip(lower=2.0, upper=8.5)
    normalized["lateral_movement_score"] = _scaled(
        _select_series(df, CANONICAL_COLUMNS["lateral_movement_score"]), upper_bound=100
    )
    source_rep = _scaled(_select_series(df, CANONICAL_COLUMNS["source_reputation"]), upper_bound=1000)
    normalized["source_reputation"] = (1 - source_rep).clip(lower=0.0, upper=1.0)
    normalized["label_high_risk"] = _infer_label(df).astype(int)
    normalized["attack_family"] = df.apply(_infer_attack_family, axis=1)
    normalized["severity_label"] = normalized["label_high_risk"].apply(
        lambda value: "high" if value else "medium"
    )
    return normalized


def ingest_csv_dataset(file_path: Path, dataset_name: str) -> int:
    df = pd.read_csv(file_path)
    if df.empty:
        raise ValueError("Uploaded CSV is empty.")
    normalized = normalize_public_cyber_df(df)
    if normalized["label_high_risk"].nunique() < 2:
        raise ValueError("Dataset must contain at least two label classes after normalization.")
    now = datetime.utcnow()
    incidents = []
    for idx, row in normalized.iterrows():
        risk_score = (
            0.18 * min(row["failed_logins"] / 20, 1)
            + 0.10 * min(row["geo_distance_km"] / 4000, 1)
            + 0.08 * row["off_hours_access"]
            + 0.12 * row["privileged_action"]
            + 0.14 * min(row["bytes_out_mb"] / 1500, 1)
            + 0.09 * min(row["distinct_ports_touched"] / 40, 1)
            + 0.10 * min(row["process_entropy"] / 8.5, 1)
            + 0.13 * row["lateral_movement_score"]
            + 0.06 * (1 - row["source_reputation"])
        )
        severity = _severity_from_risk(risk_score)
        incidents.append(
            Incident(
                event_ts=now - timedelta(minutes=int(idx)),
                source_ip="dataset-import",
                user_id="public-dataset",
                asset_id=dataset_name,
                title="Imported public cyber event",
                summary=(
                    "Normalized record imported from public cybersecurity dataset "
                    f"'{dataset_name}' for supervised risk evaluation."
                ),
                severity_label=severity,
                attack_family=row["attack_family"],
                failed_logins=int(row["failed_logins"]),
                geo_distance_km=float(row["geo_distance_km"]),
                off_hours_access=int(row["off_hours_access"]),
                privileged_action=int(row["privileged_action"]),
                bytes_out_mb=float(row["bytes_out_mb"]),
                distinct_ports_touched=int(row["distinct_ports_touched"]),
                process_entropy=float(row["process_entropy"]),
                lateral_movement_score=float(row["lateral_movement_score"]),
                source_reputation=float(row["source_reputation"]),
                risk_score=float(risk_score),
                anomaly_score=0.0,
                risk_explanation="",
                label_high_risk=int(row["label_high_risk"]),
            )
        )

    with SessionLocal() as session:
        session.add_all(incidents)
        session.commit()
    return len(incidents)
