from ..models.measure_unit import MeasureUnit
from ..schemas import MeasureUnitCreate, MeasureUnitUpdate
from .base import BaseService


class MeasureUnitService(BaseService[MeasureUnit, MeasureUnitCreate, MeasureUnitUpdate]):
    model = MeasureUnit
