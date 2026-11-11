"""Фабрика LLM-клиентов по настройкам."""

from .base import LLMClient
from config.llm import settings_llm


def create_llm_client() -> LLMClient:
    provider = settings_llm.LLM_PROVIDER.lower()
    if provider == "openai":
        from src.llm.openai_client import OpenaiClient
        return OpenaiClient()
    raise ValueError(f"Unknown LLM provider: {provider}")
