from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.base import Base


# ==========================================================
# Design note
# ==========================================================
# The spec asked for five models (Report, ScheduledReport,
# GeneratedReport, ReportHistory, ExportHistory). Reports here are
# computed on demand from live data (assets/alerts/tickets/monitoring)
# rather than pre-baked and stored, so there's no persistent "Report"
# or "GeneratedReport" row to keep -- the report *is* the API
# response. That collapses cleanly to two tables:
#   - ScheduledReport: the recurring-report configuration itself
#     ("email me the Alert Report every Monday").
#   - ExportHistory: an audit row for every export a user actually
#     downloaded (PDF/Excel/CSV/JSON), which is what "Report History"
#     / "Recent Reports" in the UI reads from.


class ScheduledReport(Base):
    __tablename__ = "scheduled_reports"

    id = Column(Integer, primary_key=True, index=True)

    report_type = Column(String(50), nullable=False)  # asset | alert | ticket | ...
    name = Column(String(150), nullable=False)

    # Daily | Weekly | Monthly | Quarterly | Yearly | Custom
    frequency = Column(String(20), nullable=False)
    # Only used when frequency == "Custom" (a cron expression).
    cron_expression = Column(String(100), nullable=True)

    export_format = Column(String(10), default="pdf")  # pdf | xlsx | csv | json

    # Comma-separated recipient emails, and/or "in_app" / "download_link".
    delivery_email = Column(Boolean, default=True)
    delivery_in_app = Column(Boolean, default=False)
    recipients = Column(Text, nullable=True)

    filters_json = Column(Text, nullable=True)  # serialized filter params

    is_active = Column(Boolean, default=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)

    creator = relationship("User")


class ExportHistory(Base):
    __tablename__ = "export_history"

    id = Column(Integer, primary_key=True, index=True)

    report_type = Column(String(50), nullable=False)
    export_format = Column(String(10), nullable=False)  # pdf | xlsx | csv | json
    file_name = Column(String(200), nullable=False)

    filters_json = Column(Text, nullable=True)

    requested_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    requester = relationship("User")
