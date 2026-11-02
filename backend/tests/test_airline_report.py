import io
from datetime import date

from openpyxl import load_workbook

from app.reports.airline_report import HEADERS, ReportData, render_excel, render_pdf

DATA = ReportData(
    title="SAF Supply Report — Test Air", airport="EDDF", start=date(2026, 1, 1), end=date(2026, 12, 31),
    rows=[["2026-02-01", "B-1", "UCO", "HEFA-SPK", "30.0%", "1,000 L", "17.0", "81.9%", "84.4%", "1.23"]],
    total_volume_liters=1000.0, total_tco2e=1.23,
)


def test_render_excel_layout():
    ws = load_workbook(io.BytesIO(render_excel(DATA))).active
    rows = list(ws.iter_rows(values_only=True))
    assert rows[0][0] == DATA.title
    assert rows[1][:2] == ("Airport: EDDF", "Period: 2026-01-01 to 2026-12-31")
    assert list(rows[3]) == HEADERS
    assert list(rows[4]) == DATA.rows[0]


def test_render_pdf_is_pdf():
    assert render_pdf(DATA).startswith(b"%PDF")
