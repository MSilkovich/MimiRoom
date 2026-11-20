from functools import cached_property
from jose import jwt

from pydantic import Field
from pydantic_settings import BaseSettings


class BackendSettings(BaseSettings):
    BACKEND_BASE_URL: str
    BACKEND_TIMEOUT_SEC: int = Field(default=15)

    BACKEND_SECRET: str
    BACKEND_SERVICE_ALG: str = "HS256"

    @cached_property
    def token(self) -> str:
        return jwt.encode(
            {
                "type": "service"
                # сюда класть данные, если такая необходимость появится
            },
            self.BACKEND_SECRET,
            algorithm=self.BACKEND_SERVICE_ALG,
        )


settings_backend = BackendSettings()
