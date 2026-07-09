"""CORSIA (ICAO Carbon Offsetting and Reduction Scheme for International Aviation)
eligibility check and emissions-reduction ledger conversion.

CORSIA requires a minimum lifecycle GHG emissions reduction (currently >=10% vs the
baseline) for a batch to qualify as a CORSIA Eligible Fuel -- confirm the current
threshold against the latest ICAO CORSIA SAF rules before compliance use.
"""

from .ghg import tco2e_saved

CORSIA_MIN_SAVINGS_PCT = 10.0


def is_corsia_eligible(ghg_savings_pct: float) -> bool:
    return ghg_savings_pct >= CORSIA_MIN_SAVINGS_PCT


def credit_for_delivery(volume_liters: float, ghg_intensity: float, fossil_comparator: float) -> float:
    """tCO2e emissions reduction credited for a given airline delivery."""
    return tco2e_saved(volume_liters, ghg_intensity, fossil_comparator)
