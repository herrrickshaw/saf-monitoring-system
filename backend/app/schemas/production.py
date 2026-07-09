from datetime import date

from pydantic import BaseModel, ConfigDict


class ProductionBatchCreate(BaseModel):
    batch_code: str
    start_date: date
    end_date: date
    astm_pathway_id: int
    feedstock_delivery_id: int
    feedstock_input_tonnes: float
    saf_output_liters: float
    blend_ratio_pct: float
    lab_certification_ref: str = ""
    process_emissions_ep: float = 0.0


class ProductionBatchOut(ProductionBatchCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    yield_pct: float


class ASTMPathwayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    annex: str
    max_blend_pct: float
    description: str
