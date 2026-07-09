"""Illustrative bio-carbon credit estimator, modeled on the UPNEDA (Uttar
Pradesh New & Renewable Energy Development Agency) "Bio Carbon Credit
Calculator" (https://online.upneda.in/app/Account/creditcalculator) -- a
state-level tool for biomass-to-energy plants that estimates annual carbon
credits from feedstock type and daily processing capacity (TPD).

UPNEDA's own page does not publish its real per-feedstock conversion factors
(it states results are "approximate" and directs operators to
carboncreditupneda@gmail.com for a precise, project-specific calculation).
The per-tonne credit factors below are therefore ILLUSTRATIVE placeholders
for demonstration purposes only -- order-of-magnitude estimates loosely based
on typical waste-to-energy displacement literature, not UPNEDA's actual
(unpublished) methodology or any official government figure. Replace them
with real project-specific or UPNEDA-confirmed values before using this for
anything beyond a rough illustration.

1 credit = 1 tCO2e, consistent with the CCC/CORSIA credit unit used elsewhere
in this system.
"""

OPERATING_DAYS_PER_YEAR = 300  # illustrative plant availability (~82% uptime)

# Illustrative tCO2e credit per tonne of feedstock processed per year, and a
# reference default capacity (TPD) matching the categories/scale shown on the
# UPNEDA calculator page.
FEEDSTOCK_TYPES = {
    "agri_waste": {"label": "Agriculture Waste", "credit_factor_tco2e_per_tonne": 0.35, "reference_capacity_tpd": 200},
    "animal_waste": {"label": "Animal Waste", "credit_factor_tco2e_per_tonne": 0.25, "reference_capacity_tpd": 300},
    "bagasse": {"label": "Bagasse", "credit_factor_tco2e_per_tonne": 0.30, "reference_capacity_tpd": 200},
    "corn_cob": {"label": "Corn Cob", "credit_factor_tco2e_per_tonne": 0.32, "reference_capacity_tpd": 200},
    "msw": {"label": "Municipal Solid Waste (MSW)", "credit_factor_tco2e_per_tonne": 0.20, "reference_capacity_tpd": 300},
    "napier_grass": {"label": "Napier Grass", "credit_factor_tco2e_per_tonne": 0.33, "reference_capacity_tpd": 150},
    "press_mud": {"label": "Press Mud", "credit_factor_tco2e_per_tonne": 0.22, "reference_capacity_tpd": 150},
    "used_palm_cooking_oil": {"label": "Used/Palm Cooking Oils", "credit_factor_tco2e_per_tonne": 0.85, "reference_capacity_tpd": 250},
    "waste_grains": {"label": "Waste Grains", "credit_factor_tco2e_per_tonne": 0.30, "reference_capacity_tpd": 200},
    "other": {"label": "Other", "credit_factor_tco2e_per_tonne": 0.25, "reference_capacity_tpd": 150},
}


def estimate_credit_per_year(feedstock_key: str, capacity_tpd: float) -> float | None:
    entry = FEEDSTOCK_TYPES.get(feedstock_key)
    if entry is None:
        return None
    return round(capacity_tpd * OPERATING_DAYS_PER_YEAR * entry["credit_factor_tco2e_per_tonne"], 1)
