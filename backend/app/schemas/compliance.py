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


class CCTSStatusOut(BaseModel):
    saf_sector_notified: bool
    compliance_mechanism_sectors: list[str]
    offset_mechanism_phase_1_sectors: list[str]
    offset_mechanism_phase_2_sectors: list[str]
    governing_bodies: dict[str, str]
    note: str


class CCTSEstimateRequest(BaseModel):
    actual_intensity_tco2e_per_unit: float
    target_intensity_tco2e_per_unit: float
    output_units: float


class CCTSEstimateOut(BaseModel):
    surplus_deficit_tco2e: float
    ccc_equivalent: float
    is_surplus: bool
    note: str


class BioCarbonFeedstockRow(BaseModel):
    key: str
    label: str
    credit_factor_tco2e_per_tonne: float
    reference_capacity_tpd: float
    reference_credit_per_year: float


class BioCarbonTableOut(BaseModel):
    operating_days_per_year: int
    rows: list[BioCarbonFeedstockRow]
    note: str


class BioCarbonEstimateRequest(BaseModel):
    feedstock_key: str
    capacity_tpd: float


class BioCarbonEstimateOut(BaseModel):
    feedstock_key: str
    capacity_tpd: float
    credit_per_year_tco2e: float
    note: str
