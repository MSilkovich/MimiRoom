"""Доменные роутеры приложений (категории и сессии).

Экспорт:
- book_router
- breed_router
- measure_unit_router
- pet_router
- pet_type_router
- service_router
- service_consumable_router
- storage_router
"""

from .book import router as book_router
from .breed import router as breed_router
from .measure_unit import router as measure_unit_router
from .pet import router as pet_router
from .pet_type import router as pet_type_router
from .service import router as service_router
from .service_consumable import router as service_consumable_router
from .storage import router as storage_router

