from typing import Type

from .base_uow import UnitOfWork
from ..models import (
    MeasureUnit,
    PetType,
    Role,
    Breed,
    Service,
    Storage,
    User,
    Pet,
    ServiceConsumable,
    Book,
)
from .measure_unit_repository import MeasureUnitRepository
from .pet_type_repository import PetTypeRepository
from .role_repository import RoleRepository
from .breed_repository import BreedRepository
from .service_repository import ServiceRepository
from .storage_repository import StorageRepository
from .user_repository import UserRepository
from .pet_repository import PetRepository
from .service_consumable_repository import ServiceConsumableRepository
from .book_repository import BookRepository


class SqlAlchemyUnitOfWork(UnitOfWork):
    """Объединяет репозитории на одной сессии.

    Открывает сессию в __aenter__ и закрывает в __aexit__, гарантируя,
    что все репозитории используют один и тот же DbContext. Коммит и
    откат транзакции выполняются здесь.
    """

    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.session = None

    async def __aenter__(self):
        self.session = self.session_factory()

        self.measure_units = MeasureUnitRepository(self.session)
        self.pet_types = PetTypeRepository(self.session)
        self.roles = RoleRepository(self.session)
        self.breeds = BreedRepository(self.session)
        self.services = ServiceRepository(self.session)
        self.storages = StorageRepository(self.session)
        self.users = UserRepository(self.session)
        self.pets = PetRepository(self.session)
        self.service_consumables = ServiceConsumableRepository(self.session)
        self.books = BookRepository(self.session)

        self._repositories = {
            MeasureUnit: self.measure_units,
            PetType: self.pet_types,
            Role: self.roles,
            Breed: self.breeds,
            Service: self.services,
            Storage: self.storages,
            User: self.users,
            Pet: self.pets,
            ServiceConsumable: self.service_consumables,
            Book: self.books,
        }
        return self

    def repository(self, model: Type):
        """Возвращает репозиторий по классу модели."""
        try:
            return self._repositories[model]
        except KeyError:
            raise LookupError(f"Нет репозитория для модели {model.__name__}")

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type is not None:
            await self.session.rollback()
        await self.session.close()
        self.session = None

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()

