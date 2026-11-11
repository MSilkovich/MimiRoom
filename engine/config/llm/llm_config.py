from pydantic import Field
from pydantic_settings import BaseSettings


class LLMSettings(BaseSettings):
    LLM_PROVIDER: str = Field(default="qwen")
    LLM_MODEL: str = Field(default="qwen3.7-flash")
    LLM_API_KEY: str | None = Field(default=None)
    LLM_BASE_URL: str | None = Field(
        default="https://foundation-models.api.cloud.ru/v1")
    LLM_TIMEOUT_SEC: int = Field(default=60)
    LLM_MAX_RETRIES: int = Field(default=2)
    LLM_MAX_TOKENS: int = Field(default=1500)
    LLM_DEBUG_RAW: bool = Field(default=False)


settings_llm = LLMSettings()
