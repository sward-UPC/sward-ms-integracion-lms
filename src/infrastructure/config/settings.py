from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    database_url: str = (
        "postgresql+asyncpg://sward:sward@localhost:5432/integracion_lms_db"
    )
    moodle_base_url: str = "https://moodle.example.com"
    moodle_token: str = "mock-token"
    moodle_mock: bool = True
    aws_region: str = "us-east-1"
    eventbridge_bus_name: str = "sward-event-bus"
    environment: str = "development"
    service_name: str = "sward-ms-integracion-lms"


settings = Settings()
