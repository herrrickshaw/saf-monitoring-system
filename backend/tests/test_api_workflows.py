"""Write-path and error-path tests for the airline, carbon-credit, compliance,
dashboard, feedstock and production routers.

Runs against its own temporary SQLite DB (dependency override), like
test_certificates.py, so the rows created here never change the seeded counts
the smoke tests assert on. Expected numbers are derived from the code's own
helpers (calculations.*), not from regulatory facts recalled from memory."""

import os
import tempfile

# app.db binds its engine at first import. Make sure an import that happens
# before conftest's `client` fixture never falls back to the repo-local saf.db.
os.environ.setdefault("SAF_DB_PATH", os.path.join(tempfile.mkdtemp(prefix="saf-test-"), "default.db"))

import io
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.calculations.corsia import CORSIA_MIN_REDUCTION_PCT, credit_for_delivery
from app.calculations.mandate_schedule import mandate_pct_for_year
from app.reports.airline_report import HEADERS


def _session_factory(tmp_path, seed):
    from app.db import Base
    from app.seed.mock_data import seed_if_empty

    engine = create_engine(f"sqlite:///{tmp_path / 't.db'}", connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    if seed:
        with Session() as db:
            seed_if_empty(db)
    return Session


def _install(Session):
    from app.db import get_db
    from app.main import app

    def _db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _db
    return TestClient(app), get_db, app


@pytest.fixture(scope="module")
def seeded_session(tmp_path_factory):
    return _session_factory(tmp_path_factory.mktemp("wf"), seed=True)


@pytest.fixture
def client(seeded_session):
    # re-installed per test: empty_client's teardown removes the override, so a
    # module-scoped override would silently fall back to the real/default DB.
    c, get_db, app = _install(seeded_session)
    yield c
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def empty_client(tmp_path):
    c, get_db, app = _install(_session_factory(tmp_path, seed=False))
    yield c
    app.dependency_overrides.pop(get_db, None)


_counter = {"n": 0}


def _uid():
    _counter["n"] += 1
    return _counter["n"]


def make_batch(client, *, key="used_cooking_oil", pathway="HEFA-SPK", iluc=0.0, category="IX-B",
               blend=40.0, volume=30000.0, lab="LAB-X", ep=0.0):  # fmt: skip
    n = _uid()
    fid = client.post("/api/feedstock", json={"name": f"fs{n}", "category": category, "supplier": "S",
                      "default_eec": 1.0, "default_ep": 10.0, "default_etd": 2.0,
                      "corsia_feedstock_key": key, "corsia_iluc_value": iluc}).json()["id"]  # fmt: skip
    did = client.post("/api/feedstock/deliveries", json={"feedstock_id": fid, "arrival_date": "2026-01-05",
                      "quantity_tonnes": 100.0, "certificate_number": f"C{n}",
                      "origin_country": "NL"}).json()["id"]  # fmt: skip
    pid = next(p for p in client.get("/api/production/pathways").json() if p["code"] == pathway)["id"]
    r = client.post("/api/production/batches", json={"batch_code": f"WF-{n}", "start_date": "2026-01-06",
                    "end_date": "2026-01-07", "astm_pathway_id": pid, "feedstock_delivery_id": did,
                    "feedstock_input_tonnes": 100.0, "saf_output_liters": volume,
                    "blend_ratio_pct": blend, "lab_certification_ref": lab,
                    "process_emissions_ep": ep})  # fmt: skip
    assert r.status_code == 200, r.text
    return r.json()["id"]


def make_offtake(client, name="WF Air", airport="EDDF"):
    r = client.post("/api/airlines", json={"airline_name": name, "contract_volume_liters": 1e6,
                    "delivery_airport": airport, "contract_start": "2026-01-01",
                    "contract_end": "2030-01-01"})  # fmt: skip
    assert r.status_code == 200, r.text
    return r.json()["id"]


def make_delivery(client, offtake_id, batch_id, day="2026-03-15", volume=1000.0):
    r = client.post("/api/airlines/deliveries", json={"airline_offtake_id": offtake_id,
                    "production_batch_id": batch_id, "volume_liters": volume, "delivery_date": day})  # fmt: skip
    assert r.status_code == 200, r.text
    return r.json()["id"]


# ---- feedstock / production -----------------------------------------------------


def test_feedstock_create_roundtrip_defaults(client):
    r = client.post("/api/feedstock", json={"name": "Bare", "category": "IX-A", "supplier": "X"})
    body = r.json()
    assert r.status_code == 200 and body["id"] > 0
    assert (body["default_eec"], body["default_ep"], body["default_etd"]) == (0.0, 0.0, 0.0)
    assert (body["corsia_feedstock_key"], body["corsia_iluc_value"]) == ("", 0.0)
    assert any(f["id"] == body["id"] for f in client.get("/api/feedstock").json())


def test_feedstock_delivery_unknown_feedstock_is_404(client):
    r = client.post("/api/feedstock/deliveries", json={"feedstock_id": 99999, "arrival_date": "2026-01-01",
                    "quantity_tonnes": 1.0, "certificate_number": "c", "origin_country": "NL"})  # fmt: skip
    assert r.status_code == 404 and r.json()["detail"] == "Feedstock not found"


def test_feedstock_deliveries_roundtrip(client):
    n = _uid()
    fid = client.post("/api/feedstock", json={"name": f"d{n}", "category": "IX-B", "supplier": "S"}).json()["id"]
    r = client.post("/api/feedstock/deliveries", json={"feedstock_id": fid, "arrival_date": "2026-02-03",
                    "quantity_tonnes": 12.5, "certificate_number": f"CN{n}", "origin_country": "PL"})  # fmt: skip
    assert r.status_code == 200
    row = next(d for d in client.get("/api/feedstock/deliveries").json() if d["id"] == r.json()["id"])
    assert (row["feedstock_id"], row["arrival_date"], row["quantity_tonnes"]) == (fid, "2026-02-03", 12.5)
    assert (row["certificate_number"], row["origin_country"]) == (f"CN{n}", "PL")


def test_certificate_without_a_core_lca_default_is_refused(client):
    batch = make_batch(client, key="not_in_the_table")
    r = client.post(f"/api/certificates/generate/{batch}")
    assert r.status_code == 400
    assert "No CORSIA default Core LCA value for pathway 'HEFA-SPK'" in r.json()["detail"]
    assert "not_in_the_table" in r.json()["detail"]
    assert client.get("/api/certificates").json() is not None


def test_production_batch_404s_and_yield(client):
    n = _uid()
    fid = client.post("/api/feedstock", json={"name": f"y{n}", "category": "IX-B", "supplier": "S"}).json()["id"]
    did = client.post("/api/feedstock/deliveries", json={"feedstock_id": fid, "arrival_date": "2026-01-05",
                      "quantity_tonnes": 10.0, "certificate_number": "c", "origin_country": "NL"}).json()["id"]  # fmt: skip
    base = {"batch_code": f"Y-{n}", "start_date": "2026-01-01", "end_date": "2026-01-02",
            "feedstock_input_tonnes": 10.0, "saf_output_liters": 10000.0, "blend_ratio_pct": 30.0}  # fmt: skip
    r = client.post("/api/production/batches", json={**base, "astm_pathway_id": 99999, "feedstock_delivery_id": did})
    assert r.status_code == 404 and r.json()["detail"] == "ASTM pathway not found"
    pid = client.get("/api/production/pathways").json()[0]["id"]
    r = client.post("/api/production/batches", json={**base, "astm_pathway_id": pid, "feedstock_delivery_id": 99999})
    assert r.status_code == 404 and r.json()["detail"] == "Feedstock delivery not found"
    r = client.post("/api/production/batches", json={**base, "astm_pathway_id": pid, "feedstock_delivery_id": did})
    assert r.status_code == 200
    # 10000 L * 0.0008 t/L = 8 t out of 10 t in -> 80.0 %
    assert r.json()["yield_pct"] == 80.0
    assert r.json()["lab_certification_ref"] == "" and r.json()["process_emissions_ep"] == 0.0


def test_production_batch_zero_input_yield_is_zero_not_a_crash(client):
    n = _uid()
    fid = client.post("/api/feedstock", json={"name": f"z{n}", "category": "IX-B", "supplier": "S"}).json()["id"]
    did = client.post("/api/feedstock/deliveries", json={"feedstock_id": fid, "arrival_date": "2026-01-05",
                      "quantity_tonnes": 1.0, "certificate_number": "c", "origin_country": "NL"}).json()["id"]  # fmt: skip
    pid = client.get("/api/production/pathways").json()[0]["id"]
    r = client.post("/api/production/batches", json={"batch_code": f"Z-{n}", "start_date": "2026-01-01",
                    "end_date": "2026-01-02", "astm_pathway_id": pid, "feedstock_delivery_id": did,
                    "feedstock_input_tonnes": 0.0, "saf_output_liters": 5.0, "blend_ratio_pct": 1.0})  # fmt: skip
    assert r.status_code == 200 and r.json()["yield_pct"] == 0.0


def test_duplicate_batch_code_is_rejected(client):
    bid = make_batch(client)
    batch = next(b for b in client.get("/api/production/batches").json() if b["id"] == bid)
    body = {k: v for k, v in batch.items() if k not in {"id", "yield_pct"}}
    with pytest.raises(IntegrityError):  # unique batch_code; the app has no handler, so it propagates
        client.post("/api/production/batches", json=body)


# ---- airlines ------------------------------------------------------------------------


def test_offtake_create_and_list(client):
    oid = make_offtake(client, name="Roundtrip Air", airport="EHAM")
    row = next(o for o in client.get("/api/airlines").json() if o["id"] == oid)
    assert row["airline_name"] == "Roundtrip Air" and row["delivery_airport"] == "EHAM"
    assert (row["contract_start"], row["contract_end"]) == ("2026-01-01", "2030-01-01")


def test_delivery_requires_existing_offtake_and_batch(client):
    bid = make_batch(client)
    oid = make_offtake(client)
    body = {"airline_offtake_id": oid, "production_batch_id": bid, "volume_liters": 5.0,
            "delivery_date": "2026-02-02"}  # fmt: skip
    r = client.post("/api/airlines/deliveries", json={**body, "airline_offtake_id": 99999})
    assert r.status_code == 404 and r.json()["detail"] == "Airline offtake not found"
    r = client.post("/api/airlines/deliveries", json={**body, "production_batch_id": 99999})
    assert r.status_code == 404 and r.json()["detail"] == "Production batch not found"
    r = client.post("/api/airlines/deliveries", json=body)
    assert r.status_code == 200
    listed = client.get("/api/airlines/deliveries").json()
    assert any(d["id"] == r.json()["id"] and d["volume_liters"] == 5.0 for d in listed)


def test_report_unknown_offtake_and_bad_params(client):
    q = {"start": "2026-01-01", "end": "2026-12-31"}
    r = client.get("/api/airlines/99999/report", params=q)
    assert r.status_code == 404 and r.json()["detail"] == "Airline offtake not found"
    oid = make_offtake(client)
    assert client.get(f"/api/airlines/{oid}/report", params={**q, "fmt": "csv"}).status_code == 422
    assert client.get(f"/api/airlines/{oid}/report", params={"end": "2026-12-31"}).status_code == 422
    assert client.get(f"/api/airlines/{oid}/report", params={"start": "2026-01-01"}).status_code == 422
    assert client.get(f"/api/airlines/{oid}/report", params={**q, "start": "nope"}).status_code == 422


def _sheet_rows(content):
    ws = load_workbook(io.BytesIO(content)).active
    rows = []
    for r in ws.iter_rows(values_only=True):
        r = list(r)
        while r and r[-1] is None:  # openpyxl pads rows to the sheet's widest row
            r.pop()
        rows.append(r)
    return ws.title, rows


def test_excel_report_period_is_inclusive_and_rows_formatted(client):
    cert_batch = make_batch(client, blend=40.0)
    assert client.post(f"/api/certificates/generate/{cert_batch}").status_code == 200
    bare_batch = make_batch(client)  # no certificate -> n/a columns
    oid = make_offtake(client, name="Excel Air", airport="LEMD")
    make_delivery(client, oid, cert_batch, "2026-02-28", 111.0)
    d_start = make_delivery(client, oid, cert_batch, "2026-03-01", 1000.0)
    make_delivery(client, oid, bare_batch, "2026-03-31", 2500.0)
    make_delivery(client, oid, cert_batch, "2026-04-01", 333.0)
    assert client.post(f"/api/carbon-credits/generate/{d_start}").status_code == 200

    r = client.get(f"/api/airlines/{oid}/report", params={"start": "2026-03-01", "end": "2026-03-31", "fmt": "excel"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert r.headers["content-disposition"] == (
        'attachment; filename="Excel Air_SAF_report_2026-03-01_2026-03-31.xlsx"'
    )
    title, rows = _sheet_rows(r.content)
    assert title == "SAF Supply Report"
    assert rows[0] == ["SAF Supply Report — Excel Air"]
    assert rows[1][:2] == ["Airport: LEMD", "Period: 2026-03-01 to 2026-03-31"]
    assert rows[2] == []
    assert rows[3] == HEADERS
    data = rows[4:]
    assert [row[0] for row in data] == ["2026-03-01", "2026-03-31"]  # start and end inclusive, others out
    full, bare = data
    assert full[5] == "1,000 L" and full[4] == "40.0%"
    assert full[6] != "n/a" and full[6].replace(".", "").isdigit()
    assert full[7].endswith("%") and full[8].endswith("%")
    assert full[9] != "n/a"  # ledger entry exists for this delivery
    assert bare[5] == "2,500 L"
    assert bare[6:] == ["n/a", "n/a", "n/a", "n/a"]


def test_pdf_report_headers_and_totals_period_filter(client):
    batch = make_batch(client)
    oid = make_offtake(client, name="Pdf Air")
    make_delivery(client, oid, batch, "2026-05-10", 1234.0)
    r = client.get(f"/api/airlines/{oid}/report", params={"start": "2026-05-01", "end": "2026-05-31"})
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    assert r.headers["content-disposition"] == 'attachment; filename="Pdf Air_SAF_report_2026-05-01_2026-05-31.pdf"'
    assert r.content.startswith(b"%PDF")
    # an empty period still renders a valid document
    r2 = client.get(f"/api/airlines/{oid}/report", params={"start": "2020-01-01", "end": "2020-01-31", "fmt": "pdf"})
    assert r2.status_code == 200 and r2.content.startswith(b"%PDF")


def test_build_pdf_total_lines_use_filtered_deliveries(client, monkeypatch):
    """The PDF is compressed, so assert on the story the builder hands to reportlab."""
    import app.reports.airline_report as rep

    captured = {}
    real_build = rep.SimpleDocTemplate.build

    def spy(self, story, *a, **k):
        captured["texts"] = [getattr(p, "text", "") for p in story]
        return real_build(self, story, *a, **k)

    monkeypatch.setattr(rep.SimpleDocTemplate, "build", spy)
    batch = make_batch(client)
    oid = make_offtake(client, name="Totals Air", airport="LIRF")
    make_delivery(client, oid, batch, "2026-06-10", 1000.0)
    make_delivery(client, oid, batch, "2026-06-20", 2000.0)
    make_delivery(client, oid, batch, "2026-07-20", 4000.0)  # outside the period
    client.get(f"/api/airlines/{oid}/report", params={"start": "2026-06-01", "end": "2026-06-30"})
    texts = captured["texts"]
    assert "Total volume delivered: 3,000 L" in texts
    assert "Total CORSIA emissions reduction credited: 0.00 tCO2e" in texts
    assert "SAF Supply Report — Totals Air" in texts
    assert "Airport: LIRF | Period: 2026-06-01 to 2026-06-30" in texts


def test_pdf_total_credit_sums_ledger_entries(client, monkeypatch):
    import app.reports.airline_report as rep

    captured = {}
    real_build = rep.SimpleDocTemplate.build
    monkeypatch.setattr(
        rep.SimpleDocTemplate, "build",
        lambda self, story, *a, **k: (captured.update(t=[getattr(p, "text", "") for p in story]),
                                      real_build(self, story, *a, **k))[1],
    )  # fmt: skip
    batch = make_batch(client)
    assert client.post(f"/api/certificates/generate/{batch}").status_code == 200
    oid = make_offtake(client, name="Credit Air")
    d1 = make_delivery(client, oid, batch, "2026-06-10", 10000.0)
    d2 = make_delivery(client, oid, batch, "2026-06-11", 20000.0)
    e1 = client.post(f"/api/carbon-credits/generate/{d1}").json()["tco2e_saved"]
    e2 = client.post(f"/api/carbon-credits/generate/{d2}").json()["tco2e_saved"]
    client.get(f"/api/airlines/{oid}/report", params={"start": "2026-06-01", "end": "2026-06-30"})
    assert f"Total CORSIA emissions reduction credited: {e1 + e2:,.2f} tCO2e" in captured["t"]


# ---- carbon credits -----------------------------------------------------------------------


def test_ledger_generate_errors(client):
    r = client.post("/api/carbon-credits/generate/99999")
    assert r.status_code == 404 and r.json()["detail"] == "Airline delivery not found"

    batch = make_batch(client)
    oid = make_offtake(client)
    did = make_delivery(client, oid, batch)
    r = client.post(f"/api/carbon-credits/generate/{did}")
    assert r.status_code == 400 and "no SAF certificate" in r.json()["detail"]

    # a huge ILUC pushes L_CEF above the baseline -> certificate exists but is not eligible
    bad = make_batch(client, iluc=500.0)
    cert = client.post(f"/api/certificates/generate/{bad}").json()
    assert cert["corsia_eligible"] is False
    did2 = make_delivery(client, oid, bad)
    r = client.post(f"/api/carbon-credits/generate/{did2}")
    assert r.status_code == 400
    detail = r.json()["detail"]
    assert f"{CORSIA_MIN_REDUCTION_PCT}%" in detail and f"actual: {cert['corsia_reduction_pct']}%" in detail
    assert not any(e["airline_delivery_id"] == did2 for e in client.get("/api/carbon-credits/ledger").json())


def test_ledger_generate_success_duplicate_and_report(client):
    batch = make_batch(client)
    cert = client.post(f"/api/certificates/generate/{batch}").json()
    assert cert["corsia_eligible"] is True
    oid = make_offtake(client)
    did = make_delivery(client, oid, batch, volume=12345.0)
    r = client.post(f"/api/carbon-credits/generate/{did}")
    assert r.status_code == 200
    entry = r.json()
    assert entry["airline_delivery_id"] == did and entry["status"] == "calculated"
    assert entry["tco2e_saved"] == credit_for_delivery(12345.0, cert["corsia_lcef"])
    assert entry["tco2e_saved"] > 0

    again = client.post(f"/api/carbon-credits/generate/{did}")
    assert again.status_code == 400 and "already generated" in again.json()["detail"]
    assert sum(1 for e in client.get("/api/carbon-credits/ledger").json() if e["airline_delivery_id"] == did) == 1

    rep = client.post(f"/api/carbon-credits/{entry['id']}/report")
    assert rep.status_code == 200 and rep.json()["status"] == "reported"
    assert rep.json()["tco2e_saved"] == entry["tco2e_saved"]
    listed = next(e for e in client.get("/api/carbon-credits/ledger").json() if e["id"] == entry["id"])
    assert listed["status"] == "reported"


def test_mark_reported_unknown_entry_is_404(client):
    r = client.post("/api/carbon-credits/99999/report")
    assert r.status_code == 404 and r.json()["detail"] == "Ledger entry not found"


# ---- compliance ---------------------------------------------------------------------------------


def _blend(client, airport, year, fuel, saf):
    r = client.post("/api/compliance/blending", json={"airport": airport, "year": year,
                    "total_jet_fuel_liters": fuel, "total_saf_liters": saf})  # fmt: skip
    assert r.status_code == 200, r.text
    return r.json()


def test_blending_record_math_and_boundary(client):
    year = 2030
    mandate = mandate_pct_for_year(year)
    fuel = 1_000_000.0
    exact = _blend(client, "BDRY1", year, fuel, fuel * mandate / 100)
    assert exact["actual_pct"] == mandate and exact["mandate_pct"] == mandate
    assert exact["compliant"] is True  # meeting the mandate exactly is compliant
    shortfall = fuel * 0.0006 / 100  # 0.0006 percentage points: survives the 3-decimal rounding
    short = _blend(client, "BDRY2", year, fuel, fuel * mandate / 100 - shortfall)
    assert short["compliant"] is False
    assert short["actual_pct"] < mandate
    assert short["actual_pct"] == round((fuel * mandate / 100 - shortfall) / fuel * 100, 3)


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="routers/compliance.py _to_out compares the 3-decimal ROUNDED actual_pct (models.py "
    "BlendingRecord.actual_pct) to the mandate, so a real shortfall below 0.0005 percentage "
    "points (here 1 L in 1,000,000 L = 5.9999% vs 6%) is reported compliant=True",
)
def test_one_litre_short_of_the_mandate_is_not_compliant(client):
    mandate = mandate_pct_for_year(2030)
    fuel = 1_000_000.0
    rec = _blend(client, "BDRY3", 2030, fuel, fuel * mandate / 100 - 1)
    assert rec["compliant"] is False


def test_blending_zero_fuel_has_zero_actual_and_is_noncompliant_when_mandated(client):
    rec = _blend(client, "ZERO1", 2030, 0.0, 0.0)
    assert rec["actual_pct"] == 0.0 and rec["compliant"] is False
    pre = _blend(client, "ZERO2", 2020, 0.0, 0.0)  # before the schedule: mandate 0 -> 0 >= 0
    assert pre["mandate_pct"] == 0.0 and pre["compliant"] is True


def test_blending_filters_by_airport_and_year(client):
    _blend(client, "FLT1", 2041, 100.0, 50.0)
    _blend(client, "FLT1", 2042, 100.0, 50.0)
    _blend(client, "FLT2", 2041, 100.0, 50.0)
    both = client.get("/api/compliance/blending", params={"airport": "FLT1", "year": 2041}).json()
    assert [(r["airport"], r["year"]) for r in both] == [("FLT1", 2041)]
    by_airport = client.get("/api/compliance/blending", params={"airport": "FLT1"}).json()
    assert sorted(r["year"] for r in by_airport) == [2041, 2042]
    by_year = client.get("/api/compliance/blending", params={"year": 2041}).json()
    assert sorted(r["airport"] for r in by_year) == ["FLT1", "FLT2"]
    assert client.get("/api/compliance/blending", params={"airport": "NOPE"}).json() == []
    assert len(client.get("/api/compliance/blending").json()) >= 3


# ---- dashboard ---------------------------------------------------------------------------------------


def test_dashboard_empty_database(empty_client):
    body = empty_client.get("/api/dashboard/summary").json()
    assert body["total_saf_liters"] == 0
    assert body["total_tco2e_credited"] == 0
    assert body["active_contracts"] == 0
    assert body["current_year_blending_pct"] == 0.0  # no records -> 0, not a crash
    assert body["current_year_mandate_pct"] == mandate_pct_for_year(date.today().year)


def test_dashboard_active_contracts_boundary_and_average(empty_client):
    c = empty_client
    today = date.today()

    def offtake(end):
        return c.post("/api/airlines", json={"airline_name": "A", "contract_volume_liters": 1.0,
                      "delivery_airport": "X", "contract_start": "2020-01-01",
                      "contract_end": end.isoformat()})  # fmt: skip

    offtake(today)  # ends today -> still active
    offtake(today - timedelta(days=1))  # ended yesterday -> not active
    offtake(today + timedelta(days=1))
    _blend(c, "A1", today.year, 100.0, 10.0)
    _blend(c, "A2", today.year, 100.0, 20.0)
    _blend(c, "A3", today.year - 1, 100.0, 90.0)  # other year ignored
    body = c.get("/api/dashboard/summary").json()
    assert body["active_contracts"] == 2
    assert body["current_year_blending_pct"] == 15.0
    assert body["current_year_mandate_pct"] == mandate_pct_for_year(today.year)


def test_dashboard_sums_batches_and_credits(client):
    before = client.get("/api/dashboard/summary").json()
    batch = make_batch(client, volume=50000.0)
    cert = client.post(f"/api/certificates/generate/{batch}").json()
    oid = make_offtake(client)
    did = make_delivery(client, oid, batch, volume=20000.0)
    entry = client.post(f"/api/carbon-credits/generate/{did}").json()
    after = client.get("/api/dashboard/summary").json()
    assert after["total_saf_liters"] == pytest.approx(before["total_saf_liters"] + 50000.0)
    assert after["total_tco2e_credited"] == pytest.approx(before["total_tco2e_credited"] + entry["tco2e_saved"])
    assert after["active_contracts"] == before["active_contracts"] + 1
    assert cert["corsia_eligible"] is True


# ---- certificates / compliance estimate (field-level checks) ---------------------------------------------


def test_certificate_uses_batch_process_emissions_over_feedstock_default(client):
    from app.calculations.ghg import FOSSIL_COMPARATOR_GCO2_PER_MJ, ghg_savings_pct

    bid = make_batch(client, ep=20.0)  # feedstock default_ep is 10.0 in make_batch
    cert = client.post(f"/api/certificates/generate/{bid}").json()
    assert cert["ghg_intensity"] == 1.0 + 0.0 + 20.0 + 2.0  # eec + el + batch ep + etd
    assert cert["ghg_savings_pct"] == ghg_savings_pct(23.0)
    assert cert["fossil_comparator"] == FOSSIL_COMPARATOR_GCO2_PER_MJ
    default = client.post(f"/api/certificates/generate/{make_batch(client)}").json()
    assert default["ghg_intensity"] == 1.0 + 10.0 + 2.0  # unset batch ep falls back to the feedstock default


def test_certificate_flags_follow_feedstock_category_and_blend(client):
    ok = client.post(f"/api/certificates/generate/{make_batch(client, category='IX-B')}").json()
    assert ok["eligible_feedstock"] is True and ok["astm_conformant"] is True
    crop = client.post(
        f"/api/certificates/generate/{make_batch(client, key='corn_grain_ethanol', pathway='ATJ-SPK', category='CROP', iluc=5.0)}"
    ).json()
    assert crop["eligible_feedstock"] is False
    over = client.post(f"/api/certificates/generate/{make_batch(client, blend=99.0)}").json()
    assert over["astm_conformant"] is False  # blend above the pathway maximum
    nolab = client.post(f"/api/certificates/generate/{make_batch(client, lab='')}").json()
    assert nolab["astm_conformant"] is False  # no lab certification reference recorded


def test_ccts_estimate_zero_difference_is_a_surplus_of_zero(client):
    r = client.post("/api/compliance/ccts-icm/estimate", json={"actual_intensity_tco2e_per_unit": 1.5,
                    "target_intensity_tco2e_per_unit": 1.5, "output_units": 1000.0})  # fmt: skip
    body = r.json()
    assert body["surplus_deficit_tco2e"] == 0.0 and body["ccc_equivalent"] == 0.0
    assert body["is_surplus"] is True
    deficit = client.post("/api/compliance/ccts-icm/estimate", json={"actual_intensity_tco2e_per_unit": 2.0,
                          "target_intensity_tco2e_per_unit": 1.0, "output_units": 0.0005}).json()  # fmt: skip
    assert deficit["surplus_deficit_tco2e"] == -0.001  # rounded to 3 dp
    assert deficit["is_surplus"] is False and deficit["ccc_equivalent"] == 0.001
