import os
from typing import Any, Union

import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv("SIGNALMIND_API_URL", "http://127.0.0.1:8000/api/v1")


def call_api(method: str, path: str, timeout: int = 30) -> tuple[bool, Union[dict[str, Any], list[Any], str]]:
    try:
        response = requests.request(method, f"{API_URL}{path}", timeout=timeout)
        response.raise_for_status()
        if response.content:
            return True, response.json()
        return True, {}
    except requests.RequestException as exc:
        return False, str(exc)


def render_shell() -> None:
    st.set_page_config(page_title="SignalMind", layout="wide")
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(7, 61, 74, 0.25), transparent 34%),
                radial-gradient(circle at top right, rgba(155, 74, 35, 0.18), transparent 28%),
                linear-gradient(180deg, #06111b 0%, #07131e 48%, #091018 100%);
        }
        .hero {
            padding: 1.4rem 1.6rem;
            border: 1px solid rgba(88, 117, 132, 0.35);
            background: linear-gradient(135deg, rgba(8, 24, 37, 0.94), rgba(7, 16, 28, 0.88));
            border-radius: 18px;
            margin-bottom: 1rem;
            box-shadow: 0 24px 70px rgba(0, 0, 0, 0.28);
        }
        .hero-kicker {
            color: #7fd7c7;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            margin-bottom: 0.35rem;
        }
        .hero-title {
            color: #f5f7fb;
            font-size: 3.35rem;
            font-weight: 800;
            line-height: 0.95;
            margin: 0;
        }
        .hero-copy {
            color: #aab8c7;
            font-size: 1.05rem;
            max-width: 48rem;
            margin-top: 0.8rem;
        }
        .panel {
            border: 1px solid rgba(88, 117, 132, 0.28);
            border-radius: 16px;
            padding: 1rem 1rem 0.8rem 1rem;
            background: rgba(8, 20, 31, 0.88);
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.02);
        }
        .panel-title {
            color: #eaf0f6;
            font-size: 0.86rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            margin-bottom: 0.8rem;
        }
        .brief-box {
            border-left: 3px solid #7fd7c7;
            background: rgba(11, 31, 43, 0.82);
            padding: 1rem;
            border-radius: 10px;
            color: #dce5ee;
            line-height: 1.6;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <section class="hero">
            <div class="hero-kicker">Cyber Decision Intelligence Platform</div>
            <h1 class="hero-title">SignalMind</h1>
            <div class="hero-copy">
                Incident risk scoring, sequence anomaly detection, retrieval-backed reasoning,
                and analyst-ready decision support in a single operational console.
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def request_ingest(dataset_name: str, uploaded_file) -> tuple[bool, Union[dict[str, Any], str]]:
    try:
        response = requests.post(
            f"{API_URL}/datasets/ingest",
            data={"dataset_name": dataset_name},
            files={"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")},
            timeout=120,
        )
        response.raise_for_status()
        return True, response.json()
    except requests.RequestException as exc:
        return False, str(exc)


def render_metric_strip(df: pd.DataFrame) -> None:
    avg_risk = float(df["risk_score"].mean())
    avg_anomaly = float(df["anomaly_score"].mean())
    high_risk_count = int((df["risk_score"] >= 0.7).sum())
    critical_count = int((df["severity_label"] == "critical").sum())

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Incidents", f"{len(df)}")
    m2.metric("Avg Risk", f"{avg_risk:.2f}")
    m3.metric("High Risk", f"{high_risk_count}")
    m4.metric("Critical", f"{critical_count}", delta=f"Avg anomaly {avg_anomaly:.0f}")


def render_incident_analytics(df: pd.DataFrame) -> None:
    analytics_left, analytics_right = st.columns((1.3, 1))

    with analytics_left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Risk Timeline</div>', unsafe_allow_html=True)
        timeline = (
            df.sort_values("event_ts")[["event_ts", "risk_score", "anomaly_score"]]
            .assign(event_ts=lambda frame: pd.to_datetime(frame["event_ts"]))
            .set_index("event_ts")
        )
        st.line_chart(timeline, height=280)
        st.markdown("</div>", unsafe_allow_html=True)

    with analytics_right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Severity and Attack Mix</div>', unsafe_allow_html=True)
        severity_counts = df["severity_label"].value_counts().rename_axis("severity").reset_index(name="count")
        st.bar_chart(severity_counts.set_index("severity"), height=130)
        attack_counts = df["attack_family"].value_counts().head(6).rename_axis("attack_family").reset_index(name="count")
        st.bar_chart(attack_counts.set_index("attack_family"), height=130)
        st.markdown("</div>", unsafe_allow_html=True)


def render_action_rail() -> None:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Control Plane</div>', unsafe_allow_html=True)
    a1, a2, a3 = st.columns(3)

    if a1.button("Bootstrap Demo Data", use_container_width=True):
        ok, payload = call_api("POST", "/bootstrap/demo-data")
        if ok:
            st.success("Demo data bootstrapped")
            st.json(payload)
        else:
            st.error(payload)

    if a2.button("Train Models", use_container_width=True):
        ok, payload = call_api("POST", "/models/train", timeout=120)
        if ok:
            st.success("Models retrained")
            st.json(payload)
        else:
            st.error(payload)

    if a3.button("Evaluate Models", use_container_width=True):
        ok, payload = call_api("POST", "/models/evaluate", timeout=120)
        if ok:
            st.success("Evaluation completed")
            st.json(payload)
        else:
            st.error(payload)

    st.markdown("</div>", unsafe_allow_html=True)


def render_ingestion_panel() -> None:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Dataset Ingestion</div>', unsafe_allow_html=True)
    dataset_name = st.text_input("Dataset Name", value="unsw-nb15-sample")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    st.caption("Known-good test file: data/raw/sample_unsw_nb15_like.csv")
    if st.button("Ingest CSV Dataset", disabled=uploaded_file is None, use_container_width=True):
        ok, payload = request_ingest(dataset_name, uploaded_file)
        if ok:
            st.success("Dataset ingested")
            st.json(payload)
        else:
            st.error(payload)
    st.markdown("</div>", unsafe_allow_html=True)


def render_evaluation_panel(evaluations_payload: list[dict[str, Any]]) -> None:
    if not evaluations_payload:
        return

    latest = evaluations_payload[0]
    left, right = st.columns((0.9, 1.4))

    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Latest Evaluation</div>', unsafe_allow_html=True)
        st.metric("ROC AUC", f'{latest["classical_auc"]:.3f}')
        st.metric("Precision", f'{latest["classical_precision"]:.3f}')
        st.metric("Recall", f'{latest["classical_recall"]:.3f}')
        st.metric("F1", f'{latest["classical_f1"]:.3f}')
        st.caption(f'Artifacts: {latest["artifact_path"]}')
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Evaluation History</div>', unsafe_allow_html=True)
        eval_df = pd.DataFrame(evaluations_payload)[
            [
                "created_at",
                "dataset_name",
                "sample_count",
                "classical_auc",
                "classical_precision",
                "classical_recall",
                "classical_f1",
            ]
        ]
        st.dataframe(eval_df, use_container_width=True, height=220)
        st.markdown("</div>", unsafe_allow_html=True)


def render_investigation_panel(df: pd.DataFrame) -> None:
    left, right = st.columns((1.25, 1))
    selected_id = right.selectbox("Incident ID", df["id"].tolist())
    selected_incident = df[df["id"] == selected_id].iloc[0].to_dict()

    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Incident Feed</div>', unsafe_allow_html=True)
        incident_view = df[
            [
                "id",
                "event_ts",
                "title",
                "severity_label",
                "attack_family",
                "risk_score",
                "anomaly_score",
            ]
        ].copy()
        st.dataframe(incident_view, use_container_width=True, height=310)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Incident Investigation</div>', unsafe_allow_html=True)
        st.write(f'**Title:** {selected_incident["title"]}')
        st.write(f'**Severity:** {selected_incident["severity_label"]}')
        st.write(f'**Attack family:** {selected_incident["attack_family"]}')
        st.write(f'**Risk score:** {selected_incident["risk_score"]:.3f}')
        st.write(f'**Anomaly score:** {selected_incident["anomaly_score"]:.1f}')
        st.write(f'**Risk drivers:** {selected_incident.get("risk_explanation", "not available")}')

        if st.button("Generate Analyst Brief", use_container_width=True):
            ok, payload = call_api("POST", f"/incidents/{selected_id}/brief")
            if ok:
                st.session_state["latest_brief"] = payload
            else:
                st.error(payload)

        latest_brief = st.session_state.get("latest_brief")
        if latest_brief and latest_brief.get("incident_id") == selected_id:
            st.markdown('<div class="brief-box">', unsafe_allow_html=True)
            st.write(latest_brief["decision"]["summary"])
            st.caption(latest_brief["decision"]["severity_rationale"])
            st.write("**Recommended actions**")
            for action in latest_brief["decision"]["recommended_actions"]:
                st.write(f'- {action["priority"]}: {action["title"]} - {action["rationale"]}')
            st.write("**Evidence**")
            for item in latest_brief["decision"]["evidence"]:
                st.write(f'- {item["kind"]}: {item["detail"]}')
            st.write("**Investigation questions**")
            for question in latest_brief["decision"]["investigation_questions"]:
                st.write(f"- {question}")
            st.caption("Runbooks: " + ", ".join(latest_brief.get("recommended_runbooks", [])))
            st.caption("Similar incidents: " + ", ".join(latest_brief.get("similar_incidents", [])))
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


render_shell()

health_ok, health_payload = call_api("GET", "/health", timeout=5)
if health_ok:
    st.success(f"Backend connected: {API_URL}")
else:
    st.error(f"Backend unavailable: {health_payload}")
    st.info("Start FastAPI with: uvicorn app.main:app --reload")

render_action_rail()

ingest_col, status_col = st.columns((0.9, 1.1))
with ingest_col:
    render_ingestion_panel()

with status_col:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">System Status</div>', unsafe_allow_html=True)
    st.write("SignalMind combines supervised risk scoring, sequential anomaly detection, retrieval, and structured decision intelligence for cyber incident triage.")
    st.write("Recommended analyst flow: bootstrap or ingest telemetry, retrain models, evaluate quality, then investigate priority incidents.")
    st.caption("Demonstrates production AI system design across ML, deep learning, retrieval, reasoning, and API delivery.")
    st.markdown("</div>", unsafe_allow_html=True)

incidents_ok, incidents_payload = call_api("GET", "/incidents")
if incidents_ok:
    incidents_df = pd.DataFrame(incidents_payload)
    if not incidents_df.empty:
        render_metric_strip(incidents_df)
        render_incident_analytics(incidents_df)
        render_investigation_panel(incidents_df)
    else:
        st.info("No incidents found. Bootstrap demo data or ingest a dataset first.")
else:
    st.warning("Incident feed unavailable until the backend is running.")

evaluations_ok, evaluations_payload = call_api("GET", "/models/evaluations")
if evaluations_ok and evaluations_payload:
    render_evaluation_panel(evaluations_payload)
