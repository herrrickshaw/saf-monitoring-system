"""Generates a traceable per-airline, per-period SAF supply report (PDF + Excel)
covering feedstock origin, GHG intensity, ASTM pathway, blend ratio, and CORSIA
credit for every delivered batch -- the artifact an airline needs for its own
ReFuelEU/CORSIA compliance reporting."""

from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import date

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from ..models import AirlineDelivery, AirlineOfftake


def _deliveries_for_period(db: Session, airline_offtake_id: int, start: date, end: date) -> list[AirlineDelivery]:
    return (
        db.query(AirlineDelivery)
        .filter(
            AirlineDelivery.airline_offtake_id == airline_offtake_id,
            AirlineDelivery.delivery_date >= start,
            AirlineDelivery.delivery_date <= end,
        )
        .all()
    )


def _row_for(delivery: AirlineDelivery) -> list:
    batch = delivery.batch
    cert = batch.certificate
    feedstock = batch.feedstock_delivery.feedstock
    return [
        delivery.delivery_date.isoformat(),
        batch.batch_code,
        feedstock.name,
        batch.astm_pathway.code,
        f"{batch.blend_ratio_pct:.1f}%",
        f"{delivery.volume_liters:,.0f} L",
        f"{cert.ghg_intensity:.1f}" if cert else "n/a",
        f"{cert.ghg_savings_pct:.1f}%" if cert else "n/a",
        f"{cert.corsia_reduction_pct:.1f}%" if cert else "n/a",
        f"{delivery.credit_ledger.tco2e_saved:.2f}" if delivery.credit_ledger else "n/a",
    ]


HEADERS = [
    "Delivery Date", "Batch Code", "Feedstock", "ASTM Pathway", "Blend Ratio",
    "Volume", "RED III GHG Intensity (gCO2eq/MJ)", "RED III GHG Savings %",
    "CORSIA Reduction %", "tCO2e Credited (CORSIA)",
]


@dataclass(frozen=True)
class ReportData:
    """Everything a renderer needs: formatted rows plus period totals."""

    title: str
    airport: str
    start: date
    end: date
    rows: list[list]
    total_volume_liters: float
    total_tco2e: float


def collect_report_data(db: Session, offtake: AirlineOfftake, start: date, end: date) -> ReportData:
    """Query the period's deliveries once and shape them for PDF/Excel rendering."""
    deliveries = _deliveries_for_period(db, offtake.id, start, end)
    return ReportData(
        title=f"SAF Supply Report \u2014 {offtake.airline_name}",
        airport=offtake.delivery_airport,
        start=start,
        end=end,
        rows=[_row_for(d) for d in deliveries],
        total_volume_liters=sum(d.volume_liters for d in deliveries),
        total_tco2e=sum(d.credit_ledger.tco2e_saved for d in deliveries if d.credit_ledger),
    )


def render_pdf(data: ReportData) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=15 * mm, bottomMargin=15 * mm)
    styles = getSampleStyleSheet()
    story = [
        Paragraph(data.title, styles["Title"]),
        Paragraph(f"Airport: {data.airport} | Period: {data.start} to {data.end}", styles["Normal"]),
        Spacer(1, 8 * mm),
    ]
    table = Table([HEADERS] + data.rows, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(f"Total volume delivered: {data.total_volume_liters:,.0f} L", styles["Normal"]))
    story.append(
        Paragraph(f"Total CORSIA emissions reduction credited: {data.total_tco2e:,.2f} tCO2e", styles["Normal"])
    )
    doc.build(story)
    return buffer.getvalue()


def render_excel(data: ReportData) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "SAF Supply Report"
    ws.append([data.title])
    ws.append([f"Airport: {data.airport}", f"Period: {data.start} to {data.end}"])
    ws.append([])
    ws.append(HEADERS)
    for row in data.rows:
        ws.append(row)
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def build_pdf(db: Session, offtake: AirlineOfftake, start: date, end: date) -> bytes:
    return render_pdf(collect_report_data(db, offtake, start, end))


def build_excel(db: Session, offtake: AirlineOfftake, start: date, end: date) -> bytes:
    return render_excel(collect_report_data(db, offtake, start, end))
