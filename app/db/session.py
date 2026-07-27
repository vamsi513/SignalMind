from collections.abc import Iterator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.base import Base

settings = get_settings()
engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _apply_sqlite_migrations()


def _apply_sqlite_migrations() -> None:
    inspector = inspect(engine)
    if "incidents" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("incidents")}
    with engine.begin() as connection:
        if "risk_explanation" not in columns:
            connection.execute(
                text("ALTER TABLE incidents ADD COLUMN risk_explanation TEXT DEFAULT ''")
            )

    if "model_evaluations" in inspector.get_table_names():
        eval_columns = {column["name"] for column in inspector.get_columns("model_evaluations")}
        with engine.begin() as connection:
            if "isolation_forest_auc" not in eval_columns:
                connection.execute(
                    text("ALTER TABLE model_evaluations ADD COLUMN isolation_forest_auc FLOAT DEFAULT 0.0")
                )
            if "sequence_autoencoder_auc" not in eval_columns:
                connection.execute(
                    text("ALTER TABLE model_evaluations ADD COLUMN sequence_autoencoder_auc FLOAT DEFAULT 0.0")
                )


def get_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
