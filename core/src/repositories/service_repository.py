from ..models.service import Service
from .sqlalchemy_repository import SqlAlchemyRepository


class ServiceRepository(SqlAlchemyRepository[Service]):
    def __init__(self, session):
        super().__init__(Service, session)
