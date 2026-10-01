from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Catalogo de Servicios API"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "catalogo_servicios"
    database_user: str = "catalogo"
    database_password: str = "catalogo_dev"
    app_encryption_key: str = ""
    session_expire_minutes: int = 480
    frontend_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url(self) -> str:
        user = quote_plus(self.database_user)
        password = quote_plus(self.database_password)
        return f"postgresql://{user}:{password}@{self.database_host}:{self.database_port}/{self.database_name}"


settings = Settings()
