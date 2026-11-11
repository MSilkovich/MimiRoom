from ..models.pet_type import PetType
from ..schemas import PetTypeCreate, PetTypeUpdate
from .base import BaseService


class PetTypeService(BaseService[PetType, PetTypeCreate, PetTypeUpdate]):
    model = PetType
