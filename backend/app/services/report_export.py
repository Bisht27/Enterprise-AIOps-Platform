"""
Turns the dicts returned by app/services/report_analytics.py into
downloadable files.

- CSV / JSON: export the specific report_type's row-level data
  (e.g. the `assets` list of an asset report).
- XLSX: always builds the full multi-sheet workbook (Summary, Assets,
  Monitoring/Performance, Alerts, Tickets, Notifications) per the
  spec, since a single-sheet Excel file has no advantage over CSV.
- PDF: a genuinely generated (not templated-then-screenshotted)
  report with a title page, generated date, summary table, and a
  detail table, with page numbers in the footer. It does NOT embed
  charts -- rendering charts into a PDF needs a headless rendering
  step (e.g. matplotlib -> PNG) which is a meaningfully bigger, more
  fragile dependency chain than everything else in this module, and
  the frontend already provides interactive charts. Flagging this as
  a known gap rather than faking it.
"""

import csv
import io
import json
from datetime import datetime

import matplotlib
matplotlib.use("Agg")  # headless -- no display server in this environment
import matplotlib.pyplot as plt

import pandas as pd
from fpdf import FPDF

from app.core.config import settings
from app.services import report_analytics as analytics


# Which breakdown field (if present in the report data) gets charted
# in the PDF -- first match wins. Keeps to ONE chart per PDF rather
# than trying to replicate every frontend chart, since each embedded
# chart is a real matplotlib render (not free) and the PDF's job is a
# readable summary document, not a chart gallery.
CHART_FIELD_PRIORITY = [
    "by_severity", "by_status", "by_priority",
    "assets_by_type", "assets_by_department", "by_type", "by_channel",
]


def _render_breakdown_chart(labels: list[str], values: list[float], title: str) -> bytes:
    fig, ax = plt.subplots(figsize=(6.5, 3))
    bars = ax.bar(labels, values, color="#2563eb")
    ax.set_title(title, fontsize=11)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="x", labelrotation=30, labelsize=8)
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f"{int(height)}", (bar.get_x() + bar.get_width() / 2, height),
                    textcoords="offset points", xytext=(0, 3), ha="center", fontsize=7)
    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150)
    plt.close(fig)
    buffer.seek(0)
    return buffer.getvalue()


def _find_chart_data(data: dict) -> tuple[str, list[dict]] | None:
    for field in CHART_FIELD_PRIORITY:
        value = data.get(field)
        if isinstance(value, list) and value and isinstance(value[0], dict) and "label" in value[0]:
            return field, value
    return None


REPORT_ROW_KEY = {
    "asset": "assets",
    "alert": "alerts",
    "ticket": "tickets",
    "security": "events",
    "user_activity": "users",
}


def _rows_for(report_type: str, data: dict) -> list[dict]:
    key = REPORT_ROW_KEY.get(report_type)
    if key and key in data:
        return data[key]
    # Dashboard / performance reports don't have one obvious row list;
    # flatten the top-level scalars into a single summary row instead.
    return [{k: v for k, v in data.items() if isinstance(v, (str, int, float, bool))}]


def to_csv(report_type: str, data: dict) -> bytes:
    rows = _rows_for(report_type, data)
    if not rows:
        return b""

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue().encode("utf-8")


def to_json(data: dict) -> bytes:
    def default(o):
        if isinstance(o, datetime):
            return o.isoformat()
        return str(o)

    return json.dumps(data, default=default, indent=2).encode("utf-8")


def to_excel_workbook(db, filters) -> bytes:
    dashboard = analytics.get_dashboard_report(db, filters)
    assets = analytics.get_asset_report(db, filters)
    performance = analytics.get_performance_report(db, filters)
    alerts = analytics.get_alert_report(db, filters)
    tickets = analytics.get_ticket_report(db, filters)
    notifications = analytics.get_notification_report(db, filters)

    summary_df = pd.DataFrame([
        {"Metric": "Total Assets", "Value": dashboard["total_assets"]},
        {"Metric": "Online Assets", "Value": dashboard["online_assets"]},
        {"Metric": "Offline Assets", "Value": dashboard["offline_assets"]},
        {"Metric": "Total Alerts", "Value": dashboard["total_alerts"]},
        {"Metric": "Critical Alerts", "Value": dashboard["critical_alerts"]},
        {"Metric": "Open Tickets", "Value": dashboard["open_tickets"]},
        {"Metric": "Closed Tickets", "Value": dashboard["closed_tickets"]},
        {"Metric": "Avg CPU Usage", "Value": dashboard["avg_cpu_usage"]},
        {"Metric": "Avg RAM Usage", "Value": dashboard["avg_ram_usage"]},
        {"Metric": "Avg Disk Usage", "Value": dashboard["avg_disk_usage"]},
        {"Metric": "Asset Availability %", "Value": dashboard["asset_availability_pct"]},
    ])

    assets_df = pd.DataFrame(assets["assets"])
    monitoring_df = pd.DataFrame(performance["per_asset"])
    alerts_df = pd.DataFrame(alerts["alerts"])
    tickets_df = pd.DataFrame(tickets["tickets"])

    notif_rows = [
        {"Channel": channel, "Status": status, "Count": count}
        for channel, statuses in notifications["by_channel"].items()
        for status, count in statuses.items()
    ]
    notifications_df = pd.DataFrame(notif_rows)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        (assets_df if not assets_df.empty else pd.DataFrame([{"info": "No assets"}])).to_excel(
            writer, sheet_name="Assets", index=False
        )
        (monitoring_df if not monitoring_df.empty else pd.DataFrame([{"info": "No monitoring data"}])).to_excel(
            writer, sheet_name="Monitoring", index=False
        )
        (alerts_df if not alerts_df.empty else pd.DataFrame([{"info": "No alerts"}])).to_excel(
            writer, sheet_name="Alerts", index=False
        )
        (tickets_df if not tickets_df.empty else pd.DataFrame([{"info": "No tickets"}])).to_excel(
            writer, sheet_name="Tickets", index=False
        )
        (notifications_df if not notifications_df.empty else pd.DataFrame([{"info": "No notifications"}])).to_excel(
            writer, sheet_name="Notifications", index=False
        )

    return buffer.getvalue()


class _ReportPDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def to_pdf(report_type: str, data: dict) -> bytes:
    pdf = _ReportPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(17, 24, 39)
    pdf.cell(0, 12, settings.APP_NAME, ln=True)

    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(37, 99, 235)
    pdf.cell(0, 8, f"{report_type.replace('_', ' ').title()} Report", ln=True)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(107, 114, 128)
    pdf.cell(0, 6, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", ln=True)
    pdf.ln(6)

    # Summary table -- scalar top-level fields
    scalar_fields = {k: v for k, v in data.items() if isinstance(v, (str, int, float, bool))}
    if scalar_fields:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(17, 24, 39)
        pdf.cell(0, 8, "Summary", ln=True)
        pdf.set_font("Helvetica", "", 10)
        for label, value in scalar_fields.items():
            pdf.set_text_color(75, 85, 99)
            pdf.cell(70, 7, label.replace("_", " ").title())
            pdf.set_text_color(17, 24, 39)
            pdf.cell(0, 7, str(value), ln=True)
        pdf.ln(4)

    # Chart -- one, if the data has a breakdown worth charting (see
    # CHART_FIELD_PRIORITY above).
    chart = _find_chart_data(data)
    if chart:
        field_name, breakdown = chart
        try:
            chart_bytes = _render_breakdown_chart(
                [str(row["label"])[:12] for row in breakdown],
                [row["count"] for row in breakdown],
                field_name.replace("_", " ").title(),
            )
            pdf.image(io.BytesIO(chart_bytes), x=15, w=pdf.w - 30)
            pdf.ln(4)
        except Exception:  # noqa: BLE001
            # A chart failing to render should never block the rest
            # of the PDF from being generated.
            pass

    # Detail table
    rows = _rows_for(report_type, data)
    if rows and len(rows) > 1:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(17, 24, 39)
        pdf.cell(0, 8, "Details", ln=True)

        columns = list(rows[0].keys())[:6]  # keep the table readable
        col_width = (pdf.w - 20) / max(len(columns), 1)

        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(243, 244, 246)
        for col in columns:
            pdf.cell(col_width, 7, col.replace("_", " ").title(), border=1, fill=True)
        pdf.ln()

        pdf.set_font("Helvetica", "", 8)
        for row in rows[:200]:  # cap so the PDF stays a real, openable file
            for col in columns:
                pdf.cell(col_width, 6, str(row.get(col, ""))[:30], border=1)
            pdf.ln()

    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(156, 163, 175)
    pdf.multi_cell(0, 5, "Generated automatically by the AIOps Platform Reports module.")

    return bytes(pdf.output())
