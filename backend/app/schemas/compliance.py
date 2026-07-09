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
