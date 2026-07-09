from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SAFCertificateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    production_batch_id: int
    ghg_intensity: float
    ghg_savings_pct: float
    fossil_comparator: float
    eligible_feedstock: bool
    astm_conformant: bool
    corsia_core_lca_value: float
    corsia_lcef: float
    corsia_reduction_pct: float
    corsia_eligible: bool
    issued_date: datetime
