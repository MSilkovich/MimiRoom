from ..models.service_consumable import ServiceConsumable
from ..schemas import ServiceConsumableCreate, ServiceConsumableUpdate
from .base import BaseService


class ServiceConsumableService(
    BaseService[ServiceConsumable,
                ServiceConsumableCreate, ServiceConsumableUpdate]
):
    model = ServiceConsumable
