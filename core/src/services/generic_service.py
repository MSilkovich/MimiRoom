from typing import Type, TypeVar, Generic, Callable

from ..models.base_model import Base
from ..repositories.base_uow import UnitOfWork
from ..schemas.base_schema import Base as PySchema


ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=PySchema)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=PySchema)

UowFactory = Callable[[], UnitOfWork]


class GenericService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Общая основа сервисов.

    Хранит фабрику Unit of Work (типа ``db_helper.session_factory`` или
    лямбды ``lambda: SqlAlchemyUnitOfWork(...)``) и класс модели, для
    которой сервис предоставляет операции.
    """

    model: Type[ModelType]

    def __init__(self, uow_factory: UowFactory) -> None:
        self.uow_factory = uow_factory

