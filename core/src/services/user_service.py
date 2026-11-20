from src.context import system_context
from src.excpetions.crud import NotFoundError
from src.repositories.user_repository import UserRepository

from ..models.user import User
from ..schemas import UserCreate, UserUpdate, Summary, UserSummary, PetSummary
from .base import BaseService


class UserService(BaseService[User, UserCreate, UserUpdate]):
    model = User

    async def get_summary_by_id(self, user_id: int) -> Summary | None:
        with system_context():
            async with self.uow_factory() as uow:
                user_repo: UserRepository = uow.repository(User)
                return await user_repo.get_summary_by_id(user_id)
