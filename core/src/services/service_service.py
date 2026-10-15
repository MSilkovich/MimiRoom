from ..models.service import Service
from ..schemas import ServiceCreate, ServiceUpdate
from .base_service import BaseService


class ServiceService(BaseService[Service, ServiceCreate, ServiceUpdate]):
    model = Service
