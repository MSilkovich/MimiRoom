from ..models.pet import Pet
from ..schemas import PetCreate, PetUpdate
from .base_service import BaseService


class PetService(BaseService[Pet, PetCreate, PetUpdate]):
    model = Pet
