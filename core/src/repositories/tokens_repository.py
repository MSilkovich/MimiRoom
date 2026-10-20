from datetime import datetime, timezone

from sqlalchemy import select, update

from ..models.refresh_token import RefreshToken
from .sqlalchemy_repository import SqlAlchemyRepository


class RefreshTokenRepository(SqlAlchemyRepository[RefreshToken]):
    def __init__(self, session):
        super().__init__(RefreshToken, session)

    async def get_by_jti(self, jti: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.jti == jti)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def revoke(self, jti: str) -> None:
        stmt = update(RefreshToken).where(
            RefreshToken.jti == jti).values(revoked=True)
        await self.session.execute(stmt)
        await self.session.flush()

    async def revoke_all_for_user(self, user_id: int) -> None:
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
            .values(revoked=True)
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def purge_expired(self) -> None:
        now = datetime.now(timezone.utc)
        stmt = select(RefreshToken).where(RefreshToken.expires_at < now)
        res = await self.session.execute(stmt)
        for token in res.scalars():
            await self.session.delete(token)
        await self.session.flush()
