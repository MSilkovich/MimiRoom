import pytest

from src.repositories.backend_repository import BackendRepository


@pytest.fixture
def backend_repo() -> BackendRepository:
    return BackendRepository()
