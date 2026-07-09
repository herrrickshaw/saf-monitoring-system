from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AirlineDelivery, AirlineOfftake, ProductionBatch
from ..reports.airline_report import build_excel, build_pdf
from ..schemas.airlines import (
    AirlineDeliveryCreate,
    AirlineDeliveryOut,
    AirlineOfftakeCreate,
    AirlineOfftakeOut,
)

router = APIRouter(prefix="/api/airlines", tags=["airlines"])


@router.get("", response_model=list[AirlineOfftakeOut])
def list_offtakes(db: Session = Depends(get_db)):
    return db.query(AirlineOfftake).all()


@router.post("", response_model=AirlineOfftakeOut)
def create_offtake(payload: AirlineOfftakeCreate, db: Session = Depends(get_db)):
    offtake = AirlineOfftake(**payload.model_dump())
    db.add(offtake)
    db.commit()
    db.refresh(offtake)
    return offtake


@router.get("/deliveries", response_model=list[AirlineDeliveryOut])
def list_deliveries(db: Session = Depends(get_db)):
    return db.query(AirlineDelivery).all()


@router.post("/deliveries", response_model=AirlineDeliveryOut)
def create_delivery(payload: AirlineDeliveryCreate, db: Session = Depends(get_db)):
    if not db.get(AirlineOfftake, payload.airline_offtake_id):
        raise HTTPException(404, "Airline offtake not found")
    if not db.get(ProductionBatch, payload.production_batch_id):
        raise HTTPException(404, "Production batch not found")
    delivery = AirlineDelivery(**payload.model_dump())
    db.add(delivery)
    db.commit()
    db.refresh(delivery)
    return delivery


@router.get("/{offtake_id}/report")
def download_report(
    offtake_id: int,
    start: date = Query(...),
    end: date = Query(...),
    fmt: str = Query("pdf", pattern="^(pdf|excel)$"),
    db: Session = Depends(get_db),
):
    offtake = db.get(AirlineOfftake, offtake_id)
    if not offtake:
        raise HTTPException(404, "Airline offtake not found")

    if fmt == "pdf":
        content = build_pdf(db, offtake, start, end)
        media_type = "application/pdf"
        filename = f"{offtake.airline_name}_SAF_report_{start}_{end}.pdf"
    else:
        content = build_excel(db, offtake, start, end)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"{offtake.airline_name}_SAF_report_{start}_{end}.xlsx"

    return StreamingResponse(
        iter([content]),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
