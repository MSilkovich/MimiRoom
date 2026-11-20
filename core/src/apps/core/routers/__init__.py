"""
Доменные роутеры приложений (категории и сессии).
"""

from .book import router as book_router
from .breed import router as breed_router
from .measure_unit import router as measure_unit_router
from .pet import router as pet_router
from .pet_type import router as pet_type_router
from .service import router as service_router, router_service as service_router_service
from .storage import router as storage_router
from .staff import router as staff_router
from .users import router as user_router, router_service as user_router_service
from .auth import router as auth_router
