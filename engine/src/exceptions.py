class LLMError(Exception):
    """Базовая ошибка LLM-слоя."""


class BackendError(Exception):
    """Ошибка обращения к backend API (сеть, 4xx/5xx, некорректный ответ)."""


class BackendNotFoundError(BackendError):
    """Backend вернул 404."""
