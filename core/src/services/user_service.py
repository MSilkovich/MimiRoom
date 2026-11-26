from src.context import system_context
from src.excpetions.crud import NotFoundError, ValidationError
from src.permissions.enums.roles import Role
from src.permissions.permission_rule import PermissionRule
from src.permissions.role_permissions import ROLE_MASK
from src.repositories.user_repository import UserRepository

from ..models.user import User
from ..schemas import UserCreate, UserUpdate, Summary, UserSummary, PetSummary
from .auth_service import AuthService
from .base import BaseService


class UserService(BaseService[User, UserCreate, UserUpdate]):
    model = User

    async def create(
        self, data: UserCreate, rule: PermissionRule | None = None
    ) -> User:
        """Создать пользователя, сохранив пароль только в виде хэша."""
        payload = data.model_dump()
        payload["password"] = AuthService.hash_password(data.password)

        async with self.uow_factory() as uow:
            repo = uow.repository(self.model)
            instance = await repo.create(payload, rule)
            await uow.commit()
            return instance

    async def update(
        self,
        pk: int,
        data: UserUpdate,
        rule: PermissionRule | None = None,
    ) -> User | None:
        """Обновить пользователя, хэшируя новый пароль.

        Если пароль не передан (или пустой) — поле не трогаем, чтобы не
        затереть существующий хэш и не записать ``NULL`` в NOT NULL-колонку.
        """
        updates = data.model_dump(exclude_unset=True)
        if updates.get("password"):
            updates["password"] = AuthService.hash_password(updates["password"])
        else:
            updates.pop("password", None)

        async with self.uow_factory() as uow:
            repo = uow.repository(self.model)
            if not updates:
                return await repo.get_single(rule=rule, **{repo.pk_name: pk})
            instance = await repo.update(updates, rule, **{repo.pk_name: pk})
            await uow.commit()
            return instance

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
