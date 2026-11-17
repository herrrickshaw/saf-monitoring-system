"""Illustrative UPNEDA-style bio-carbon credit endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..calculations import biocarbon_estimator
from ..schemas.compliance import (
    BioCarbonEstimateOut,
    BioCarbonEstimateRequest,
    BioCarbonFeedstockRow,
    BioCarbonTableOut,
)

router = APIRouter()

_BIOCARBON_NOTE = (
    "Illustrative estimate only, modeled on the UPNEDA Bio Carbon Credit Calculator "
    "(online.upneda.in) -- UPNEDA does not publish its real per-feedstock conversion "
    "factors; the figures here are placeholder order-of-magnitude values for "
    "demonstration, not an official or project-accurate calculation."
)


@router.get("/bio-carbon/table", response_model=BioCarbonTableOut)
def bio_carbon_table():
    """Reference table of illustrative bio-carbon credit factors by feedstock
    type, at UPNEDA's example reference capacities. See
    calculations/biocarbon_estimator.py."""
    rows = [
        BioCarbonFeedstockRow(
            key=key,
            label=entry["label"],
            credit_factor_tco2e_per_tonne=entry["credit_factor_tco2e_per_tonne"],
            reference_capacity_tpd=entry["reference_capacity_tpd"],
            reference_credit_per_year=biocarbon_estimator.estimate_credit_per_year(
                key, entry["reference_capacity_tpd"]
            ),
        )
        for key, entry in biocarbon_estimator.FEEDSTOCK_TYPES.items()
    ]
    return BioCarbonTableOut(
        operating_days_per_year=biocarbon_estimator.OPERATING_DAYS_PER_YEAR,
        rows=rows,
        note=_BIOCARBON_NOTE,
    )


@router.post("/bio-carbon/estimate", response_model=BioCarbonEstimateOut)
def bio_carbon_estimate(payload: BioCarbonEstimateRequest):
    credit = biocarbon_estimator.estimate_credit_per_year(payload.feedstock_key, payload.capacity_tpd)
    if credit is None:
        raise HTTPException(400, f"Unknown feedstock key '{payload.feedstock_key}'")
    return BioCarbonEstimateOut(
        feedstock_key=payload.feedstock_key,
        capacity_tpd=payload.capacity_tpd,
        credit_per_year_tco2e=credit,
        note=_BIOCARBON_NOTE,
    )
