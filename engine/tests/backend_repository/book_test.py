import pytest

from src.repositories.backend_repository import BackendRepository


class TestBooking:
    """Тесты бронирований (запись по конкретному времени)."""

    @pytest.mark.asyncio
    async def test_create_booking_calls_post_with_payload(
        self, backend_repo, mocker
    ):
        mock_req = mocker.patch.object(
            BackendRepository, "_request",
            new=mocker.AsyncMock(return_value={"booking_id": 10}),
        )

        result = await backend_repo.create_booking(
            master_id=1,
            service_id=2,
            start_time="2026-11-24T16:00:00+03:00",
            client_name="Иван",
            client_phone="+79990001122",
            comment="Первый визит",
        )

        mock_req.assert_awaited_once_with(
            "POST",
            "/api/v0.0.1/bookings",
            json={
                "master_id": 1,
                "service_id": 2,
                "start_time": "2026-11-24T16:00:00+03:00",
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
            master_id=3,
            service_id=4,
            start_time="2026-11-24T17:30:00+03:00",
            client_name="Анна",
            client_phone="+79990000000",
        )

        mock_req.assert_awaited_once_with(
            "POST",
            "/api/v0.0.1/bookings",
            json={
                "master_id": 3,
                "service_id": 4,
                "start_time": "2026-11-24T17:30:00+03:00",
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
                master_id=1,
                service_id=1,
                start_time="2026-11-24T09:00:00+03:00",
                client_name="Тест",
                client_phone="+70000000000",
            )


class TestAvailability:
    """Тесты получения слотов."""

    @pytest.mark.asyncio
    async def test_get_availability_posts_body_with_master(
        self, backend_repo, mocker
    ):
        mock_req = mocker.patch.object(
            BackendRepository, "_request",
            new=mocker.AsyncMock(return_value=[]),
        )

        await backend_repo.get_availability(
            service_id=2,
            date_from="2026-11-24",
            date_to="2026-11-25",
            master_id=1,
        )

        mock_req.assert_awaited_once_with(
            "POST",
            "/api/v0.0.1/slots/available",
            json={
                "service_id": 2,
                "date_from": "2026-11-24",
                "date_to": "2026-11-25",
                "master_id": 1,
            },
        )

    @pytest.mark.asyncio
    async def test_get_availability_without_master_omits_field(
        self, backend_repo, mocker
    ):
        mock_req = mocker.patch.object(
            BackendRepository, "_request",
            new=mocker.AsyncMock(return_value=[]),
        )

        await backend_repo.get_availability(
            service_id=7,
            date_from="2026-11-24",
        )

        mock_req.assert_awaited_once_with(
            "POST",
            "/api/v0.0.1/slots/available",
            json={
                "service_id": 7,
                "date_from": "2026-11-24",
                "date_to": "2026-11-24",
            },
        )
