from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.monitoring import Monitoring
from app.models.asset import Asset
from app.models.alert import Alert

from app.schemas.monitoring import MonitoringCreate
from app.schemas.alert import AlertCreate

from app.api.v1.alerts.service import create_alert
from app.services.notification_service import notify
from app.core.config import settings


# ============================
# Thresholds
# ============================

CPU_WARNING_THRESHOLD = 90
CPU_THRESHOLD = 90

RAM_WARNING_THRESHOLD = 90
RAM_THRESHOLD = 90

DISK_WARNING_THRESHOLD = 90
DISK_THRESHOLD = 90

NETWORK_WARNING_BYTES = 100_000_000


_RANGE_TO_DELTA = {
    "1h": timedelta(hours=1),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
}


# =====================================================
# Save Monitoring Data
# =====================================================

def save_metrics(db: Session, data: MonitoringCreate, background_tasks=None):
    monitoring = Monitoring(**data.model_dump())

    db.add(monitoring)
    db.commit()
    db.refresh(monitoring)

    check_thresholds(db, monitoring, background_tasks)

    return monitoring


def create_monitoring(db: Session, data: MonitoringCreate):
    return save_metrics(db, data)


# =====================================================
# Latest Monitoring
# =====================================================

def get_latest_metrics(db: Session, asset_id: int):
    return (
        db.query(Monitoring)
        .filter(Monitoring.asset_id == asset_id)
        .order_by(Monitoring.created_at.desc())
        .first()
    )


# =====================================================
# History
# =====================================================

def get_metrics_history(
    db: Session,
    asset_id: int,
    range: Optional[str] = None,
):
    query = (
        db.query(Monitoring)
        .filter(Monitoring.asset_id == asset_id)
    )

    delta = _RANGE_TO_DELTA.get(range) if range else None

    if delta:
        cutoff = datetime.utcnow() - delta
        query = query.filter(
            Monitoring.created_at >= cutoff
        )

    return (
        query
        .order_by(Monitoring.created_at.desc())
        .all()
    )


def get_asset_monitoring(db: Session, asset_id: int):
    return get_metrics_history(db, asset_id)


# =====================================================
# Dashboard
# =====================================================

def get_dashboard_metrics(db: Session):

    latest = (
        db.query(Monitoring)
        .order_by(Monitoring.created_at.desc())
        .all()
    )

    if not latest:
        return {
            "total_servers": 0,
            "avg_cpu": 0,
            "avg_ram": 0,
            "avg_disk": 0,
        }

    total = len(latest)

    return {
        "total_servers": total,
        "avg_cpu": round(sum(x.cpu_usage for x in latest) / total, 2),
        "avg_ram": round(sum(x.ram_usage for x in latest) / total, 2),
        "avg_disk": round(sum(x.disk_usage for x in latest) / total, 2),
    }


# =====================================================
# Helper Functions
# =====================================================

def get_open_alert(
    db: Session,
    asset_id: int,
    alert_type: str,
):
    return (
        db.query(Alert)
        .filter(
            Alert.asset_id == asset_id,
            Alert.alert_type == alert_type,
            Alert.status == "Open",
        )
        .first()
    )


def resolve_open_alert(
    db: Session,
    asset_id: int,
    alert_type: str,
) -> bool:
    """Resolve the open alert of this type, if any. Returns True if an
    alert actually transitioned Open -> Resolved (i.e. a recovery just
    happened), False if there was nothing open to resolve."""
    alert = get_open_alert(
        db,
        asset_id,
        alert_type,
    )

    if alert:
        alert.status = "Resolved"
        alert.resolved_at = datetime.utcnow()
        db.commit()
        return True

    return False


# =====================================================
# Threshold Checker -- consolidated, state-transition-based
# =====================================================
#
# Enterprise-grade behavior (see notification architecture notes):
#   - Metrics are evaluated against NORMAL / WARNING / CRITICAL bands.
#   - An Alert row (per asset + metric type) is the source of truth
#     for "is this metric currently in a bad state". create_alert()/
#     resolve_open_alert() keep that row in sync exactly as before.
#   - What changed: individual per-metric emails/WhatsApp messages are
#     no longer sent here (notify_individually=False). Instead, ONE
#     notification is sent per monitoring cycle, and only when
#     something actually changed for this asset -- a metric newly
#     breached a threshold, a metric recovered, or a metric has been
#     breached continuously for 24h+ without a reminder. A cycle where
#     nothing crossed a threshold and nothing changed sends nothing.

# Configurable via ALERT_REMINDER_HOURS (see app/core/config.py) so the
# reminder cadence can be tuned per environment without a code change.
REMINDER_INTERVAL = timedelta(hours=settings.ALERT_REMINDER_HOURS)

_METRIC_DEFS = [
    # (alert_type, warning_threshold, critical_threshold, value_fn, label, unit)
    ("CPU", CPU_WARNING_THRESHOLD, CPU_THRESHOLD, lambda m: m.cpu_usage, "CPU Usage", "%"),
    ("RAM", RAM_WARNING_THRESHOLD, RAM_THRESHOLD, lambda m: m.ram_usage, "RAM Usage", "%"),
    ("Disk", DISK_WARNING_THRESHOLD, DISK_THRESHOLD, lambda m: m.disk_usage, "Disk Usage", "%"),
]


def _metric_state(value: float, warning: float, critical: float) -> str:
    if value >= critical:
        return "Critical"
    if value >= warning:
        return "Warning"
    return "Normal"


def _sync_metric_alert(db: Session, monitoring: Monitoring, alert_type: str,
                        state: str, message: str, background_tasks) -> tuple[bool, bool]:
    """
    Bring the Alert row for this asset+metric in line with `state`
    (Normal / Warning / Critical), without sending an individual
    notification (that's handled once, consolidated, by the caller).

    Returns (newly_triggered, newly_recovered).
    """
    if state == "Normal":
        recovered = resolve_open_alert(db, monitoring.asset_id, alert_type)
        return False, recovered

    existing = get_open_alert(db, monitoring.asset_id, alert_type)
    if existing:
        return False, False

    create_alert(
        db,
        AlertCreate(
            asset_id=monitoring.asset_id,
            alert_type=alert_type,
            severity=state,
            message=message,
        ),
        background_tasks,
        notify_individually=False,
    )
    return True, False


def _build_alert_fields(asset: Optional[Asset], monitoring: Monitoring,
                         severity: str, triggered_labels: list[str],
                         timestamp: str) -> list[dict]:
    """The single template used for Email / WhatsApp / Dashboard, per
    the required layout: Asset Name, Hostname, IP Address, Logged-in
    User, Operating System, CPU/RAM/Disk/Storage/Network, Running
    Processes, Severity, Timestamp, Triggered Metrics."""

    def disk_used_pct() -> str:
        # "Storage Usage" is the point-in-time used/total captured at
        # asset registration (Asset.disk_used / disk_total), distinct
        # from "Disk Usage" which is the live monitored percentage.
        try:
            used = float(asset.disk_used) if asset and asset.disk_used else None
            total = float(asset.disk_total) if asset and asset.disk_total else None
            if used is not None and total:
                return f"{used:.2f} / {total:.2f} GB ({used / total * 100:.1f}%)"
        except (TypeError, ValueError):
            pass
        return "N/A"

    return [
        {"label": "Asset Name", "value": asset.asset_name if asset else str(monitoring.asset_id)},
        {"label": "Hostname", "value": (asset.hostname if asset else None) or "N/A"},
        {"label": "IP Address", "value": (asset.ip_address if asset else None) or "N/A"},
        {"label": "Logged-in User", "value": monitoring.logged_in_user or "N/A"},
        {"label": "Operating System", "value": (asset.operating_system if asset else None) or "N/A"},
        {"label": "CPU Usage", "value": f"{monitoring.cpu_usage:.2f}%"},
        {"label": "RAM Usage", "value": f"{monitoring.ram_usage:.2f}%"},
        {"label": "Disk Usage", "value": f"{monitoring.disk_usage:.2f}%"},
        {"label": "Storage Usage", "value": disk_used_pct()},
        {"label": "Network Upload", "value": f"{(monitoring.network_sent or 0) / 1_000_000:.2f} MB"},
        {"label": "Network Download", "value": f"{(monitoring.network_received or 0) / 1_000_000:.2f} MB"},
        {"label": "Running Processes", "value": str(monitoring.running_processes) if monitoring.running_processes is not None else "N/A"},
        {"label": "Severity", "value": severity},
        {"label": "Timestamp", "value": timestamp},
        {"label": "Triggered Metrics", "value": ", ".join(triggered_labels) if triggered_labels else "None"},
    ]


def _render_template_text(title: str, fields: list[dict]) -> str:
    lines = [title, ""]
    for f in fields:
        lines.append(f"{f['label']}: {f['value']}")
    return "\n".join(lines)


def check_thresholds(db: Session, monitoring: Monitoring, background_tasks=None):

    asset = (
        db.query(Asset)
        .filter(Asset.id == monitoring.asset_id)
        .first()
    )

    asset_name = asset.asset_name if asset else str(monitoring.asset_id)
    now = datetime.utcnow()
    timestamp = now.strftime("%Y-%m-%d %H:%M UTC")

    triggered_labels: list[str] = []
    metric_severity: dict[str, str] = {}
    any_newly_triggered = False
    any_newly_recovered = False

    for alert_type, warning, critical, value_fn, label, unit in _METRIC_DEFS:
        value = value_fn(monitoring) or 0
        state = _metric_state(value, warning, critical)
        message = f"{label} is {value:.2f}{unit}"

        newly_triggered, newly_recovered = _sync_metric_alert(
            db, monitoring, alert_type, state, message, background_tasks,
        )
        any_newly_triggered = any_newly_triggered or newly_triggered
        any_newly_recovered = any_newly_recovered or newly_recovered

        if state != "Normal":
            triggered_labels.append(f"{label} ({value:.2f}{unit})")
            metric_severity[alert_type] = state

    # ---- Network is byte-based (not a percentage band), handled
    # separately but through the same Alert-row sync mechanism.
    total_network = (monitoring.network_sent or 0) + (monitoring.network_received or 0)
    network_state = "Warning" if total_network >= NETWORK_WARNING_BYTES else "Normal"
    network_message = f"Combined Network Traffic is {total_network / 1_000_000:.2f} MB"
    newly_triggered, newly_recovered = _sync_metric_alert(
        db, monitoring, "Network", network_state, network_message, background_tasks,
    )
    any_newly_triggered = any_newly_triggered or newly_triggered
    any_newly_recovered = any_newly_recovered or newly_recovered
    if network_state != "Normal":
        triggered_labels.append(f"Network Usage ({total_network / 1_000_000:.2f} MB)")
        metric_severity["Network"] = network_state

    is_critical = "Critical" in metric_severity.values()
    is_warning = bool(metric_severity) and not is_critical
    overall_severity = "Critical" if is_critical else ("Warning" if is_warning else "Info")

    # ---- Reminder: is any still-open, already-notified alert overdue
    # for a "still active" nudge? One consolidated reminder covers all
    # of them, throttled per-alert via last_notified_at.
    reminder_due = False
    if metric_severity:
        open_alerts = (
            db.query(Alert)
            .filter(
                Alert.asset_id == monitoring.asset_id,
                Alert.alert_type.in_(list(metric_severity.keys())),
                Alert.status == "Open",
            )
            .all()
        )
        for a in open_alerts:
            reference = a.last_notified_at or a.created_at
            if reference and (now - reference) >= REMINDER_INTERVAL:
                reminder_due = True
                break

    should_notify = any_newly_triggered or any_newly_recovered or reminder_due

    # ---- Health status stays in sync with the same aggregation, but
    # no longer fires its own separate notification -- it's folded
    # into the one consolidated notification below (Issue 3).
    new_status = "Critical" if is_critical else ("Warning" if is_warning else "Healthy")
    if asset and asset.health_status != new_status:
        asset.health_status = new_status
        db.commit()

    if should_notify and asset:
        fields = _build_alert_fields(asset, monitoring, overall_severity, triggered_labels, timestamp)

        if not metric_severity:
            title = f"Enterprise AIOps Alert - Recovered: {asset_name}"
        elif any_newly_triggered:
            title = f"Enterprise AIOps Alert: {asset_name}"
        else:
            title = f"Enterprise AIOps Alert - Still Active: {asset_name}"

        message = _render_template_text(title, fields)

        notify(
            db,
            background_tasks,
            event_type="monitoring_alert" if metric_severity else "monitoring_recovery",
            title=title,
            message=message,
            severity=overall_severity,
            asset_id=monitoring.asset_id,
            extra_fields=fields,
            dashboard_path=f"/asset/{monitoring.asset_id}",
        )

        # Reset the reminder clock for every currently-open metric alert
        # on this asset, whether it was newly triggered or just reminded.
        if metric_severity:
            (
                db.query(Alert)
                .filter(
                    Alert.asset_id == monitoring.asset_id,
                    Alert.alert_type.in_(list(metric_severity.keys())),
                    Alert.status == "Open",
                )
                .update({Alert.last_notified_at: now}, synchronize_session=False)
            )
            db.commit()
