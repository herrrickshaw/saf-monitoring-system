"""Boundary and guard-clause tests for the pure calculation helpers and the
model properties. Expected values come from the module constants/formulas, not
from regulatory facts recalled from memory."""

import os
import tempfile

# app.db binds its engine at first import. Make sure an import that happens
# before conftest's `client` fixture never falls back to the repo-local saf.db.
os.environ.setdefault("SAF_DB_PATH", os.path.join(tempfile.mkdtemp(prefix="saf-test-"), "default.db"))

import pytest

from app.calculations import astm_pathways, biocarbon_estimator, ccts_icm, corsia, ghg, mandate_schedule


# ---- ghg ----------------------------------------------------------------------------


def test_ghg_intensity_subtracts_every_credit_term():
    got = ghg.ghg_intensity(eec=1, el=2, ep=3, etd=4, eu=5, esca=0.5, eccs=0.25, eccr=0.125, eee=0.0625)
    assert got == 1 + 2 + 3 + 4 + 5 - 0.5 - 0.25 - 0.125 - 0.0625
    assert ghg.ghg_intensity(1, 0, 0, 0) == 1  # optional terms default to zero


def test_ghg_savings_guard_and_rounding():
    assert ghg.ghg_savings_pct(10.0, fossil_comparator=0.0) == 0.0
    assert ghg.ghg_savings_pct(10.0, fossil_comparator=-5.0) == 0.0
    assert ghg.ghg_savings_pct(94.0) == 0.0  # default comparator: no saving at the comparator
    assert ghg.ghg_savings_pct(0.0) == 100.0
    assert ghg.ghg_savings_pct(100.0) < 0  # worse than fossil is a negative saving, not clamped
    assert ghg.ghg_savings_pct(1.0, 3.0) == round((1 - 1 / 3) * 100, 2) == 66.67


# ---- corsia ---------------------------------------------------------------------------


def test_eligibility_threshold_is_inclusive():
    t = corsia.CORSIA_MIN_REDUCTION_PCT
    assert corsia.is_corsia_eligible(t) is True
    assert corsia.is_corsia_eligible(t - 0.01) is False
    assert corsia.is_corsia_eligible(t + 0.01) is True


def test_reduction_pct_at_baseline_and_rounding():
    assert corsia.reduction_pct(corsia.CORSIA_BASELINE_GCO2_PER_MJ) == 0.0
    assert corsia.reduction_pct(0.0) == 100.0
    assert corsia.reduction_pct(1.0, baseline=3.0) == 66.67
    assert corsia.reduction_pct(1.0, baseline=-3.0) == 0.0


def test_lcef_emission_credit_and_defaults():
    assert corsia.lcef(10.0) == 10.0
    assert corsia.lcef(10.0, 5.0, 2.0) == 13.0
    assert corsia.lcef(10.0, emission_credit=4.0) == 6.0


def test_tco2e_saved_rounds_to_three_decimals_and_is_negative_above_baseline():
    got = corsia.tco2e_saved(1.0, 0.0, baseline=1.0)
    assert got == round(ghg.SAF_ENERGY_DENSITY_MJ_PER_L / 1_000_000, 3)
    assert corsia.tco2e_saved(1_000_000.0, corsia.CORSIA_BASELINE_GCO2_PER_MJ + 10) < 0
    assert corsia.tco2e_saved(0.0, 5.0) == 0.0
    assert corsia.credit_for_delivery(777.0, 12.5) == corsia.tco2e_saved(777.0, 12.5)
    assert corsia.credit_for_delivery(777.0, 12.5, baseline=50.0) == corsia.tco2e_saved(777.0, 12.5, 50.0)


def test_resolve_iluc_supplied_value_wins_even_if_negative():
    key = "corn_grain_ethanol"
    default = corsia.default_iluc_value("ATJ-SPK", key)
    assert corsia.resolve_iluc("ATJ-SPK", key, 12.5) == 12.5
    assert corsia.resolve_iluc("ATJ-SPK", key, -3.0) == -3.0
    assert corsia.resolve_iluc("ATJ-SPK", key, 0.0) == default
    assert corsia.resolve_iluc("ATJ-SPK", key) == default


def test_resolve_iluc_unverified_crop_needs_explicit_value():
    for key in corsia.CROP_KEYS_WITHOUT_DEFAULT_ILUC:
        assert corsia.default_iluc_value("FT-SPK", key) is None
        assert corsia.resolve_iluc("FT-SPK", key) is None
        assert corsia.resolve_iluc("FT-SPK", key, 7.0) == 7.0


def test_unknown_feedstock_key_defaults_to_zero_iluc_and_no_core_value():
    assert corsia.default_iluc_value("HEFA-SPK", "something_new") == 0.0
    assert corsia.default_core_lca_value("HEFA-SPK", "something_new") is None
    assert corsia.default_core_lca_value("NOPE", "used_cooking_oil") is None
    # the lookup is keyed on the PAIR, not the feedstock alone
    assert corsia.default_core_lca_value("ATJ-SPK", "used_cooking_oil") is None


def test_every_table_key_pairs_a_known_pathway_code():
    codes = {p["code"] for p in astm_pathways.PATHWAYS}
    assert {pathway for pathway, _ in corsia.DEFAULT_CORE_LCA_VALUES} <= codes
    assert set(corsia.DEFAULT_ILUC_VALUES).isdisjoint(corsia.CROP_KEYS_WITHOUT_DEFAULT_ILUC)
    feedstock_keys = {key for _, key in corsia.DEFAULT_CORE_LCA_VALUES}
    assert set(corsia.DEFAULT_ILUC_VALUES) <= feedstock_keys
    assert corsia.CROP_KEYS_WITHOUT_DEFAULT_ILUC <= feedstock_keys


# ---- mandate schedule ---------------------------------------------------------------------


def test_mandate_every_scheduled_year_and_edges():
    sched = mandate_schedule.MANDATE_SCHEDULE_PCT
    for year, pct in sched.items():
        assert mandate_schedule.mandate_pct_for_year(year) == pct
    first, last = min(sched), max(sched)
    assert mandate_schedule.mandate_pct_for_year(first - 1) == 0.0
    assert mandate_schedule.mandate_pct_for_year(last + 1) == sched[last]
    assert mandate_schedule.mandate_pct_for_year(last + 100) == sched[last]
    assert mandate_schedule.mandate_pct_for_year(0) == 0.0


def test_mandate_schedule_is_gapless_and_non_decreasing():
    sched = mandate_schedule.MANDATE_SCHEDULE_PCT
    years = sorted(sched)
    assert years == list(range(years[0], years[-1] + 1))
    values = [sched[y] for y in years]
    assert values == sorted(values)


# ---- ccts / biocarbon ----------------------------------------------------------------------------


def test_ccc_surplus_zero_rounding_and_scaling():
    assert ccts_icm.ccc_surplus_deficit(1.5, 1.5, 1000) == 0.0
    assert ccts_icm.ccc_surplus_deficit(1.0, 1.5, 0) == 0.0
    assert ccts_icm.ccc_surplus_deficit(1.0, 1.0004, 1) == 0.0  # rounds to 3 dp
    assert ccts_icm.ccc_surplus_deficit(0.0, 0.0006, 1) == 0.001
    assert ccts_icm.ccc_surplus_deficit(1.0, 1.5, 2000) == 2 * ccts_icm.ccc_surplus_deficit(1.0, 1.5, 1000)


def test_ccts_status_flag_drives_coverage():
    assert ccts_icm.is_saf_covered_under_ccts() is ccts_icm.SAF_SECTOR_NOTIFIED


def test_biocarbon_estimate_rounding_zero_and_scaling():
    key = "msw"
    factor = biocarbon_estimator.FEEDSTOCK_TYPES[key]["credit_factor_tco2e_per_tonne"]
    days = biocarbon_estimator.OPERATING_DAYS_PER_YEAR
    assert biocarbon_estimator.estimate_credit_per_year(key, 0) == 0.0
    assert biocarbon_estimator.estimate_credit_per_year(key, 1.2345) == round(1.2345 * days * factor, 1)
    assert biocarbon_estimator.estimate_credit_per_year("", 100) is None
    for k, entry in biocarbon_estimator.FEEDSTOCK_TYPES.items():
        assert entry["credit_factor_tco2e_per_tonne"] > 0 and entry["reference_capacity_tpd"] > 0
        assert biocarbon_estimator.estimate_credit_per_year(k, entry["reference_capacity_tpd"]) == round(
            entry["reference_capacity_tpd"] * days * entry["credit_factor_tco2e_per_tonne"], 1
        )


# ---- astm -------------------------------------------------------------------------------------------


@pytest.mark.parametrize("pathway", astm_pathways.PATHWAYS, ids=lambda p: p["code"])
def test_blend_exactly_at_pathway_max_is_conformant_one_over_is_not(pathway):
    cap = pathway["max_blend_pct"]
    assert astm_pathways.is_conformant(cap, cap, "LAB") is True
    assert astm_pathways.is_conformant(cap, cap + 0.1, "LAB") is False
    assert astm_pathways.is_conformant(cap, 0.0, "LAB") is True


def test_conformance_returns_real_bools_and_needs_nonblank_ref():
    assert astm_pathways.is_conformant(50.0, 10.0, "") is False
    assert astm_pathways.is_conformant(50.0, 10.0, "x") is True
    assert type(astm_pathways.is_conformant(50.0, 10.0, "")) is bool
    assert type(astm_pathways.is_conformant(50.0, 10.0, "x")) is bool


# ---- model properties / seed ----------------------------------------------------------------------------


def test_batch_yield_pct_formula_and_zero_guard():
    from app.models import ProductionBatch

    b = ProductionBatch(feedstock_input_tonnes=10.0, saf_output_liters=10000.0)
    assert b.yield_pct == 80.0
    b.saf_output_liters = 12345.0
    assert b.yield_pct == round(12345.0 * 0.0008 / 10.0 * 100, 1)
    b.feedstock_input_tonnes = 0.0
    assert b.yield_pct == 0.0
    b.feedstock_input_tonnes = -1.0
    assert b.yield_pct == 0.0


def test_blending_actual_pct_formula_and_zero_guard():
    from app.models import BlendingRecord

    r = BlendingRecord(total_jet_fuel_liters=3.0, total_saf_liters=1.0)
    assert r.actual_pct == 33.333
    r.total_jet_fuel_liters = 0.0
    assert r.actual_pct == 0.0
    r.total_jet_fuel_liters = -5.0
    assert r.actual_pct == 0.0


def test_seed_is_idempotent_and_internally_consistent(tmp_path):
    from sqlalchemy import create_engine, func, select
    from sqlalchemy.orm import sessionmaker

    from app.db import Base
    from app.models import (
        AirlineDelivery,
        BlendingRecord,
        CarbonCreditLedger,
        ProductionBatch,
        SAFCertificate,
    )
    from app.seed.mock_data import seed_if_empty

    engine = create_engine(f"sqlite:///{tmp_path / 's.db'}")
    Base.metadata.create_all(bind=engine)
    with sessionmaker(bind=engine)() as db:
        seed_if_empty(db)

        def counts():
            return [
                db.scalar(select(func.count()).select_from(m))
                for m in (ProductionBatch, SAFCertificate, AirlineDelivery, CarbonCreditLedger, BlendingRecord)
            ]

        first = counts()
        seed_if_empty(db)  # second call must be a no-op
        assert counts() == first
        assert first == [36, 36, 36, 36, 3]
        # every ledger entry equals the helper applied to its delivery's certificate
        for entry in db.scalars(select(CarbonCreditLedger)):
            d = entry.delivery
            assert entry.tco2e_saved == corsia.credit_for_delivery(d.volume_liters, d.batch.certificate.corsia_lcef)
            assert d.volume_liters <= d.batch.saf_output_liters
            assert d.delivery_date == d.batch.end_date


# ---- db path configuration (fresh interpreter: app.db binds its engine at import) ----------------------------


def _db_path_in_subprocess(env_value):
    import subprocess
    import sys
    from pathlib import Path

    backend = Path(__file__).resolve().parent.parent
    env = {k: v for k, v in os.environ.items() if k != "SAF_DB_PATH"}
    if env_value is not None:
        env["SAF_DB_PATH"] = env_value
    out = subprocess.run(
        [sys.executable, "-c", "from app.db import DB_PATH, engine; print(DB_PATH); print(engine.url)"],
        cwd=backend, env=env, capture_output=True, text=True, check=True,
    )  # fmt: skip
    return backend, out.stdout.split("\n")[:2]


def test_db_path_comes_from_env_var(tmp_path):
    target = str(tmp_path / "custom.db")
    _, (db_path, url) = _db_path_in_subprocess(target)
    assert db_path == target
    assert url == f"sqlite:///{target}"


def test_db_path_defaults_to_backend_saf_db():
    backend, (db_path, url) = _db_path_in_subprocess(None)
    assert db_path == str(backend / "saf.db")
    assert url == f"sqlite:///{backend / 'saf.db'}"
