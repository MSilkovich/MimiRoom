import pytest

from src.repositories.backend_repository import BackendRepository


class TestBooking:
    """Тесты бронирований (slot-based API)."""

    @pytest.mark.asyncio
    async def test_create_booking_calls_post_with_payload(
        self, backend_repo, mocker
    ):
        mock_req = mocker.patch.object(
            BackendRepository, "_request",
            new=mocker.AsyncMock(return_value={"booking_id": 10}),
        )

        result = await backend_repo.create_booking(
            slot_id=5,
            client_name="Иван",
            client_phone="+79990001122",
            comment="Первый визит",
        )

        mock_req.assert_awaited_once_with(
            "POST",
            "/api/v0.0.1/bookings",
            json={
                "slot_id": 5,
                "client_name": "Иван",
                "client_phone": "+79990001122",
                "comment": "Первый визит",
            },
        )
        assert result == {"booking_id": 10}

    @pytest.mark.asyncio
    async def test_create_booking_without_comment_omits_field(
        self, backend_repo, mocker
    ):
        mock_req = mocker.patch.object(
            BackendRepository, "_request",
            new=mocker.AsyncMock(return_value={"booking_id": 11}),
        )

        await backend_repo.create_booking(
            slot_id=6,
            client_name="Анна",
            client_phone="+79990000000",
        )

        mock_req.assert_awaited_once_with(
            "POST",
            "/api/v0.0.1/bookings",
            json={
                "slot_id": 6,
                "client_name": "Анна",
                "client_phone": "+79990000000",
            },
        )

    @pytest.mark.asyncio
    async def test_create_booking_propagates_errors(self, backend_repo, mocker):
        mocker.patch.object(
            BackendRepository, "_request",
            new=mocker.AsyncMock(side_effect=RuntimeError("boom")),
        )

        with pytest.raises(RuntimeError, match="boom"):
            await backend_repo.create_booking(
                slot_id=1,
                client_name="Тест",
                client_phone="+70000000000",
            )


class TestAvailability:
    """Тесты получения слотов."""

    @pytest.mark.asyncio
    async def test_get_availability_calls_request_with_params(
        self, backend_repo, mocker
    ):
        mock_req = mocker.patch.object(
            BackendRepository, "_request",
            new=mocker.AsyncMock(return_value=[]),
        )

        await backend_repo.get_availability(
            master_id=1,
            service_id=2,
            date_from="2026-11-24",
            date_to="2026-11-25",
        )

        mock_req.assert_awaited_once_with(
            "GET",
            "/api/v0.0.1/slots/availability",
            params={
                "master_id": 1,
                "service_id": 2,
                "date_from": "2026-11-24",
                "date_to": "2026-11-25",
                "only_available": True,
                "limit": 200,
            },
        )
