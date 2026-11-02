import pytest
from app.calculations.certification import MissingCorsiaDefault, compute_certificate_metrics

BASE = dict(
    eec=10.0, ep=5.0, etd=2.0, feedstock_category="WASTE", corsia_feedstock_key="used_cooking_oil",
    corsia_iluc_value=0.0, pathway_code="HEFA-SPK", pathway_max_blend_pct=50.0,
    blend_ratio_pct=30.0, lab_certification_ref="LAB-1",
)


def test_hefa_uco_metrics():
    m = compute_certificate_metrics(**BASE)
    assert m.ghg_intensity == 17.0
    assert m.fossil_comparator == 94.0
    assert m.corsia_core_lca_value == 13.9
    assert m.corsia_lcef == 13.9
    assert m.corsia_reduction_pct == 84.38
    assert m.corsia_eligible and m.eligible_feedstock and m.astm_conformant


def test_crop_feedstock_not_eligible():
    assert compute_certificate_metrics(**{**BASE, "feedstock_category": "CROP"}).eligible_feedstock is False


def test_missing_default_raises():
    with pytest.raises(MissingCorsiaDefault) as exc:
        compute_certificate_metrics(**{**BASE, "corsia_feedstock_key": "nope"})
    assert "No CORSIA default Core LCA value for pathway 'HEFA-SPK' / feedstock key 'nope'" in str(exc.value)


def test_as_dict_keys_match_model_columns():
    from app.models import SAFCertificate

    cols = {c.name for c in SAFCertificate.__table__.columns}
    assert set(compute_certificate_metrics(**BASE).as_dict()) <= cols
