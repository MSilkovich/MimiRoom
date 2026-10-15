from ..models.pet import Pet
from .sqlalchemy_repository import SqlAlchemyRepository


class PetRepository(SqlAlchemyRepository[Pet]):
    def __init__(self, session):
        super().__init__(Pet, session)
