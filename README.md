# SignalMind

SignalMind is an AI-powered cybersecurity incident intelligence platform that combines supervised risk scoring, sequential anomaly detection, retrieval, explainability, and structured decision generation.

It is built to demonstrate production-grade AI engineering across backend systems, model training, evaluation, and analyst-facing product design.

## Why This Project Matters

Most portfolio AI projects stop at one of these layers:

- a model notebook
- a chatbot wrapper
- a thin RAG demo
- a dashboard with no real ML

SignalMind is intentionally broader and more realistic. It simulates the shape of an operational cyber decision-support system:

- ingest telemetry or public cyber datasets
- detect high-risk and abnormal events
- retrieve similar incidents and remediation context
- generate structured analyst decisions
- expose the workflow through an API and an operator console

This project complements `EvalForge`:

- `EvalForge` shows LLM evaluation, PromptOps, telemetry, and async workflows
- `SignalMind` shows ML + deep learning + retrieval + explainability + decision intelligence + productized deployment shape

## What SignalMind Demonstrates

- Production-oriented FastAPI backend design
- SQLAlchemy-based persistence with SQLite and Postgres-ready structure
- Classical ML risk modeling with `HistGradientBoostingClassifier`
- Sequential anomaly detection with a PyTorch LSTM autoencoder
- Public cyber dataset ingestion and schema normalization
- Persisted evaluation runs with risk and anomaly metrics
- Retrieval of similar incidents and runbooks
- Structured decision generation with evidence, rationale, actions, and investigation questions
- Explainability through top risk-driver summaries
- Analyst-facing Streamlit console with KPIs, charts, evaluation history, and incident drill-down

## Screenshots

### Analyst Console Overview
![SignalMind Dashboard Overview](docs/signalmind-dashboard-overview.png)

### Incident Investigation
![SignalMind Incident Investigation](docs/signalmind-incident-investigation.png)

### Structured Analyst Brief
![SignalMind Analyst Brief](docs/signalmind-analyst-brief.png)

### Evaluation Console
![SignalMind Evaluation Console](docs/signalmind-evaluation-console.png)

### Dataset Ingestion
![SignalMind Dataset Ingestion](docs/signalmind-dataset-ingestion.png)

## Architecture Overview

### Backend

- `FastAPI` API layer for ingestion, training, evaluation, incident listing, and decision generation
- `SQLAlchemy` ORM with SQLite for local runs and a design that can move to Postgres
- Service layer for data generation, ingestion, retrieval, model orchestration, and decision logic

### AI Stack

- Classical ML:
  - `HistGradientBoostingClassifier` for incident risk scoring
- Deep Learning:
  - `PyTorch LSTM autoencoder` for temporal anomaly scoring
- Decision Intelligence:
  - structured prompt + provider abstraction + fallback decision synthesis
- Retrieval:
  - similar incident lookup
  - runbook retrieval for remediation guidance

### Data Strategy

SignalMind uses a hybrid data strategy:

1. Synthetic SOC-style incidents for reproducible local demos and fast end-to-end testing
2. Public cyber CSV ingestion for realism and benchmark credibility

Current public-data path is designed around normalized imports from datasets such as:

- `UNSW-NB15`
- `CIC-IDS2017`

The repo includes a small bundled sample file for local validation:

- `data/raw/sample_unsw_nb15_like.csv`

## Key Features

- End-to-end cyber incident workflow from ingestion to analyst brief
- Risk and anomaly scoring on the same incident stream
- Stored evaluation metrics for repeatable experiments
- Explainable risk summaries at the incident level
- Structured decision objects instead of a plain narrative blob
- SOC-style dashboard for demo and portfolio presentation

## Repository Structure

```text
SignalMind/
├── app/
│   ├── api/            # FastAPI routes
│   ├── core/           # config and settings
│   ├── db/             # ORM models and session setup
│   ├── llm/            # decision-generation abstractions
│   ├── ml/             # classical and sequence models
│   ├── retrieval/      # similar-incident retrieval
│   ├── schemas/        # Pydantic contracts
│   └── services/       # orchestration and business logic
├── dashboard/          # Streamlit analyst console
├── data/               # raw, processed, and model artifacts
├── docs/               # architecture notes and screenshots
├── scripts/            # local utility scripts
└── tests/              # test suite
```

## Quick Start

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -e '.[dev]'
```

### 3. Start the backend

```bash
uvicorn app.main:app --reload
```

### 4. Start the dashboard

In a second terminal:

```bash
source .venv/bin/activate
streamlit run dashboard/app.py
```

## Demo Workflow

### Option A: Synthetic end-to-end demo

1. Click `Bootstrap Demo Data`
2. Click `Train Models`
3. Click `Evaluate Models`
4. Select an incident
5. Click `Generate Analyst Brief`

### Option B: Public-style CSV demo

1. Start the backend and dashboard
2. In the dashboard, use the bundled sample:
   - `data/raw/sample_unsw_nb15_like.csv`
3. Upload it in `Dataset Ingestion`
4. Click `Ingest CSV Dataset`
5. Click `Train Models`
6. Click `Evaluate Models`
7. Investigate an imported incident and generate the brief

## API Surface

### Health

- `GET /api/v1/health`

### Data

- `POST /api/v1/bootstrap/demo-data`
- `POST /api/v1/datasets/ingest`
- `GET /api/v1/incidents`
- `GET /api/v1/incidents/{incident_id}`

### Models

- `POST /api/v1/models/train`
- `POST /api/v1/models/evaluate`
- `GET /api/v1/models/evaluations`

### Decision Support

- `POST /api/v1/incidents/{incident_id}/brief`

## Example Outcome

For a single incident, SignalMind can produce:

- predicted risk score
- sequence anomaly score
- top risk drivers
- similar historical incidents
- recommended runbooks
- structured analyst decision with:
  - summary
  - severity rationale
  - evidence
  - recommended actions
  - investigation questions

## Current Status

Completed:

- Backend API
- Synthetic telemetry bootstrap
- Public-style CSV ingestion
- Classical ML + sequence anomaly modeling
- Evaluation persistence
- Incident-level explainability
- Structured decision-intelligence layer
- Analyst console UI

In progress:

- Real benchmark packaging
- Docker and CI
- richer tests
- architecture visuals
- final release polish

## Why This Is Interview-Defensible

This project is easy to discuss in interviews because it exposes real engineering tradeoffs:

- why use a classical model and a sequence model together
- how to separate scoring, retrieval, and generation
- how to evaluate classification and anomaly layers differently
- how to normalize public cyber datasets into a product schema
- how to move from a local SQLite demo to a production service design

## Roadmap

- Add stronger benchmark ingestion adapters
- Add experiment tracking and richer reporting
- Add Docker and CI
- Add architecture diagram
- Add more realistic LLM provider integrations
- Add deeper tests for API and workflow coverage

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- SQLite
- Pandas
- scikit-learn
- PyTorch
- Streamlit

## Notes

- This repo is intentionally runnable locally without external LLM credentials
- The current decision layer uses a provider abstraction with a strong fallback path
- Synthetic metrics can look overly strong; public-data evaluation is the more realistic demo path
