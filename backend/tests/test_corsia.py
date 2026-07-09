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
