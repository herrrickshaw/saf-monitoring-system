from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..calculations.mandate_schedule import mandate_pct_for_year
from ..db import get_db
from ..models import BlendingRecord
from ..schemas.compliance import BlendingRecordCreate, BlendingRecordOut

router = APIRouter(prefix="/api/compliance", tags=["compliance"])


def _to_out(record: BlendingRecord) -> dict:
    mandate_pct = mandate_pct_for_year(record.year)
    return {
        "id": record.id,
        "airport": record.airport,
        "year": record.year,
        "total_jet_fuel_liters": record.total_jet_fuel_liters,
        "total_saf_liters": record.total_saf_liters,
        "actual_pct": record.actual_pct,
        "mandate_pct": mandate_pct,
        "compliant": record.actual_pct >= mandate_pct,
    }


@router.get("/blending", response_model=list[BlendingRecordOut])
def list_blending(
    airport: str | None = Query(None),
    year: int | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(BlendingRecord)
    if airport:
        query = query.filter(BlendingRecord.airport == airport)
    if year:
        query = query.filter(BlendingRecord.year == year)
    return [_to_out(r) for r in query.all()]


@router.post("/blending", response_model=BlendingRecordOut)
def create_blending_record(payload: BlendingRecordCreate, db: Session = Depends(get_db)):
    record = BlendingRecord(**payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return _to_out(record)
