from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_settings
from app.db.session import init_db


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Cyber incident risk, anomaly detection, and decision intelligence API.",
    )
    init_db()
    app.include_router(router, prefix="/api/v1")
    return app


app = create_app()

