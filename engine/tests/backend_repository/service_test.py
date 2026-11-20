import pytest

from src.repositories.backend_repository import BackendRepository
from src.schemas import Summary


class TestServices:
    """Тесты получения услуг."""

    @pytest.mark.asyncio
    async def test_get_services_calls_request_with_defaults(
        self, backend_repo, mocker
    ):
        mock_req = mocker.patch.object(
            BackendRepository, "_request",
            new=mocker.AsyncMock(return_value=[]),
        )

        result = await backend_repo.get_services()

        mock_req.assert_awaited_once_with(
            "GET",
            "/api/v0.0.1/s/services",
            params={"limit": 100, "offset": 0},
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_get_services_passes_custom_limit_and_offset(
        self, backend_repo, mocker
    ):
        mock_req = mocker.patch.object(
            BackendRepository, "_request",
            new=mocker.AsyncMock(return_value=[]),
        )

        await backend_repo.get_services(limit=10, offset=20)

        mock_req.assert_awaited_once_with(
            "GET",
            "/api/v0.0.1/s/services",
            params={"limit": 10, "offset": 20},
        )

    @pytest.mark.asyncio
    async def test_get_services_returns_list_of_dicts(
        self, backend_repo, mocker
    ):
        payload = [{"id": 1, "name": "svc", "price": 100}]
        mocker.patch.object(
            BackendRepository, "_request",
            new=mocker.AsyncMock(return_value=payload),
        )

        result = await backend_repo.get_services()

        assert result == payload
