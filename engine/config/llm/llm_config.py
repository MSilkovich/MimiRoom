from pydantic import Field
from pydantic_settings import BaseSettings


class LLMSettings(BaseSettings):
    LLM_PROVIDER: str
    LLM_MODEL: str
    LLM_API_KEY: str | None = Field(default=None)
    LLM_BASE_URL: str | None = Field(default=None)
    LLM_TIMEOUT_SEC: int = Field(default=60)
    LLM_MAX_RETRIES: int = Field(default=2)


settings_llm = LLMSettings()
