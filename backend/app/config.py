from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://orcaavml:orcaavml@localhost:5432/orcaavml"
    secret_key: str = "change-me-in-production-use-openssl-rand-hex-32"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    anthropic_api_key: str = ""
    pacotes_dir: str = "/tmp/pacotes"
    diario_dir: str = "/tmp/diario"
    contratos_dir: str = "/tmp/contratos"


settings = Settings()
