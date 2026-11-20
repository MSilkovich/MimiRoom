from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LLM_PROVIDER: str
    LLM_MODEL: str
    LLM_API_KEY: str = Field(default="none")
    LLM_BASE_URL: str
    LLM_TIMEOUT_SEC: int = Field(default=60)
    LLM_MAX_RETRIES: int = Field(default=2)
    LLM_MAX_TOKENS: int = Field(default=1500)
    LLM_DEBUG_RAW: bool = Field(default=False)


settings_llm = Settings()
