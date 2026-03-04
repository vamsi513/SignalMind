from app.schemas.incident import (
    EvidenceItem,
    IncidentDecision,
    IncidentRead,
    RecommendedAction,
)


def build_incident_prompt(
    incident: IncidentRead,
    similar_incidents: list[str],
    runbooks: list[str],
) -> str:
    return (
        "You are generating a cyber incident decision brief.\n"
        f"Title: {incident.title}\n"
        f"Severity label: {incident.severity_label}\n"
        f"Risk score: {incident.risk_score:.3f}\n"
        f"Anomaly score: {incident.anomaly_score:.3f}\n"
        f"Risk drivers: {incident.risk_explanation}\n"
        f"Attack family: {incident.attack_family}\n"
        f"Summary: {incident.summary}\n"
        f"Failed logins: {incident.failed_logins}\n"
        f"Bytes out MB: {incident.bytes_out_mb:.1f}\n"
        f"Lateral movement score: {incident.lateral_movement_score:.2f}\n"
        f"Source reputation: {incident.source_reputation:.2f}\n"
        f"Similar incidents: {', '.join(similar_incidents) or 'none'}\n"
        f"Runbooks: {', '.join(runbooks) or 'none'}\n"
        "Return a concise analyst decision with summary, rationale, evidence, actions, and questions."
    )


def build_fallback_decision(
    incident: IncidentRead,
    similar_incidents: list[str],
    runbooks: list[str],
) -> IncidentDecision:
    severity_rationale = (
        f"Severity is {incident.severity_label} because risk={incident.risk_score:.2f}, "
        f"anomaly={incident.anomaly_score:.1f}, and the strongest risk drivers are {incident.risk_explanation}."
    )
    evidence = [
        EvidenceItem(kind="model-signal", detail=f"Risk score {incident.risk_score:.2f}"),
        EvidenceItem(kind="sequence-anomaly", detail=f"Anomaly score {incident.anomaly_score:.1f}"),
        EvidenceItem(kind="feature-driver", detail=incident.risk_explanation or "No feature explanation available"),
        EvidenceItem(
            kind="retrieval",
            detail=f"Similar prior incidents: {', '.join(similar_incidents) or 'none'}",
        ),
    ]
    actions = [
        RecommendedAction(
            priority="P1",
            title=runbooks[0] if runbooks else "Contain suspicious activity",
            rationale="Immediate containment reduces blast radius while preserving evidence.",
        ),
        RecommendedAction(
            priority="P2",
            title="Validate identity and endpoint behavior",
            rationale="The current pattern suggests account misuse or staged lateral movement.",
        ),
        RecommendedAction(
            priority="P3",
            title="Review outbound transfer scope",
            rationale="Outbound volume and behavioral drift may indicate exfiltration or staging.",
        ),
    ]
    questions = [
        "Did this user or asset show the same risk drivers in prior incidents?",
        "Do endpoint and identity logs confirm privileged or off-hours behavior?",
        "Is the outbound activity consistent with approved business workflows?",
    ]
    return IncidentDecision(
        summary=(
            f"{incident.attack_family.replace('-', ' ').title()} activity was detected on {incident.asset_id} "
            f"with elevated modeled risk and abnormal sequence behavior."
        ),
        severity_rationale=severity_rationale,
        confidence="medium-high",
        evidence=evidence,
        recommended_actions=actions,
        investigation_questions=questions,
    )


def render_incident_brief(
    incident: IncidentRead,
    similar_incidents: list[str],
    runbooks: list[str],
) -> str:
    decision = build_fallback_decision(incident, similar_incidents, runbooks)
    action_text = "; ".join(
        f"{action.priority} {action.title}: {action.rationale}"
        for action in decision.recommended_actions
    )
    evidence_text = "; ".join(item.detail for item in decision.evidence[:4])
    return (
        f"Severity assessment: {incident.severity_label}. "
        f"Predicted risk score is {incident.risk_score:.2f} and sequence anomaly score is "
        f"{incident.anomaly_score:.4f}. "
        f"Top risk drivers: {incident.risk_explanation or 'not available'}. "
        f"Decision summary: {decision.summary}. "
        f"Evidence considered: {evidence_text}. "
        f"Recommended next actions: {action_text}."
    )
