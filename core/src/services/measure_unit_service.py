from ..models.measure_unit import MeasureUnit
from ..schemas import MeasureUnitCreate, MeasureUnitUpdate
from .base_service import BaseService


class MeasureUnitService(BaseService[MeasureUnit, MeasureUnitCreate, MeasureUnitUpdate]):
    model = MeasureUnit
