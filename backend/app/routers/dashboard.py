from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..calculations.mandate_schedule import mandate_pct_for_year
from ..db import get_db
from ..models import AirlineOfftake, BlendingRecord, CarbonCreditLedger, ProductionBatch

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    total_saf_liters = db.query(func.coalesce(func.sum(ProductionBatch.saf_output_liters), 0.0)).scalar()
    total_tco2e = db.query(func.coalesce(func.sum(CarbonCreditLedger.tco2e_saved), 0.0)).scalar()
    active_contracts = (
        db.query(func.count(AirlineOfftake.id)).filter(AirlineOfftake.contract_end >= date.today()).scalar()
    )

    current_year = date.today().year
    blending_records = db.query(BlendingRecord).filter(BlendingRecord.year == current_year).all()
    if blending_records:
        avg_actual_pct = sum(r.actual_pct for r in blending_records) / len(blending_records)
    else:
        avg_actual_pct = 0.0

    return {
        "total_saf_liters": total_saf_liters,
        "total_tco2e_credited": total_tco2e,
        "active_contracts": active_contracts,
        "current_year_blending_pct": round(avg_actual_pct, 2),
        "current_year_mandate_pct": mandate_pct_for_year(current_year),
    }
