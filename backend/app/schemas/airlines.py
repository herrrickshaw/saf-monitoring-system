from datetime import date

from pydantic import BaseModel, ConfigDict


class AirlineOfftakeCreate(BaseModel):
    airline_name: str
    contract_volume_liters: float
    delivery_airport: str
    contract_start: date
    contract_end: date


class AirlineOfftakeOut(AirlineOfftakeCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class AirlineDeliveryCreate(BaseModel):
    airline_offtake_id: int
    production_batch_id: int
    volume_liters: float
    delivery_date: date


class AirlineDeliveryOut(AirlineDeliveryCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
