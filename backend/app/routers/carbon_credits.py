from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..calculations.corsia import CORSIA_MIN_REDUCTION_PCT, credit_for_delivery
from ..db import get_db
from ..models import AirlineDelivery, CarbonCreditLedger
from ..schemas.carbon_credits import CarbonCreditLedgerOut

router = APIRouter(prefix="/api/carbon-credits", tags=["carbon-credits"])


@router.get("/ledger", response_model=list[CarbonCreditLedgerOut])
def list_ledger(db: Session = Depends(get_db)):
    return db.query(CarbonCreditLedger).all()


@router.post("/generate/{airline_delivery_id}", response_model=CarbonCreditLedgerOut)
def generate_ledger_entry(airline_delivery_id: int, db: Session = Depends(get_db)):
    delivery = db.get(AirlineDelivery, airline_delivery_id)
    if not delivery:
        raise HTTPException(404, "Airline delivery not found")
    if delivery.credit_ledger:
        raise HTTPException(400, "Ledger entry already generated for this delivery")
    certificate = delivery.batch.certificate
    if not certificate:
        raise HTTPException(400, "Batch has no SAF certificate yet -- generate one first")
    if not certificate.corsia_eligible:
        raise HTTPException(
            400,
            f"Batch does not meet the CORSIA {CORSIA_MIN_REDUCTION_PCT}% minimum lifecycle "
            f"GHG reduction (actual: {certificate.corsia_reduction_pct}%) -- not eligible for credit",
        )

    tco2e = credit_for_delivery(delivery.volume_liters, certificate.corsia_lcef)
    entry = CarbonCreditLedger(airline_delivery_id=delivery.id, tco2e_saved=tco2e)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.post("/{ledger_id}/report", response_model=CarbonCreditLedgerOut)
def mark_reported(ledger_id: int, db: Session = Depends(get_db)):
    entry = db.get(CarbonCreditLedger, ledger_id)
    if not entry:
        raise HTTPException(404, "Ledger entry not found")
    entry.status = "reported"
    db.commit()
    db.refresh(entry)
    return entry
