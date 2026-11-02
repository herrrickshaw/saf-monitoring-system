"""All ``/api/compliance`` routes: blending, India CCTS/ICM, bio-carbon.

The route handlers live in the three ``compliance_*`` modules; this module
keeps the original ``routers.compliance.router`` entry point."""

from __future__ import annotations

from fastapi import APIRouter

from . import compliance_bio_carbon, compliance_blending, compliance_ccts

router = APIRouter(prefix="/api/compliance", tags=["compliance"])
router.include_router(compliance_blending.router)
router.include_router(compliance_ccts.router)
router.include_router(compliance_bio_carbon.router)
