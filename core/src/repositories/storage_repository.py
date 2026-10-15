from ..models.storage import Storage
from .sqlalchemy_repository import SqlAlchemyRepository


class StorageRepository(SqlAlchemyRepository[Storage]):
    def __init__(self, session):
        super().__init__(Storage, session)
