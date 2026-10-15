from ..models.breed import Breed
from .sqlalchemy_repository import SqlAlchemyRepository


class BreedRepository(SqlAlchemyRepository[Breed]):
    def __init__(self, session):
        super().__init__(Breed, session)
