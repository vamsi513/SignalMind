# SignalMind Architecture

## System shape

SignalMind is structured as an end-to-end cyber decision intelligence platform rather than a single-model demo:

- `app/api`: external contract for ingestion, training, listing, and briefing workflows
- `app/db`: persistence layer with SQLAlchemy models and session management
- `app/services`: orchestration layer for data generation, training, retrieval, and incident briefing
- `app/ml`: classical and sequence models
- `app/retrieval`: similar-incident and runbook retrieval
- `app/llm`: structured narrative generation behind a provider abstraction
- `dashboard`: operator-facing demo UI

## AI stack

The initial version intentionally demonstrates three separate AI patterns:

1. Classical ML
   - `HistGradientBoostingClassifier` predicts incident risk from engineered security features.
2. Sequential deep learning
   - An `LSTM` autoencoder scores temporal behavior drift and anomaly magnitude.
3. LLM decision layer
   - A provider abstraction plus structured fallback synthesis turns model outputs and retrieved context into analyst-ready decisions.

## Data strategy

The project starts with realistic synthetic SOC telemetry because it gives:

- deterministic local demos
- traceable feature semantics
- reproducible model training
- no licensing friction for portfolio publishing

The next step is broader public dataset ingestion via adapters instead of rewriting the system:

- `UNSW-NB15` for labeled intrusion/risk classification
- `CIC-IDS2017` for attack-pattern benchmarking
- optional enterprise log datasets for temporal anomaly benchmarking

## Why this is strong for interviews

This architecture is credible because it separates:

- online API concerns from model code
- persistence from orchestration
- scoring from retrieval
- generation from evidence selection

That makes it easy to discuss feature engineering, model tradeoffs, explainability, evaluation, batch retraining, and productionization without the repo collapsing into a notebook or a framework wrapper.
