from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..calculations.astm_pathways import is_conformant
from ..calculations.corsia import is_corsia_eligible
from ..calculations.ghg import FOSSIL_COMPARATOR_GCO2_PER_MJ, ghg_intensity, ghg_savings_pct
from ..db import get_db
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
    process_ep = batch.process_emissions_ep or feedstock.default_ep
    intensity = ghg_intensity(
        eec=feedstock.default_eec,
        el=0.0,
        ep=process_ep,
        etd=feedstock.default_etd,
    )
    savings_pct = ghg_savings_pct(intensity, FOSSIL_COMPARATOR_GCO2_PER_MJ)

    certificate = SAFCertificate(
        production_batch_id=batch.id,
        ghg_intensity=intensity,
        ghg_savings_pct=savings_pct,
        fossil_comparator=FOSSIL_COMPARATOR_GCO2_PER_MJ,
        eligible_feedstock=feedstock.category != "CROP",
        astm_conformant=is_conformant(
            batch.astm_pathway.max_blend_pct, batch.blend_ratio_pct, batch.lab_certification_ref
        ),
        corsia_eligible=is_corsia_eligible(savings_pct),
    )
    db.add(certificate)
    db.commit()
    db.refresh(certificate)
    return certificate
