from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    SERVICE_JWT_SECRET: str
    SERVICE_JWT_ALG: str = "HS256"


settings_jwt = Settings()
