import random
from datetime import datetime, timedelta

from app.db.models import Incident, Runbook

ATTACK_FAMILIES = [
    "credential-abuse",
    "data-exfiltration",
    "privilege-escalation",
    "lateral-movement",
    "malware-execution",
]

RUNBOOKS = [
    ("Credential Abuse Containment", "identity", "Reset credentials, revoke sessions, enforce MFA, review IAM logs."),
    ("Data Exfiltration Response", "network", "Block egress, preserve packet evidence, identify exposed records."),
    ("Lateral Movement Investigation", "endpoint", "Isolate hosts, review east-west traffic, inspect admin shares."),
    ("Privilege Escalation Triage", "iam", "Audit role changes, disable suspect accounts, verify policy drift."),
]

RISK_PROFILES = {
    "benign": {
        "failed_logins_mean": 2,
        "geo_distance_mean": 180,
        "off_hours_weights": [0.92, 0.08],
        "privileged_weights": [0.95, 0.05],
        "bytes_out_mean": 90,
        "ports_mean": 4,
        "entropy_mean": 3.2,
        "lateral_mean": 0.08,
        "reputation_mean": 0.88,
    },
    "watch": {
        "failed_logins_mean": 6,
        "geo_distance_mean": 850,
        "off_hours_weights": [0.70, 0.30],
        "privileged_weights": [0.82, 0.18],
        "bytes_out_mean": 260,
        "ports_mean": 10,
        "entropy_mean": 4.8,
        "lateral_mean": 0.28,
        "reputation_mean": 0.62,
    },
    "critical": {
        "failed_logins_mean": 15,
        "geo_distance_mean": 3400,
        "off_hours_weights": [0.18, 0.82],
        "privileged_weights": [0.25, 0.75],
        "bytes_out_mean": 1100,
        "ports_mean": 30,
        "entropy_mean": 7.2,
        "lateral_mean": 0.78,
        "reputation_mean": 0.22,
    },
}


def _severity_from_signal(score: float) -> str:
    if score >= 0.82:
        return "critical"
    if score >= 0.62:
        return "high"
    if score >= 0.38:
        return "medium"
    return "low"


def generate_incidents(count: int) -> list[Incident]:
    random.seed(42)
    now = datetime.utcnow()
    incidents: list[Incident] = []
    for idx in range(count):
        profile_name = "benign" if idx % 5 in {0, 1} else "watch" if idx % 5 in {2, 3} else "critical"
        profile = RISK_PROFILES[profile_name]
        attack_family = random.choice(ATTACK_FAMILIES)
        failed_logins = max(0, int(random.gauss(profile["failed_logins_mean"], 3)))
        geo_distance_km = abs(random.gauss(profile["geo_distance_mean"], 500))
        off_hours_access = random.choices([0, 1], weights=profile["off_hours_weights"])[0]
        privileged_action = random.choices([0, 1], weights=profile["privileged_weights"])[0]
        bytes_out_mb = abs(random.gauss(profile["bytes_out_mean"], 180))
        distinct_ports_touched = max(1, int(random.gauss(profile["ports_mean"], 6)))
        process_entropy = min(8.5, max(2.2, random.gauss(profile["entropy_mean"], 0.9)))
        lateral_movement_score = min(1.0, max(0.0, random.gauss(profile["lateral_mean"], 0.15)))
        source_reputation = min(1.0, max(0.0, random.gauss(profile["reputation_mean"], 0.12)))

        latent_risk = (
            0.12 * min(failed_logins / 15, 1)
            + 0.10 * min(geo_distance_km / 4000, 1)
            + 0.08 * off_hours_access
            + 0.12 * privileged_action
            + 0.15 * min(bytes_out_mb / 1200, 1)
            + 0.08 * min(distinct_ports_touched / 40, 1)
            + 0.12 * min(process_entropy / 8.5, 1)
            + 0.16 * lateral_movement_score
            + 0.07 * (1 - source_reputation)
        )
        high_risk = int(latent_risk >= 0.55)
        severity = _severity_from_signal(latent_risk)
        title = f"{attack_family.replace('-', ' ').title()} event on asset-{idx % 18:02d}"
        summary = (
            f"Suspicious {attack_family} pattern observed for user-{idx % 34:02d} "
            f"from source 10.24.{idx % 16}.{idx % 255} with elevated behavioral drift."
        )

        incidents.append(
            Incident(
                event_ts=now - timedelta(minutes=15 * idx),
                source_ip=f"10.24.{idx % 16}.{idx % 255}",
                user_id=f"user-{idx % 34:02d}",
                asset_id=f"asset-{idx % 18:02d}",
                title=title,
                summary=summary,
                severity_label=severity,
                attack_family=attack_family,
                failed_logins=failed_logins,
                geo_distance_km=geo_distance_km,
                off_hours_access=off_hours_access,
                privileged_action=privileged_action,
                bytes_out_mb=bytes_out_mb,
                distinct_ports_touched=distinct_ports_touched,
                process_entropy=process_entropy,
                lateral_movement_score=lateral_movement_score,
                source_reputation=source_reputation,
                risk_score=latent_risk,
                anomaly_score=0.0,
                label_high_risk=high_risk,
            )
        )
    return incidents


def generate_runbooks() -> list[Runbook]:
    return [Runbook(name=name, category=category, content=content) for name, category, content in RUNBOOKS]
