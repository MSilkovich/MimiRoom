from ..models.breed import Breed
from ..schemas import BreedCreate, BreedUpdate
from .base_service import BaseService


class BreedService(BaseService[Breed, BreedCreate, BreedUpdate]):
    model = Breed
