from ..models.role import Role
from .sqlalchemy_repository import SqlAlchemyRepository


class RoleRepository(SqlAlchemyRepository[Role]):
    def __init__(self, session):
        super().__init__(Role, session)
