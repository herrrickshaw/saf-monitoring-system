from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CarbonCreditLedgerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    airline_delivery_id: int
    tco2e_saved: float
    status: str
    calculated_date: datetime
