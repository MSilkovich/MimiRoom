from ..models.role import Role
from ..schemas import RoleCreate, RoleUpdate
from .base_service import BaseService


class RoleService(BaseService[Role, RoleCreate, RoleUpdate]):
    model = Role
