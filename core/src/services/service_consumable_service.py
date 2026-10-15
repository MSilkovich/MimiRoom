from ..models.service_consumable import ServiceConsumable
from ..schemas import ServiceConsumableCreate, ServiceConsumableUpdate
from .base_service import BaseService


class ServiceConsumableService(
    BaseService[ServiceConsumable, ServiceConsumableCreate, ServiceConsumableUpdate]
):
    model = ServiceConsumable
