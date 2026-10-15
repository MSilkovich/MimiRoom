from ..models.user import User
from .sqlalchemy_repository import SqlAlchemyRepository


class UserRepository(SqlAlchemyRepository[User]):
    def __init__(self, session):
        super().__init__(User, session)
