from ..models.breed import Breed
from ..schemas import BreedCreate, BreedUpdate
from .base import BaseService


class BreedService(BaseService[Breed, BreedCreate, BreedUpdate]):
    model = Breed
