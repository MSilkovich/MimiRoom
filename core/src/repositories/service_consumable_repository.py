from ..models.service_consumable import ServiceConsumable
from .sqlalchemy_repository import SqlAlchemyRepository


class ServiceConsumableRepository(SqlAlchemyRepository[ServiceConsumable]):
    def __init__(self, session):
        super().__init__(ServiceConsumable, session)
