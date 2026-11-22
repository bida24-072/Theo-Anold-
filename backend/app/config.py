from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://theo:theo_dev_password@localhost:5432/theo"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    enrollment_shared_secret: str = "university-shared-secret"
    cors_origins: str = "*"
    edge_sync_interval: int = 5

    class Config:
        env_file = ".env"

settings = Settings()
