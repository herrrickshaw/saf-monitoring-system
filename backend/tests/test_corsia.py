import pytest

from app.calculations.corsia import (
    CORSIA_BASELINE_GCO2_PER_MJ,
    default_core_lca_value,
    is_corsia_eligible,
    lcef,
    reduction_pct,
    tco2e_saved,
)


def test_corsia_baseline_is_89():
    assert CORSIA_BASELINE_GCO2_PER_MJ == 89.0


def test_default_core_lca_lookup_used_cooking_oil():
    # ICAO Table 2.6 (HEFA-SPK, Used cooking oil)
    assert default_core_lca_value("HEFA-SPK", "used_cooking_oil") == 13.9


def test_default_core_lca_lookup_missing_combination_is_none():
    assert default_core_lca_value("HEFA-SPK", "unobtainium") is None


def test_lcef_sums_core_and_iluc_minus_credit():
    assert lcef(core_lca_value=13.9, iluc_value=0.0) == 13.9
    assert lcef(core_lca_value=13.9, iluc_value=5.0, emission_credit=2.0) == 16.9


def test_worked_example_used_cooking_oil_reduction():
    # ICAO worked example: UCO / HEFA-SPK, waste feedstock -> ILUC 0
    core = default_core_lca_value("HEFA-SPK", "used_cooking_oil")
    value = lcef(core, iluc_value=0.0)
    pct = reduction_pct(value)
    assert value == 13.9
    assert pct == 84.38
    assert is_corsia_eligible(pct) is True


def test_eligibility_threshold_is_10_pct():
    assert is_corsia_eligible(10.0) is True
    assert is_corsia_eligible(9.99) is False


def test_tco2e_saved_zero_when_lcef_equals_baseline():
    assert tco2e_saved(1_000_000, lcef_value=CORSIA_BASELINE_GCO2_PER_MJ) == 0.0


def test_tco2e_saved_positive_for_low_carbon_fuel():
    assert tco2e_saved(1_000_000, lcef_value=13.9) > 0


def test_tco2e_saved_scales_with_volume():
    small = tco2e_saved(1000, lcef_value=13.9)
    large = tco2e_saved(10000, lcef_value=13.9)
    assert large == pytest.approx(small * 10, abs=0.01)


# ---------------------------------------------------------------------------
# ILUC for crop (main-product) feedstocks.
# Expected values: ICAO CORSIA default tables as reproduced (core / ILUC / total
# columns) in ISCC CORSIA 205 "Life Cycle Emissions" v2.0 -- Global ILUC column.
#   ETJ corn grain            65.7 + 34.9 = 100.6  (USA 25.1 -> 90.8)  fails
#   ATJ-isobutanol corn grain 55.8 + 29.7 =  85.5  (USA 22.1 -> 77.9)  fails (Global)
#   HEFA soybean              40.4 + 25.8 =  66.2
#   ATJ-isobutanol molasses   27.0 +  9.1 =  36.1  (27.0 is CORE, not ILUC)
#   HEFA jatropha (fertiliser) 46.9 - 24.8 = 22.1
# ---------------------------------------------------------------------------

def test_default_iluc_is_zero_for_wastes_and_residues():
    from app.calculations.corsia import default_iluc_value
    for key in ("used_cooking_oil", "tallow", "agricultural_residues_isobutanol",
                "forestry_residues_ethanol_standalone"):
        pathway = "HEFA-SPK" if key in ("used_cooking_oil", "tallow") else "ATJ-SPK"
        assert default_iluc_value(pathway, key) == 0.0


@pytest.mark.parametrize("pathway,key,iluc,total", [
    ("ATJ-SPK", "corn_grain_ethanol", 34.9, 100.6),
    ("ATJ-SPK", "corn_grain_isobutanol", 29.7, 85.5),
    ("HEFA-SPK", "soybean_oilseed", 25.8, 66.2),
    ("ATJ-SPK", "molasses_isobutanol", 9.1, 36.1),
    ("ATJ-SPK", "sugarcane_isobutanol", 9.1, 33.1),
    ("ATJ-SPK", "sugarcane_ethanol_integrated", 8.5, 32.6),
    ("HEFA-SPK", "jatropha_oilseed_meal_fertilizer", -24.8, 22.1),
    ("HEFA-SPK", "jatropha_oilseed_meal_feed", -48.1, -1.3),
])
def test_default_iluc_and_total_match_published_table(pathway, key, iluc, total):
    from app.calculations.corsia import default_iluc_value
    assert default_iluc_value(pathway, key) == iluc
    assert lcef(default_core_lca_value(pathway, key), default_iluc_value(pathway, key)) == pytest.approx(total)


def test_corn_ethanol_to_jet_is_not_corsia_eligible_once_iluc_is_counted():
    from app.calculations.corsia import default_iluc_value
    total = lcef(default_core_lca_value("ATJ-SPK", "corn_grain_ethanol"),
                 default_iluc_value("ATJ-SPK", "corn_grain_ethanol"))
    pct = reduction_pct(total)
    assert pct == pytest.approx((1 - 100.6 / 89) * 100, abs=0.01)   # -13.03 %
    assert is_corsia_eligible(pct) is False


def test_core_only_would_wrongly_pass_corn_ethanol():
    # Documents the failure mode: core alone (ILUC treated as 0) gives a 26% cut.
    pct = reduction_pct(lcef(default_core_lca_value("ATJ-SPK", "corn_grain_ethanol"), 0.0))
    assert pct == pytest.approx(26.18, abs=0.01) and is_corsia_eligible(pct)


def test_reduction_pct_zero_baseline_guard_and_negative_lcef():
    assert reduction_pct(10.0, baseline=0.0) == 0.0
    assert reduction_pct(-1.3) == pytest.approx(101.46, abs=0.01)


def test_tco2e_saved_hand_computed():
    # 1,000,000 L x 34.37 MJ/L? use the module constant, then (89-13.9) g/MJ -> t
    from app.calculations.ghg import SAF_ENERGY_DENSITY_MJ_PER_L
    expected = round(1_000_000 * SAF_ENERGY_DENSITY_MJ_PER_L * (89.0 - 13.9) / 1e6, 3)
    assert tco2e_saved(1_000_000, 13.9) == expected
