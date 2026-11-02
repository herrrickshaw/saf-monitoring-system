from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..calculations.certification import MissingCorsiaDefault, compute_certificate_metrics
from ..db import get_db, persist
from ..models import ProductionBatch, SAFCertificate
from ..schemas.certificates import SAFCertificateOut

router = APIRouter(prefix="/api/certificates", tags=["certificates"])


@router.get("", response_model=list[SAFCertificateOut])
def list_certificates(db: Session = Depends(get_db)):
    return db.query(SAFCertificate).all()


@router.post("/generate/{batch_id}", response_model=SAFCertificateOut)
def generate_certificate(batch_id: int, db: Session = Depends(get_db)):
    batch = db.get(ProductionBatch, batch_id)
    if not batch:
        raise HTTPException(404, "Production batch not found")
    if batch.certificate:
        raise HTTPException(400, "Certificate already generated for this batch")

    feedstock = batch.feedstock_delivery.feedstock
    try:
        metrics = compute_certificate_metrics(
            eec=feedstock.default_eec,
            ep=batch.process_emissions_ep or feedstock.default_ep,
            etd=feedstock.default_etd,
            feedstock_category=feedstock.category,
            corsia_feedstock_key=feedstock.corsia_feedstock_key,
            corsia_iluc_value=feedstock.corsia_iluc_value,
            pathway_code=batch.astm_pathway.code,
            pathway_max_blend_pct=batch.astm_pathway.max_blend_pct,
            blend_ratio_pct=batch.blend_ratio_pct,
            lab_certification_ref=batch.lab_certification_ref,
        )
    except MissingCorsiaDefault as exc:
        raise HTTPException(400, str(exc)) from exc

    certificate = SAFCertificate(production_batch_id=batch.id, **metrics.as_dict())
    return persist(db, certificate)
