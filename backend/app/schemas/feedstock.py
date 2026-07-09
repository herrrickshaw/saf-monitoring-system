from datetime import date

from pydantic import BaseModel, ConfigDict


class FeedstockCreate(BaseModel):
    name: str
    category: str  # IX-A | IX-B | CROP
    supplier: str
    default_eec: float = 0.0
    default_ep: float = 0.0
    default_etd: float = 0.0
    corsia_feedstock_key: str = ""
    corsia_iluc_value: float = 0.0


class FeedstockOut(FeedstockCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class FeedstockDeliveryCreate(BaseModel):
    feedstock_id: int
    arrival_date: date
    quantity_tonnes: float
    certificate_number: str
    origin_country: str


class FeedstockDeliveryOut(FeedstockDeliveryCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
