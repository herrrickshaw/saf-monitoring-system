"""Certificate generation through the API: a crop feedstock created without an
explicit ILUC value must not be certified CORSIA-eligible on its core value alone.

Runs against its own temporary SQLite DB (dependency override) so the rows it
creates do not change the seeded counts the smoke tests assert on."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    from app.db import Base, get_db
    from app.main import app
    from app.seed.mock_data import seed_if_empty

    engine = create_engine(f"sqlite:///{tmp_path_factory.mktemp('certs') / 't.db'}",
                           connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    with Session() as db:
        seed_if_empty(db)

    def _db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _db
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)


def _make_batch(client, *, key, category="CROP", iluc=None, code):
    fs = {"name": f"test {key}", "category": category, "supplier": "Synthetic Co",
          "corsia_feedstock_key": key}
    if iluc is not None:
        fs["corsia_iluc_value"] = iluc
    fid = client.post("/api/feedstock", json=fs).json()["id"]
    did = client.post("/api/feedstock/deliveries", json={
        "feedstock_id": fid, "arrival_date": "2026-01-05", "quantity_tonnes": 100.0,
        "certificate_number": f"SYN-{code}", "origin_country": "US"}).json()["id"]
    atj = next(p for p in client.get("/api/production/pathways").json() if p["code"] == "ATJ-SPK")
    bid = client.post("/api/production/batches", json={
        "batch_code": code, "start_date": "2026-01-06", "end_date": "2026-01-07",
        "astm_pathway_id": atj["id"], "feedstock_delivery_id": did,
        "feedstock_input_tonnes": 100.0, "saf_output_liters": 30000.0,
        "blend_ratio_pct": 50.0, "lab_certification_ref": "LAB-1"}).json()["id"]
    return client.post(f"/api/certificates/generate/{bid}")


def test_corn_ethanol_to_jet_certificate_counts_default_iluc(client):
    r = _make_batch(client, key="corn_grain_ethanol", code="T-CORN-ETJ")
    assert r.status_code == 200, r.text
    cert = r.json()
    assert cert["corsia_core_lca_value"] == 65.7
    assert cert["corsia_lcef"] == 100.6           # 65.7 core + 34.9 Global ILUC
    assert cert["corsia_eligible"] is False


def test_explicit_regional_iluc_overrides_default(client):
    # USA ILUC for corn isobutanol is 22.1 -> 55.8 + 22.1 = 77.9 -> 12.47 % cut
    r = _make_batch(client, key="corn_grain_isobutanol", iluc=22.1, code="T-CORN-IBA-US")
    cert = r.json()
    assert cert["corsia_lcef"] == 77.9
    assert cert["corsia_reduction_pct"] == 12.47
    assert cert["corsia_eligible"] is True


def test_residue_feedstock_keeps_zero_iluc(client):
    r = _make_batch(client, key="agricultural_residues_isobutanol", category="IX-A", code="T-RES")
    cert = r.json()
    assert cert["corsia_lcef"] == 29.3 and cert["corsia_eligible"] is True


def test_crop_without_a_verified_default_iluc_is_refused(client):
    # rapeseed (HEFA) has a non-zero ICAO ILUC but no value carried in this repo:
    # the certificate must not silently use ILUC = 0.
    fs = {"name": "test rapeseed", "category": "CROP", "supplier": "Synthetic Co",
          "corsia_feedstock_key": "rapeseed_canola_oilseed"}
    fid = client.post("/api/feedstock", json=fs).json()["id"]
    did = client.post("/api/feedstock/deliveries", json={
        "feedstock_id": fid, "arrival_date": "2026-01-05", "quantity_tonnes": 10.0,
        "certificate_number": "SYN-RAPE", "origin_country": "DE"}).json()["id"]
    hefa = next(p for p in client.get("/api/production/pathways").json() if p["code"] == "HEFA-SPK")
    bid = client.post("/api/production/batches", json={
        "batch_code": "T-RAPE", "start_date": "2026-01-06", "end_date": "2026-01-07",
        "astm_pathway_id": hefa["id"], "feedstock_delivery_id": did,
        "feedstock_input_tonnes": 10.0, "saf_output_liters": 3000.0,
        "blend_ratio_pct": 50.0, "lab_certification_ref": "LAB-1"}).json()["id"]
    r = client.post(f"/api/certificates/generate/{bid}")
    assert r.status_code == 400 and "ILUC" in r.text


def test_generate_certificate_404_and_duplicate(client):
    assert client.post("/api/certificates/generate/999999").status_code == 404
    r = _make_batch(client, key="agricultural_residues_isobutanol", category="IX-A", code="T-DUP")
    bid = r.json()["production_batch_id"]
    assert client.post(f"/api/certificates/generate/{bid}").status_code == 400
