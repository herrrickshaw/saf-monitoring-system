from app.calculations.astm_pathways import PATHWAYS, is_conformant


def test_conformant_when_within_max_blend_and_certified():
    assert is_conformant(pathway_max_blend_pct=50.0, blend_ratio_pct=40.0, lab_certification_ref="LAB-1") is True


def test_not_conformant_when_blend_exceeds_pathway_max():
    assert is_conformant(pathway_max_blend_pct=50.0, blend_ratio_pct=60.0, lab_certification_ref="LAB-1") is False


def test_not_conformant_without_lab_certification():
    assert is_conformant(pathway_max_blend_pct=50.0, blend_ratio_pct=40.0, lab_certification_ref="") is False


def test_each_d7566_annex_appears_once_with_its_own_pathway():
    annexes = [p["annex"] for p in PATHWAYS if p["annex"].startswith("Annex A")]
    assert len(annexes) == len(set(annexes))
    by_annex = {p["annex"]: p for p in PATHWAYS}
    assert by_annex["Annex A3"]["max_blend_pct"] == 10.0          # SIP from fermented sugars
    assert by_annex["Annex A8"]["code"] == "ATJ-SKA"              # added July 2023
    assert by_annex["Annex A8"]["max_blend_pct"] == 50.0
    assert not any("HFS-SIP" == p["code"] for p in PATHWAYS)      # same process as Annex A3


def test_co_processing_is_not_labelled_a_d7566_annex():
    co = [p for p in PATHWAYS if p["code"].startswith("Co-processed")]
    assert co and all("D1655" in p["annex"] for p in co)
