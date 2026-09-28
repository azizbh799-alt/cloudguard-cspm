from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://cloudguard:cloudguard@localhost:5432/cloudguard"
    jwt_secret: str = "development-only-change-me"
    environment: str = "development"
    cors_origins: str = "http://localhost:3000"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
