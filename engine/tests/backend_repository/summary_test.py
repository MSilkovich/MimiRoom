import pytest

from src.repositories.backend_repository import BackendRepository
from src.schemas import Summary


class TestBackendRepositoryGetUserSummary:
    """Интеграционные тесты get_user_summary против реального бэкенда."""

    @pytest.mark.asyncio
    async def test_get_user_summary_returns_summary_for_existing_user(
        self, backend_repo: BackendRepository, existing_user_id: int = 1
    ):
        result = await backend_repo.get_user_summary(existing_user_id)

        assert isinstance(result, Summary)
        assert result.user.id == existing_user_id

    # @pytest.mark.asyncio
    # async def test_get_user_summary_raises_for_unknown_user(
    #     self, backend_repo: BackendRepository, unknown_user_id: int = 52
    # ):
    #     with pytest.raises(Exception):
    #         await backend_repo.get_user_summary(unknown_user_id)
