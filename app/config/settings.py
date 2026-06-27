from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    app_name: str = Field(default="sql-analizador-consultas", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: Optional[str] = Field(default="logs/sql-analizador-consultas.log", alias="LOG_FILE")
    approval_threshold: int = Field(default=60, alias="APPROVAL_THRESHOLD")
    database_url: str = Field(default="postgresql://user:password@localhost:5432/dbname", alias="DATABASE_URL")

    model_config = {"env_file": ".env", "env_file_encoding": "latin-1", "populate_by_name": True}


settings = Settings()
