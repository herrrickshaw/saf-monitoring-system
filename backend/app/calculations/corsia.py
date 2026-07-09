"""CORSIA (ICAO Carbon Offsetting and Reduction Scheme for International Aviation)
life cycle emissions methodology, default values, and eligibility check.

Source: ICAO "CORSIA Default Life Cycle Emissions Values for CORSIA Eligible Fuels",
8th Edition (approved 19 November 2025), Tables 1-6; and Annex 16 Volume IV,
Part II, Sustainability Criterion 1.1. Values are the published ICAO defaults as
of that edition -- ICAO periodically amends this document (only by Council
approval), so reconcile against the current edition before real compliance use.
https://www.icao.int/CORSIA/corsia-eligible-fuels

Methodology (Section 3.1 of the ICAO document):

    L_CEF = core LCA value + ILUC - emission credits         (gCO2e/MJ)

Wastes, residues, and by-products are assigned a default ILUC value of zero
(Section 5.2); only feedstocks classified as main/primary products carry a
non-zero default ILUC value (Section 5.3, Tables 7-12 -- not reproduced here
since this system's default feedstocks are all waste/residue/by-product).

The CORSIA baseline life cycle emissions value for conventional (fossil) jet
fuel is 89 gCO2e/MJ (used directly in the co-processing equations in Section
3.1.1 of the ICAO document). A fuel qualifies as a CORSIA Eligible Fuel only if
its lifecycle GHG emissions are reduced by at least 10% relative to this
baseline (Annex 16 Vol IV, Sustainability Criterion 1.1).

Worked example (Used Cooking Oil, HEFA-SPK pathway):
    core LCA value = 13.9 gCO2e/MJ (Table 2.6)
    ILUC = 0 (waste feedstock)
    L_CEF = 13.9 + 0 - 0 = 13.9 gCO2e/MJ
    reduction % = (1 - 13.9 / 89) * 100 = 84.38%  ->  eligible (>= 10%)
"""

from .ghg import SAF_ENERGY_DENSITY_MJ_PER_L

CORSIA_BASELINE_GCO2_PER_MJ = 89.0
CORSIA_MIN_REDUCTION_PCT = 10.0  # Annex 16 Vol IV, Sustainability Criterion 1.1

# Default Core LCA values (gCO2e/MJ), keyed by (ASTM pathway code, feedstock key).
# ICAO "CORSIA Default Life Cycle Emissions Values for CORSIA Eligible Fuels",
# 8th Edition, Tables 1 (Gasification FT), 2 (HEFA), 3 (ATJ-SPK/isobutanol),
# 4 (ATJ-SPK/ethanol, standalone conversion values used here), 5 (SIP).
# Correction values for coal-derived hydrogen/process heat inputs are not
# applied -- the base (non-coal) default is used.
DEFAULT_CORE_LCA_VALUES = {
    ("FT-SPK", "agricultural_residues"): 7.7,
    ("FT-SPK", "forestry_residues"): 8.3,
    ("FT-SPK", "msw_0pct_nbc"): 5.2,
    ("FT-SPK", "poplar"): 12.2,
    ("FT-SPK", "miscanthus"): 10.4,
    ("FT-SPK", "switchgrass"): 10.4,
    ("HEFA-SPK", "tallow"): 22.5,
    ("HEFA-SPK", "beef_tallow"): 29.7,
    ("HEFA-SPK", "poultry_fat"): 33.7,
    ("HEFA-SPK", "lard_fat"): 27.8,
    ("HEFA-SPK", "mixed_animal_fats"): 28.6,
    ("HEFA-SPK", "used_cooking_oil"): 13.9,
    ("HEFA-SPK", "palm_fatty_acid_distillate"): 20.7,
    ("HEFA-SPK", "corn_oil"): 17.2,
    ("HEFA-SPK", "soybean_oilseed"): 40.4,
    ("HEFA-SPK", "rapeseed_canola_oilseed"): 47.4,
    ("HEFA-SPK", "palm_ffb_high_biogas_capture"): 37.4,
    ("HEFA-SPK", "palm_ffb_low_biogas_capture"): 60.0,
    ("HEFA-SPK", "brassica_carinata_oilseed"): 34.4,
    ("HEFA-SPK", "camelina_oilseed"): 42.0,
    ("HEFA-SPK", "jatropha_oilseed_meal_fertilizer"): 46.9,
    ("HEFA-SPK", "jatropha_oilseed_meal_feed"): 46.8,
    ("HEFA-SPK", "non_standard_coconuts"): 26.9,
    ("HEFA-SPK", "palm_oil_mill_effluent"): 18.1,
    ("ATJ-SPK", "agricultural_residues_isobutanol"): 29.3,
    ("ATJ-SPK", "forestry_residues_isobutanol"): 23.8,
    ("ATJ-SPK", "sugarcane_isobutanol"): 24.0,
    ("ATJ-SPK", "corn_grain_isobutanol"): 55.8,
    ("ATJ-SPK", "miscanthus_isobutanol"): 43.4,
    ("ATJ-SPK", "switchgrass_isobutanol"): 43.4,
    ("ATJ-SPK", "molasses_isobutanol"): 27.0,
    ("ATJ-SPK", "sugarcane_ethanol_integrated"): 24.1,
    ("ATJ-SPK", "corn_grain_ethanol"): 65.7,
    ("ATJ-SPK", "agricultural_residues_ethanol_standalone"): 39.7,
    ("ATJ-SPK", "agricultural_residues_ethanol_integrated"): 24.6,
    ("ATJ-SPK", "forestry_residues_ethanol_standalone"): 40.0,
    ("ATJ-SPK", "forestry_residues_ethanol_integrated"): 24.9,
    ("ATJ-SPK", "waste_gases_ethanol_standalone"): 42.4,
    ("ATJ-SPK", "waste_gases_ethanol_integrated"): 29.4,
    ("SIP", "sugarcane"): 32.8,
    ("SIP", "sugar_beet"): 32.4,
}


def default_core_lca_value(pathway_code: str, feedstock_key: str) -> float | None:
    return DEFAULT_CORE_LCA_VALUES.get((pathway_code, feedstock_key))


def lcef(core_lca_value: float, iluc_value: float = 0.0, emission_credit: float = 0.0) -> float:
    """L_CEF = core LCA value + ILUC - emission credits, gCO2e/MJ."""
    return core_lca_value + iluc_value - emission_credit


def reduction_pct(lcef_value: float, baseline: float = CORSIA_BASELINE_GCO2_PER_MJ) -> float:
    if baseline <= 0:
        return 0.0
    return round((1 - lcef_value / baseline) * 100, 2)


def is_corsia_eligible(ghg_reduction_pct: float) -> bool:
    return ghg_reduction_pct >= CORSIA_MIN_REDUCTION_PCT


def tco2e_saved(volume_liters: float, lcef_value: float, baseline: float = CORSIA_BASELINE_GCO2_PER_MJ) -> float:
    """tCO2e emissions reduction credited for a given airline delivery, using the
    CORSIA baseline (89 gCO2e/MJ) -- not the RED III fossil comparator."""
    mj = volume_liters * SAF_ENERGY_DENSITY_MJ_PER_L
    saved_g = mj * (baseline - lcef_value)
    return round(saved_g / 1_000_000, 3)


def credit_for_delivery(volume_liters: float, lcef_value: float, baseline: float = CORSIA_BASELINE_GCO2_PER_MJ) -> float:
    return tco2e_saved(volume_liters, lcef_value, baseline)
