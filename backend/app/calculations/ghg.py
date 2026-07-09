"""RED III / EASA GHG intensity methodology (Annex V/VI style formula).

e = eec + el + ep + etd + eu - esca - eccs - eccr - eee   (gCO2eq/MJ)

Defaults below are illustrative and MUST be reconciled against the current
Delegated/Implementing Regulation before being used for real compliance
reporting -- the EU periodically revises default values per feedstock pathway.
"""

FOSSIL_COMPARATOR_GCO2_PER_MJ = 94.0  # RED III fossil fuel comparator for jet fuel
SAF_ENERGY_DENSITY_MJ_PER_L = 33.0  # approx net calorific value of SAF, MJ/L


def ghg_intensity(
    eec: float,
    el: float,
    ep: float,
    etd: float,
    eu: float = 0.0,
    esca: float = 0.0,
    eccs: float = 0.0,
    eccr: float = 0.0,
    eee: float = 0.0,
) -> float:
    """Total GHG intensity of the fuel pathway, gCO2eq/MJ."""
    return eec + el + ep + etd + eu - esca - eccs - eccr - eee


def ghg_savings_pct(intensity: float, fossil_comparator: float = FOSSIL_COMPARATOR_GCO2_PER_MJ) -> float:
    """% GHG savings for ReFuelEU/RED III reporting. Note: CORSIA eligibility and
    the tCO2e credit ledger use the separate CORSIA baseline/methodology in
    calculations/corsia.py (89 gCO2e/MJ), not this RED III comparator (94)."""
    if fossil_comparator <= 0:
        return 0.0
    return round((1 - intensity / fossil_comparator) * 100, 2)
