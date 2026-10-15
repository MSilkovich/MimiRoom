from ..models.pet_type import PetType
from .sqlalchemy_repository import SqlAlchemyRepository


class PetTypeRepository(SqlAlchemyRepository[PetType]):
    def __init__(self, session):
        super().__init__(PetType, session)
