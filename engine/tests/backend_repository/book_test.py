import pytest

from src.repositories.backend_repository import BackendRepository
from src.schemas import Summary


class TestBook:
    """Тесты бронирований."""

    @pytest.mark.asyncio
    async def test_create_booking_calls_post_with_payload(
        self, backend_repo, mocker
    ):
        data = {"service_id": 1, "user_id": 2}
        mock_req = mocker.patch.object(
            BackendRepository, "_request",
            new=mocker.AsyncMock(return_value={"id": 10}),
        )

        result = await backend_repo.create_booking(data)

        mock_req.assert_awaited_once_with(
            "POST",
            "/api/v0.0.1/book",
            json=data,
        )
        assert result == {"id": 10}

    @pytest.mark.asyncio
    async def test_create_booking_propagates_errors(self, backend_repo, mocker):
        mocker.patch.object(
            BackendRepository, "_request",
            new=mocker.AsyncMock(side_effect=RuntimeError("boom")),
        )

        with pytest.raises(RuntimeError, match="boom"):
            await backend_repo.create_booking({})
