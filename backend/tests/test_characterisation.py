"""Characterisation test: seeded API output must match a snapshot captured from
the pre-refactor code (tests/golden/api_snapshot.json). Timestamps are dropped."""
import io
import json
from pathlib import Path

from openpyxl import load_workbook

GOLDEN = Path(__file__).parent / "golden" / "api_snapshot.json"
VOLATILE = {"issued_date", "calculated_date"}


def _strip(obj):
    if isinstance(obj, list):
        return [_strip(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _strip(v) for k, v in obj.items() if k not in VOLATILE}
    return obj


def snapshot(client) -> dict:
    out = {
        "certificates": client.get("/api/certificates").json(),
        "ledger": client.get("/api/carbon-credits/ledger").json(),
        "blending": client.get("/api/compliance/blending").json(),
        "bio_table": client.get("/api/compliance/bio-carbon/table").json(),
    }
    oid = client.get("/api/airlines").json()[0]["id"]
    r = client.get(f"/api/airlines/{oid}/report", params={"start": "2000-01-01", "end": "2100-01-01", "fmt": "excel"})
    rows = [list(x) for x in load_workbook(io.BytesIO(r.content)).active.iter_rows(values_only=True)]
    # drop the delivery-date column (relative to "today") and the period line
    out["excel_rows_no_date"] = [rows[0], rows[3]] + [x[1:] for x in rows[4:]]
    out["excel_disposition"] = r.headers["content-disposition"].split("_report_")[0]
    return _strip(out)


def test_api_output_matches_pre_refactor_snapshot(client):
    expected = json.loads(GOLDEN.read_text())
    assert json.loads(json.dumps(snapshot(client), default=str)) == expected
