from ..models.user import User
from ..schemas import UserCreate, UserUpdate
from .base import BaseService


class UserService(BaseService[User, UserCreate, UserUpdate]):
    model = User
