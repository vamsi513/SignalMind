from app.services.incident_service import train_models


if __name__ == "__main__":
    print(train_models().model_dump())

