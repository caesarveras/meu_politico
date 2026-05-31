from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Meu Políticos API"
    app_version: str = "0.1.0"
    default_locale: str = "pt-BR"
    supported_locales: list[str] = ["pt-BR", "es", "en"]
    environment: str = "development"
    database_url: str = "sqlite:///./meuspoliticos.db"
    redis_url: str = "redis://localhost:6379/0"
    camara_api_base_url: str = "https://dadosabertos.camara.leg.br/api/v2"
    sync_daily_enabled: bool = False
    sync_daily_hour: int = 0
    sync_daily_minute: int = 0
    sync_daily_timezone: str = "America/Sao_Paulo"

    model_config = SettingsConfigDict(env_file=(".env.local", ".env"), env_file_encoding="utf-8", extra="ignore")


settings = Settings()
