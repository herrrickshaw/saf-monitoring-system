from app.calculations.astm_pathways import is_conformant


def test_conformant_when_within_max_blend_and_certified():
    assert is_conformant(pathway_max_blend_pct=50.0, blend_ratio_pct=40.0, lab_certification_ref="LAB-1") is True


def test_not_conformant_when_blend_exceeds_pathway_max():
    assert is_conformant(pathway_max_blend_pct=50.0, blend_ratio_pct=60.0, lab_certification_ref="LAB-1") is False


def test_not_conformant_without_lab_certification():
    assert is_conformant(pathway_max_blend_pct=50.0, blend_ratio_pct=40.0, lab_certification_ref="") is False
