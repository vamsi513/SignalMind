from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.schemas.evaluation import ModelEvaluationRead
from app.schemas.ingestion import IngestionResponse
from app.schemas.incident import (
    BootstrapResponse,
    IncidentBriefResponse,
    IncidentRead,
    ModelTrainingResponse,
)
from app.services.data_ingestion import ingest_csv_dataset
from app.services.evaluation_service import evaluate_models, latest_evaluations
from app.services.bootstrap import bootstrap_demo_data
from app.services.incident_service import (
    generate_incident_brief,
    get_incident,
    list_incidents,
    train_models,
)

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/bootstrap/demo-data", response_model=BootstrapResponse)
def bootstrap() -> BootstrapResponse:
    return bootstrap_demo_data()


@router.get("/incidents", response_model=list[IncidentRead])
def incidents(limit: int = 50) -> list[IncidentRead]:
    return list_incidents(limit=limit)


@router.get("/incidents/{incident_id}", response_model=IncidentRead)
def incident_detail(incident_id: int) -> IncidentRead:
    incident = get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("/models/train", response_model=ModelTrainingResponse)
def train() -> ModelTrainingResponse:
    try:
        return train_models()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/datasets/ingest", response_model=IngestionResponse)
async def ingest_dataset(
    dataset_name: str = Form(...),
    file: UploadFile = File(...),
) -> IngestionResponse:
    safe_suffix = Path(file.filename or "dataset.csv").suffix or ".csv"
    safe_name = "".join(ch for ch in dataset_name.lower() if ch.isalnum() or ch in {"-", "_"}).strip("-_")
    safe_name = safe_name or "dataset"
    target_path = Path("data/raw") / f"{safe_name}-{uuid4().hex[:8]}{safe_suffix}"
    content = await file.read()
    target_path.write_bytes(content)
    try:
        count = ingest_csv_dataset(target_path, dataset_name=dataset_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return IngestionResponse(
        dataset_name=dataset_name,
        records_ingested=count,
        source_path=str(target_path),
    )


@router.post("/models/evaluate", response_model=ModelEvaluationRead)
def evaluate() -> ModelEvaluationRead:
    try:
        return evaluate_models()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/models/evaluations", response_model=list[ModelEvaluationRead])
def evaluations(limit: int = 10) -> list[ModelEvaluationRead]:
    return latest_evaluations(limit=limit)


@router.post("/incidents/{incident_id}/brief", response_model=IncidentBriefResponse)
def brief(incident_id: int) -> IncidentBriefResponse:
    incident = get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    try:
        return generate_incident_brief(incident_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
