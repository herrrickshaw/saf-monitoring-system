"""India's Carbon Credit Trading Scheme (CCTS) / Indian Carbon Market (ICM).

Source: Bureau of Energy Efficiency (BEE), https://beeindia.gov.in
Legal basis: Energy Conservation (Amendment) Act, 2022, Section 14, Clause (w)
(empowers the Central Government to specify a carbon trading scheme and the
issuance of Carbon Credit Certificates by a designated agency); Greenhouse
Gases Emission Intensity Target Rules, 2025.

STATUS (as of this writing): SAF / aviation fuel production is **not yet** a
notified sector under either CCTS mechanism:
  - Compliance Mechanism (mandatory, GHG emission-intensity targets):
    Aluminium, Chlor Alkali, Cement, Fertiliser, Iron & Steel, Pulp & Paper,
    Petrochemicals, Petroleum Refinery, Textile.
  - Offset Mechanism (voluntary project crediting), phased:
    Phase I: Energy, Industries, Agriculture, Waste handling, Forestry, Transport
    Phase II: Fugitive emissions, Construction, Solvent use, Carbon capture/
    storage/removal

This module implements the CCC accounting mechanics now so the platform is
ready the moment BEE notifies SAF/aviation-fuel production under CCTS (most
plausibly as an extension of Petroleum Refinery under the Compliance
Mechanism, or as a new Offset Mechanism project category) -- flip
SAF_SECTOR_NOTIFIED and supply the official target intensity once that
notification is published. Until then, treat any output here as a what-if
estimate, not a real compliance obligation or tradeable credit.

Mechanics: 1 Carbon Credit Certificate (CCC) = 1 tCO2e reduced or removed.
Under the Compliance Mechanism, an obligated entity that beats its GHG
emission-intensity target earns surplus CCCs; one that misses it must
surrender/purchase CCCs to cover the shortfall. CCCs are issued by BEE on
recommendation of the National Steering Committee for the ICM and Central
Government approval, recorded on the ICM Registry (operated by Grid
Controller of India), and traded on an electronic platform regulated by the
Central Electricity Regulatory Commission (CERC).
"""

SAF_SECTOR_NOTIFIED = False  # flip to True once BEE notifies SAF/aviation under CCTS

CCC_UNIT_TCO2E = 1.0

COMPLIANCE_MECHANISM_SECTORS = [
    "Aluminium",
    "Chlor Alkali",
    "Cement",
    "Fertiliser",
    "Iron & Steel",
    "Pulp & Paper",
    "Petrochemicals",
    "Petroleum Refinery",
    "Textile",
]

OFFSET_MECHANISM_PHASE_1_SECTORS = [
    "Energy",
    "Industries",
    "Agriculture",
    "Waste handling",
    "Forestry",
    "Transport",
]

OFFSET_MECHANISM_PHASE_2_SECTORS = [
    "Fugitive emissions",
    "Construction",
    "Solvent use",
    "Carbon capture/storage/removal",
]

GOVERNING_BODIES = {
    "National Steering Committee for ICM (NSCICM)": "Overall scheme oversight; chaired by Secretary, Ministry of Power",
    "Bureau of Energy Efficiency (BEE)": "Scheme administrator -- sets targets, issues CCCs, accredits verifiers",
    "Grid Controller of India (GCI)": "Operates the ICM Registry -- entity accounts, credit issuance, trading platform",
    "Central Electricity Regulatory Commission (CERC)": "Regulates the CCC trading platform/exchange",
}


def is_saf_covered_under_ccts() -> bool:
    return SAF_SECTOR_NOTIFIED


def ccc_surplus_deficit(
    actual_intensity_tco2e_per_unit: float,
    target_intensity_tco2e_per_unit: float,
    output_units: float,
) -> float:
    """CCCs earned (positive, entity beat its target) or owed (negative, entity
    missed its target), in tCO2e / CCC units. output_units is the entity's
    production output for the compliance period, in the same "per unit of
    product" basis as the target (e.g. tonnes of SAF)."""
    return round((target_intensity_tco2e_per_unit - actual_intensity_tco2e_per_unit) * output_units, 3)
