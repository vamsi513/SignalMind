from app.db.models import Incident


def describe_dataset_scope(incidents: list[Incident]) -> str:
    imported_datasets = sorted({incident.asset_id for incident in incidents if incident.source_ip == "dataset-import"})
    synthetic_present = any(incident.source_ip != "dataset-import" for incident in incidents)

    if imported_datasets and synthetic_present:
        return "mixed:" + ",".join(["synthetic-demo"] + imported_datasets)
    if imported_datasets:
        return ",".join(imported_datasets)
    return "synthetic-demo"
