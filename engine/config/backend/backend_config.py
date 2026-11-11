from pydantic import Field
from pydantic_settings import BaseSettings


class BackendSettings(BaseSettings):
    BACKEND_URL: str
    BACKEND_SERVICE_TOKEN: str
    BACKEND_TIMEOUT_SEC: int = Field(default=15)


settings_backend = BackendSettings()
