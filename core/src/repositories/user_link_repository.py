from ..models.user_link import UserLink
from .sqlalchemy_repository import SqlAlchemyRepository


class UserLinkRepository(SqlAlchemyRepository[UserLink]):
    def __init__(self, session):
        super().__init__(UserLink, session)
