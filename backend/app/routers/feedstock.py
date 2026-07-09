from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Feedstock, FeedstockDelivery
from ..schemas.feedstock import (
    FeedstockCreate,
    FeedstockDeliveryCreate,
    FeedstockDeliveryOut,
    FeedstockOut,
)

router = APIRouter(prefix="/api/feedstock", tags=["feedstock"])


@router.get("", response_model=list[FeedstockOut])
def list_feedstocks(db: Session = Depends(get_db)):
    return db.query(Feedstock).all()


@router.post("", response_model=FeedstockOut)
def create_feedstock(payload: FeedstockCreate, db: Session = Depends(get_db)):
    feedstock = Feedstock(**payload.model_dump())
    db.add(feedstock)
    db.commit()
    db.refresh(feedstock)
    return feedstock


@router.get("/deliveries", response_model=list[FeedstockDeliveryOut])
def list_deliveries(db: Session = Depends(get_db)):
    return db.query(FeedstockDelivery).all()


@router.post("/deliveries", response_model=FeedstockDeliveryOut)
def create_delivery(payload: FeedstockDeliveryCreate, db: Session = Depends(get_db)):
    if not db.get(Feedstock, payload.feedstock_id):
        raise HTTPException(404, "Feedstock not found")
    delivery = FeedstockDelivery(**payload.model_dump())
    db.add(delivery)
    db.commit()
    db.refresh(delivery)
    return delivery
