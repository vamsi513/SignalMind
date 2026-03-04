from pydantic import BaseModel


class IngestionResponse(BaseModel):
    dataset_name: str
    records_ingested: int
    source_path: str
