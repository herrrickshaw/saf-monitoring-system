def test_dashboard_summary(client):
    r = client.get("/api/dashboard/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["total_saf_liters"] > 0
    assert body["active_contracts"] == 3


def test_feedstock_and_deliveries_seeded(client):
    r = client.get("/api/feedstock")
    assert r.status_code == 200
    assert len(r.json()) == 3

    r = client.get("/api/feedstock/deliveries")
    assert r.status_code == 200
    assert len(r.json()) == 36


def test_production_batches_and_pathways_seeded(client):
    r = client.get("/api/production/pathways")
    assert r.status_code == 200
    assert len(r.json()) == 9

    r = client.get("/api/production/batches")
    assert r.status_code == 200
    assert len(r.json()) == 36


def test_certificates_seeded_and_astm_conformant(client):
    r = client.get("/api/certificates")
    assert r.status_code == 200
    certs = r.json()
    assert len(certs) == 36
    assert all(c["astm_conformant"] for c in certs)


def test_carbon_credit_ledger_seeded(client):
    r = client.get("/api/carbon-credits/ledger")
    assert r.status_code == 200
    assert len(r.json()) == 36


def test_airlines_seeded(client):
    r = client.get("/api/airlines")
    assert r.status_code == 200
    names = {a["airline_name"] for a in r.json()}
    assert names == {"Lufthansa Group", "British Airways", "Air France-KLM"}


def test_blending_compliance_flags(client):
    r = client.get("/api/compliance/blending")
    assert r.status_code == 200
    by_airport = {b["airport"]: b for b in r.json()}
    assert by_airport["EDDF"]["compliant"] is True
    assert by_airport["EGLL"]["compliant"] is False


def test_airline_report_download(client):
    offtake_id = client.get("/api/airlines").json()[0]["id"]
    r = client.get(
        f"/api/airlines/{offtake_id}/report",
        params={"start": "2025-01-01", "end": "2026-12-31", "fmt": "pdf"},
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert len(r.content) > 500


def test_ccts_icm_status(client):
    r = client.get("/api/compliance/ccts-icm/status")
    assert r.status_code == 200
    body = r.json()
    assert body["saf_sector_notified"] is False
    assert len(body["compliance_mechanism_sectors"]) == 9


def test_ccts_icm_estimate(client):
    r = client.post(
        "/api/compliance/ccts-icm/estimate",
        json={"actual_intensity_tco2e_per_unit": 1.0, "target_intensity_tco2e_per_unit": 1.5, "output_units": 1000},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["surplus_deficit_tco2e"] == 500.0
    assert body["is_surplus"] is True


def test_bio_carbon_table(client):
    r = client.get("/api/compliance/bio-carbon/table")
    assert r.status_code == 200
    body = r.json()
    assert len(body["rows"]) == 10
    assert all(row["reference_credit_per_year"] > 0 for row in body["rows"])


def test_bio_carbon_estimate(client):
    r = client.post("/api/compliance/bio-carbon/estimate", json={"feedstock_key": "agri_waste", "capacity_tpd": 200})
    assert r.status_code == 200
    assert r.json()["credit_per_year_tco2e"] == 21000.0


def test_bio_carbon_estimate_unknown_feedstock(client):
    r = client.post("/api/compliance/bio-carbon/estimate", json={"feedstock_key": "unobtainium", "capacity_tpd": 100})
    assert r.status_code == 400
