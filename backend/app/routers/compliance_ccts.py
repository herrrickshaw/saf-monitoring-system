"""India CCTS / ICM endpoints (status + what-if CCC estimate)."""

from __future__ import annotations

from fastapi import APIRouter

from ..calculations import ccts_icm
from ..schemas.compliance import CCTSEstimateOut, CCTSEstimateRequest, CCTSStatusOut

router = APIRouter()

@router.get("/ccts-icm/status", response_model=CCTSStatusOut)
def ccts_icm_status():
    """India's Carbon Credit Trading Scheme (CCTS) / Indian Carbon Market (ICM)
    coverage status -- SAF/aviation is not yet a notified sector under either
    mechanism. See calculations/ccts_icm.py for sources and details."""
    notified = ccts_icm.is_saf_covered_under_ccts()
    return CCTSStatusOut(
        saf_sector_notified=notified,
        compliance_mechanism_sectors=ccts_icm.COMPLIANCE_MECHANISM_SECTORS,
        offset_mechanism_phase_1_sectors=ccts_icm.OFFSET_MECHANISM_PHASE_1_SECTORS,
        offset_mechanism_phase_2_sectors=ccts_icm.OFFSET_MECHANISM_PHASE_2_SECTORS,
        governing_bodies=ccts_icm.GOVERNING_BODIES,
        note=(
            "SAF/aviation fuel production is not yet notified under CCTS."
            if not notified
            else "SAF/aviation fuel production is notified under CCTS."
        ),
    )


@router.post("/ccts-icm/estimate", response_model=CCTSEstimateOut)
def ccts_icm_estimate(payload: CCTSEstimateRequest):
    """What-if CCC surplus/deficit estimate using the BEE Compliance Mechanism
    formula. Informational only until BEE notifies SAF/aviation under CCTS and
    publishes an official target intensity -- see /ccts-icm/status."""
    surplus_deficit = ccts_icm.ccc_surplus_deficit(
        payload.actual_intensity_tco2e_per_unit,
        payload.target_intensity_tco2e_per_unit,
        payload.output_units,
    )
    return CCTSEstimateOut(
        surplus_deficit_tco2e=surplus_deficit,
        ccc_equivalent=round(abs(surplus_deficit) / ccts_icm.CCC_UNIT_TCO2E, 3),
        is_surplus=surplus_deficit >= 0,
        note=(
            "Estimate only -- SAF/aviation is not yet a notified CCTS sector; no real "
            "CCCs can be earned or owed until BEE publishes an official target."
            if not ccts_icm.is_saf_covered_under_ccts()
            else "Based on the notified official target intensity."
        ),
    )
