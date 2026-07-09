from pydantic import BaseModel, ConfigDict


class BlendingRecordCreate(BaseModel):
    airport: str
    year: int
    total_jet_fuel_liters: float
    total_saf_liters: float


class BlendingRecordOut(BlendingRecordCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    actual_pct: float
    mandate_pct: float
    compliant: bool
