"""ASTM D7566 approved SAF conversion pathways and their certified max blend ratios
with conventional Jet A-1. Values are illustrative defaults from the published
Annexes as of the D7566-23 revision -- reconcile against the current standard
edition before real compliance use, as ASTM periodically adds pathways/annexes.
"""

PATHWAYS = [
    {"code": "FT-SPK", "annex": "Annex A1", "max_blend_pct": 50.0,
     "description": "Fischer-Tropsch Synthetic Paraffinic Kerosene"},
    {"code": "HEFA-SPK", "annex": "Annex A2", "max_blend_pct": 50.0,
     "description": "Hydroprocessed Esters and Fatty Acids SPK"},
    {"code": "SIP", "annex": "Annex A3", "max_blend_pct": 10.0,
     "description": "Synthesized Iso-Paraffins from hydroprocessed fermented sugars"},
    {"code": "FT-SPK/A", "annex": "Annex A4", "max_blend_pct": 50.0,
     "description": "FT-SPK with Aromatics"},
    {"code": "ATJ-SPK", "annex": "Annex A5", "max_blend_pct": 50.0,
     "description": "Alcohol-to-Jet Synthetic Paraffinic Kerosene"},
    {"code": "CHJ", "annex": "Annex A6", "max_blend_pct": 50.0,
     "description": "Catalytic Hydrothermolysis Jet fuel"},
    {"code": "HC-HEFA-SPK", "annex": "Annex A7", "max_blend_pct": 10.0,
     "description": "Hydrocarbon-HEFA SPK (algae-derived)"},
    {"code": "HFS-SIP", "annex": "Annex A8", "max_blend_pct": 10.0,
     "description": "Hydroprocessed Fermented Sugars to Synthesized Iso-Paraffins"},
    {"code": "Co-processed HEFA/FT", "annex": "Annex A2/A1 co-processing", "max_blend_pct": 5.0,
     "description": "Co-processing of hydrotreated esters/FT feed in a conventional refinery"},
]


def is_conformant(pathway_max_blend_pct: float, blend_ratio_pct: float, lab_certification_ref: str) -> bool:
    """A batch is ASTM D7566 conformant if its blend ratio is within the pathway's
    certified max and a lab certification reference has been recorded (the fit-for
    -purpose lab test itself -- freeze point, density, etc. -- happens outside
    this system; we only track that a reference exists)."""
    return bool(lab_certification_ref) and blend_ratio_pct <= pathway_max_blend_pct
