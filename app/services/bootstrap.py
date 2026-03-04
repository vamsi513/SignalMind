from app.db.models import Incident, Runbook
from app.db.session import SessionLocal
from app.schemas.incident import BootstrapResponse
from app.services.synthetic_data import generate_incidents, generate_runbooks


def bootstrap_demo_data(incident_count: int = 240) -> BootstrapResponse:
    incidents = generate_incidents(incident_count)
    runbooks = generate_runbooks()
    with SessionLocal() as session:
        incidents_created = 0
        runbooks_created = 0
        existing_incidents = session.query(Incident).all()
        existing_class_count = len({incident.label_high_risk for incident in existing_incidents})
        should_refresh_demo_incidents = bool(existing_incidents) and existing_class_count < 2

        if should_refresh_demo_incidents:
            for incident in existing_incidents:
                session.delete(incident)
            session.flush()

        if should_refresh_demo_incidents or not existing_incidents:
            session.add_all(incidents)
            incidents_created = len(incidents)
        if session.query(Runbook).count() == 0:
            session.add_all(runbooks)
            runbooks_created = len(runbooks)
        session.commit()
    return BootstrapResponse(incidents_created=incidents_created, runbooks_created=runbooks_created)
