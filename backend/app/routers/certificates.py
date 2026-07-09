from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..calculations.astm_pathways import is_conformant
from ..calculations.corsia import default_core_lca_value, is_corsia_eligible, lcef, reduction_pct
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

    # RED III / ReFuelEU GHG intensity (94 gCO2eq/MJ comparator)
    process_ep = batch.process_emissions_ep or feedstock.default_ep
    intensity = ghg_intensity(
        eec=feedstock.default_eec,
        el=0.0,
        ep=process_ep,
        etd=feedstock.default_etd,
    )
    savings_pct = ghg_savings_pct(intensity, FOSSIL_COMPARATOR_GCO2_PER_MJ)

    # CORSIA L_CEF (89 gCO2e/MJ baseline) using ICAO's published default Core LCA
    # values for this ASTM pathway + feedstock combination
    core_lca = default_core_lca_value(batch.astm_pathway.code, feedstock.corsia_feedstock_key)
    if core_lca is None:
        raise HTTPException(
            400,
            f"No CORSIA default Core LCA value for pathway '{batch.astm_pathway.code}' / "
            f"feedstock key '{feedstock.corsia_feedstock_key}'. Record an actual life cycle "
            "emissions value per the ICAO 'CORSIA Methodology for Calculating Actual Life "
            "Cycle Emissions Values' instead, or set a matching corsia_feedstock_key.",
        )
    batch_lcef = lcef(core_lca, feedstock.corsia_iluc_value)
    corsia_pct = reduction_pct(batch_lcef)

    certificate = SAFCertificate(
        production_batch_id=batch.id,
        ghg_intensity=intensity,
        ghg_savings_pct=savings_pct,
        fossil_comparator=FOSSIL_COMPARATOR_GCO2_PER_MJ,
        eligible_feedstock=feedstock.category != "CROP",
        astm_conformant=is_conformant(
            batch.astm_pathway.max_blend_pct, batch.blend_ratio_pct, batch.lab_certification_ref
        ),
        corsia_core_lca_value=core_lca,
        corsia_lcef=batch_lcef,
        corsia_reduction_pct=corsia_pct,
        corsia_eligible=is_corsia_eligible(corsia_pct),
    )
    db.add(certificate)
    db.commit()
    db.refresh(certificate)
    return certificate
