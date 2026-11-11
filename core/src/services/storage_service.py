from ..models.storage import Storage
from ..schemas import StorageCreate, StorageUpdate
from .base import BaseService


class StorageService(BaseService[Storage, StorageCreate, StorageUpdate]):
    model = Storage
