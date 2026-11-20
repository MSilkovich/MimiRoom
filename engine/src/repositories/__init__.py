"""Репозитории для запросов к backend API.

Каждый репозиторий — класс, наследующий BaseRepository,
с методами под конкретный домен (услуги, брони, пользователи...).
"""

from .backend_repository import BackendRepository

# такой вот singleton
backend_repository = BackendRepository()

__all__ = [
    "BackendRepository",
    "backend_repository"
]

