"""Handlers инструментов LLM.

Каждая функция — handler для одного инструмента из registry.py.
Handlers не делают HTTP-запросы напрямую — они вызывают репозитории.
"""

from . import handlers

__all__ = [
    "handlers",
]
