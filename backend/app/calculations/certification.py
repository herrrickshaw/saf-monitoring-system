"""Pure assembly of the GHG / ASTM / CORSIA metrics stored on a SAF certificate.

Takes plain numbers in, returns a dataclass out -- no database or HTTP types --
so the logic behind ``POST /api/certificates/generate/{batch_id}`` is testable
in isolation."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .astm_pathways import is_conformant
from .corsia import default_core_lca_value, is_corsia_eligible, lcef, reduction_pct
from .ghg import FOSSIL_COMPARATOR_GCO2_PER_MJ, ghg_intensity, ghg_savings_pct


class MissingCorsiaDefault(LookupError):
    """No ICAO default Core LCA value exists for the pathway/feedstock pair."""

    def __init__(self, pathway_code: str, feedstock_key: str | None):
        self.pathway_code = pathway_code
        self.feedstock_key = feedstock_key
        super().__init__(
            f"No CORSIA default Core LCA value for pathway '{pathway_code}' / "
            f"feedstock key '{feedstock_key}'. Record an actual life cycle "
            "emissions value per the ICAO 'CORSIA Methodology for Calculating Actual Life "
            "Cycle Emissions Values' instead, or set a matching corsia_feedstock_key."
        )


@dataclass(frozen=True)
class CertificateMetrics:
    ghg_intensity: float
    ghg_savings_pct: float
    fossil_comparator: float
    eligible_feedstock: bool
    astm_conformant: bool
    corsia_core_lca_value: float
    corsia_lcef: float
    corsia_reduction_pct: float
    corsia_eligible: bool

    def as_dict(self) -> dict:
        return asdict(self)


def compute_certificate_metrics(
    *,
    eec: float,
    ep: float,
    etd: float,
    feedstock_category: str,
    corsia_feedstock_key: str | None,
    corsia_iluc_value: float,
    pathway_code: str,
    pathway_max_blend_pct: float,
    blend_ratio_pct: float,
    lab_certification_ref: str | None,
) -> CertificateMetrics:
    """GHG (RED III, 94 gCO2eq/MJ comparator) and CORSIA (89 gCO2e/MJ) metrics for one batch.

    ``ep`` is the already-resolved process emission (batch value or feedstock default).
    Raises MissingCorsiaDefault when ICAO publishes no default for the pathway/feedstock."""
    intensity = ghg_intensity(eec=eec, el=0.0, ep=ep, etd=etd)
    savings_pct = ghg_savings_pct(intensity, FOSSIL_COMPARATOR_GCO2_PER_MJ)

    core_lca = default_core_lca_value(pathway_code, corsia_feedstock_key)
    if core_lca is None:
        raise MissingCorsiaDefault(pathway_code, corsia_feedstock_key)
    batch_lcef = lcef(core_lca, corsia_iluc_value)
    corsia_pct = reduction_pct(batch_lcef)

    return CertificateMetrics(
        ghg_intensity=intensity,
        ghg_savings_pct=savings_pct,
        fossil_comparator=FOSSIL_COMPARATOR_GCO2_PER_MJ,
        eligible_feedstock=feedstock_category != "CROP",
        astm_conformant=is_conformant(pathway_max_blend_pct, blend_ratio_pct, lab_certification_ref),
        corsia_core_lca_value=core_lca,
        corsia_lcef=batch_lcef,
        corsia_reduction_pct=corsia_pct,
        corsia_eligible=is_corsia_eligible(corsia_pct),
    )
