from src.excpetions.auth import PermissionDeniedError
from src.excpetions.crud import ConflictError, ValidationError
from src.models.service import Service
from src.models.user import User
from src.permissions.enums.roles import Role
from src.permissions.enums.scope import Scope
from src.permissions.permission_rule import PermissionRule
from src.schemas import MasterCreate, MasterUpdate
from .auth_service import AuthService
from .base import BaseService


class MasterService(BaseService[User, MasterCreate, MasterUpdate]):
    """Мастер — это ``User`` с ролью ``groomer``."""

    model = User

    @staticmethod
    async def _ensure_services_exist(service_repo, service_ids: list[int]) -> None:
        unique_ids = set(service_ids)
        found = await service_repo.get_many_by_ids(unique_ids)
        missing = unique_ids - {service.service_id for service in found}
        if missing:
            raise ValidationError(f"Услуги не найдены: {sorted(missing)}")

    async def get(self, pk: int, rule=None) -> User | None:  # type: ignore[override]
        async with self.uow_factory() as uow:
            repo = uow.repository(User)
            user = await repo.get_single(user_id=pk)
            if user is not None and user.role == Role.GROOMER:
                return user
            return None

    async def get_multi(  # type: ignore[override]
        self,
        order: str | None = None,
        limit: int = 100,
        offset: int = 0,
        rule=None,
    ) -> list[User]:
        async with self.uow_factory() as uow:
            repo = uow.repository(User)
            return await repo.get_masters(limit=limit, offset=offset)

    async def create(self, data: MasterCreate) -> User:
        async with self.uow_factory() as uow:
            user_repo = uow.repository(User)
            service_repo = uow.repository(Service)

            if await user_repo.get_single(login=data.login):
                raise ConflictError("Пользователь с таким логином уже есть")

            payload = data.model_dump(exclude={"service_ids"})
            payload["role"] = Role.GROOMER
            payload["password"] = AuthService.hash_password(data.password)

            user = await user_repo.create(payload)
            user_id = user.user_id

            if data.service_ids:
                await self._ensure_services_exist(
                    service_repo, data.service_ids
                )
                await user_repo.replace_master_services(
                    user_id, data.service_ids
                )

            await uow.commit()
            uow.session.expire_all()
            reloaded = await user_repo.get_single(user_id=user_id)
            return reloaded or user

    async def update(
        self,
        pk: int,
        data: MasterUpdate,
        rule: PermissionRule | None = None,
    ) -> User | None:  # type: ignore[override]
        if (
            rule is not None
            and rule.scope == Scope.OWN
            and data.service_ids is not None
        ):
            raise PermissionDeniedError(
                "Набор услуг мастера меняет администратор/менеджер"
            )

        async with self.uow_factory() as uow:
            user_repo = uow.repository(User)
            service_repo = uow.repository(Service)

            user = await user_repo.get_single(rule=rule, user_id=pk)
            if user is None:
                return None

            payload = data.model_dump(
                exclude_unset=True, exclude={"service_ids"}
            )
            if payload.get("password"):
                payload["password"] = AuthService.hash_password(
                    payload["password"]
                )
            if payload:
                await user_repo.update(payload, rule=rule, user_id=pk)

            if data.service_ids is not None:
                await self._ensure_services_exist(
                    service_repo, data.service_ids
                )
                await user_repo.replace_master_services(
                    pk, data.service_ids
                )

            await uow.commit()
            uow.session.expire_all()
            return await user_repo.get_single(rule=rule, user_id=pk)
