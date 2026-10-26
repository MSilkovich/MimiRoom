from ..models.user_link import UserLink
from ..schemas import UserLinkCreate, UserLinkRead, UserLinkUpdate
from .base_service import BaseService


class UserLinkService(BaseService[UserLink, UserLinkCreate, UserLinkUpdate]):
    model = UserLink
