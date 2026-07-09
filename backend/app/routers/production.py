from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import ASTMPathway, FeedstockDelivery, ProductionBatch
from ..schemas.production import ASTMPathwayOut, ProductionBatchCreate, ProductionBatchOut

router = APIRouter(prefix="/api/production", tags=["production"])


@router.get("/pathways", response_model=list[ASTMPathwayOut])
def list_pathways(db: Session = Depends(get_db)):
    return db.query(ASTMPathway).all()


@router.get("/batches", response_model=list[ProductionBatchOut])
def list_batches(db: Session = Depends(get_db)):
    return db.query(ProductionBatch).all()


@router.post("/batches", response_model=ProductionBatchOut)
def create_batch(payload: ProductionBatchCreate, db: Session = Depends(get_db)):
    if not db.get(ASTMPathway, payload.astm_pathway_id):
        raise HTTPException(404, "ASTM pathway not found")
    if not db.get(FeedstockDelivery, payload.feedstock_delivery_id):
        raise HTTPException(404, "Feedstock delivery not found")
    batch = ProductionBatch(**payload.model_dump())
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch
