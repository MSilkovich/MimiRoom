from ..models.measure_unit import MeasureUnit
from .sqlalchemy_repository import SqlAlchemyRepository


class MeasureUnitRepository(SqlAlchemyRepository[MeasureUnit]):
    def __init__(self, session):
        super().__init__(MeasureUnit, session)
