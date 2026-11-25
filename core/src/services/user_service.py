from src.context import system_context
from src.excpetions.crud import NotFoundError, ValidationError
from src.permissions.enums.roles import Role
from src.permissions.role_permissions import ROLE_MASK
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

    async def update_role(self, user_id: int, role: Role | None) -> User | None:
        """Назначить роль и синхронно обновить её маску прав."""
        if role is None:
            raise ValidationError("Роль обязательна")
        async with self.uow_factory() as uow:
            repo = uow.repository(User)
            user = await repo.get_single(user_id=user_id)
            if user is None:
                raise NotFoundError("Пользователь не найден")
            updated = await repo.update(
                {"role": role, "permission_mask": ROLE_MASK[role]},
                user_id=user_id,
            )
            await uow.commit()
            return updated
