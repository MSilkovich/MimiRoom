from ..models import User, Pet, Breed
from .sqlalchemy_repository import SqlAlchemyRepository
from ..schemas import Summary, UserSummary, PetSummary

from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload


class UserRepository(SqlAlchemyRepository[User]):
    def __init__(self, session):
        super().__init__(User, session)

    async def get_summary_by_id(self, user_id: int) -> Summary | None:
        # NOTE: только для использования в system_context - к текущему пользователю не обращаться, прав доступа нет
        stmt = (
            select(User)
            .where(User.user_id == user_id)
            .options(
                selectinload(User.pets)
                .joinedload(Pet.breed)
                .joinedload(Breed.pet_type)
            )
        )

        u = (await self.session.execute(stmt)).scalar_one_or_none()
        if not u:
            return None

        return Summary(
            user=UserSummary(id=u.user_id, name=u.name, phone=u.phone),
            pets=[PetSummary(id=p.pet_id, name=p.name, breed=p.breed.title,
                             pet_type=p.breed.pet_type.title) for p in u.pets]
        )
