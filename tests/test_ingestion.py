from pathlib import Path

import pandas as pd

from app.db.models import Incident
from app.db.session import SessionLocal
from app.services.data_ingestion import ingest_csv_dataset, normalize_public_cyber_df
from app.services.dataset_context import describe_dataset_scope


def test_normalize_public_cyber_df_maps_two_classes() -> None:
    df = pd.DataFrame(
        {
            "ct_srv_src": [2, 12],
            "ct_dst_ltm": [3, 14],
            "is_ftp_login": [0, 1],
            "ct_ftp_cmd": [0, 2],
            "sbytes": [15000, 410000],
            "ct_dst_sport_ltm": [4, 24],
            "sttl": [48, 150],
            "ct_src_dport_ltm": [3, 22],
            "sinpkt": [900, 220],
            "attack_cat": ["Normal", "Exploits"],
            "label": [0, 1],
        }
    )

    normalized = normalize_public_cyber_df(df)

    assert len(normalized) == 2
    assert sorted(normalized["label_high_risk"].unique().tolist()) == [0, 1]


def test_ingest_csv_dataset_uses_sample_file(tmp_path: Path) -> None:
    source = Path("data/raw/sample_unsw_nb15_like.csv")
    target = tmp_path / "sample.csv"
    target.write_text(source.read_text())

    count = ingest_csv_dataset(target, dataset_name="sample-test")

    assert count == 10


def test_dataset_scope_detects_mixed_sources() -> None:
    incidents = [
        Incident(
            event_ts=pd.Timestamp("2026-03-03"),
            source_ip="10.0.0.1",
            user_id="user-01",
            asset_id="asset-01",
            title="synthetic",
            summary="synthetic",
            severity_label="low",
            attack_family="credential-abuse",
            failed_logins=1,
            geo_distance_km=10.0,
            off_hours_access=0,
            privileged_action=0,
            bytes_out_mb=10.0,
            distinct_ports_touched=1,
            process_entropy=2.5,
            lateral_movement_score=0.1,
            source_reputation=0.9,
            risk_score=0.1,
            anomaly_score=0.0,
            risk_explanation="",
            label_high_risk=0,
        ),
        Incident(
            event_ts=pd.Timestamp("2026-03-03"),
            source_ip="dataset-import",
            user_id="public-dataset",
            asset_id="unsw-sample",
            title="imported",
            summary="imported",
            severity_label="high",
            attack_family="data-exfiltration",
            failed_logins=12,
            geo_distance_km=1200.0,
            off_hours_access=1,
            privileged_action=1,
            bytes_out_mb=500.0,
            distinct_ports_touched=10,
            process_entropy=6.0,
            lateral_movement_score=0.7,
            source_reputation=0.2,
            risk_score=0.8,
            anomaly_score=10.0,
            risk_explanation="",
            label_high_risk=1,
        ),
    ]

    assert describe_dataset_scope(incidents) == "mixed:synthetic-demo,unsw-sample"
