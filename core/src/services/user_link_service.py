"""Сервис привязок внешних провайдеров (UserLink)."""

from sqlalchemy.exc import IntegrityError

from ..excpetions.crud import ConflictError
from ..models.enums.provider import Provider
from ..models.user_link import UserLink
from ..schemas import UserLinkCreate, UserLinkUpdate
from .base import BaseService


class UserLinkService(BaseService[UserLink, UserLinkCreate, UserLinkUpdate]):
    model = UserLink

    async def get_by_external(
        self, provider: Provider, external_id: str
    ) -> UserLink | None:
        """Найти привязку по провайдеру и внешнему id (для сервисного lookup)."""
        async with self.uow_factory() as uow:
            repo = uow.repository(UserLink)
            return await repo.get_single(
                provider=provider, external_id=external_id
            )

    async def list_for_user(
        self, user_id: int, limit: int = 100, offset: int = 0
    ) -> list[UserLink]:
        """Список привязок конкретного пользователя (для ЛК)."""
        async with self.uow_factory() as uow:
            repo = uow.repository(UserLink)
            return await repo.get_multi(
                limit=limit, offset=offset, user_id=user_id
            )

    async def get_for_user(self, link_id: int, user_id: int) -> UserLink | None:
        """Получить привязку пользователя по id."""
        async with self.uow_factory() as uow:
            repo = uow.repository(UserLink)
            return await repo.get_single(id=link_id, user_id=user_id)

    async def link_external(self, data: UserLinkCreate) -> UserLink:
        """Создать или обновить привязку (идемпотентно).

        Правила:
        - если ``provider+external_id`` уже привязан к этому же пользователю —
          возвращаем существующую связку (обновляем options, если переданы);
        - если привязан к другому пользователю — 409;
        - если у пользователя уже есть связка с этим провайдером, но другой
          external_id — перепривязываем (обновляем external_id).
        """
        if data.user_id is None:
            raise ConflictError("user_id обязателен для привязки")

        async with self.uow_factory() as uow:
            repo = uow.repository(UserLink)

            by_external = await repo.get_single(
                provider=data.provider, external_id=data.external_id
            )
            if by_external is not None:
                if by_external.user_id != data.user_id:
                    raise ConflictError(
                        "Этот внешний аккаунт уже привязан к другому пользователю"
                    )
                if data.options:
                    item = await repo.update(
                        {"options": data.options}, None, id=by_external.id
                    )
                    await uow.commit()
                    return item
                return by_external

            by_user = await repo.get_single(
                user_id=data.user_id, provider=data.provider
            )
            try:
                if by_user is not None:
                    item = await repo.update(
                        {
                            "external_id": data.external_id,
                            "options": data.options,
                        },
                        None,
                        id=by_user.id,
                        user_id=data.user_id,
                    )
                else:
                    item = await repo.create(
                        {
                            "user_id": data.user_id,
                            "provider": data.provider,
                            "external_id": data.external_id,
                            "options": data.options or {},
                        }
                    )
                await uow.commit()
                return item
            except IntegrityError as exc:
                raise ConflictError(
                    "Не удалось привязать аккаунт: конфликт уникальности"
                ) from exc

    async def update_for_user(
        self, link_id: int, user_id: int, data: UserLinkUpdate
    ) -> UserLink | None:
        """Обновить привязку, только если она принадлежит пользователю."""
        updates = data.model_dump(exclude_unset=True)
        # provider/external_id в модели NOT NULL — не позволяем обнулить их
        for field in ("provider", "external_id"):
            if updates.get(field, "") is None:
                updates.pop(field, None)
        async with self.uow_factory() as uow:
            repo = uow.repository(UserLink)
            existing = await repo.get_single(id=link_id, user_id=user_id)
            if existing is None:
                return None
            if not updates:
                return existing
            try:
                item = await repo.update(
                    updates, None, id=link_id, user_id=user_id
                )
                await uow.commit()
                return item
            except IntegrityError as exc:
                raise ConflictError(
                    "Конфликт: такая привязка уже существует"
                ) from exc

    async def delete_for_user(self, link_id: int, user_id: int) -> bool:
        """Жёстко удалить привязку пользователя.

        Используем permanent delete, иначе soft-deleted строка продолжит
        занимать уникальный индекс ``(provider, external_id)`` и помешает
        повторной привязке.
        """
        async with self.uow_factory() as uow:
            repo = uow.repository(UserLink)
            existing = await repo.get_single(id=link_id, user_id=user_id)
            if existing is None:
                return False
            await repo.delete_permanent(id=link_id, user_id=user_id)
            await uow.commit()
            return True
