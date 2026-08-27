from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "my-case-api"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://mycase:mycase_dev_password@localhost:5432/mycase_dev"
    cors_origins: str = "http://localhost:3000,http://localhost:3001,http://localhost:3002"
    jwt_secret: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
