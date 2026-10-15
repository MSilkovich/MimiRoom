from abc import abstractmethod, ABC


class UnitOfWork(ABC):

    @abstractmethod
    def __init__(self, session_factory=None):
        ...

    @abstractmethod
    async def __aenter__(self):
        ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc, tb):
        ...

    @abstractmethod
    async def commit(self):
        ...

    @abstractmethod
    async def rollback(self):
        ...

