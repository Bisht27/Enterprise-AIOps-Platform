"""
All report numbers are computed live from existing tables (Asset,
Monitoring, Alert, Ticket, NotificationDelivery) -- there is no
separate reporting data warehouse, so every endpoint here reflects the
current state of the platform, which also satisfies the spec's
"reports should update automatically" requirement for free (there's
nothing to keep in sync).

Two metrics are worth calling out because this schema doesn't track
them explicitly, so they're *derived* rather than stored:

- MTTD (Mean Time To Detect): approximated as the time between an
  Alert being created and its first linked Ticket being created --
  the schema has no separate "detected_at" distinct from Alert
  creation, so this measures triage speed, not true detection time.
- MTTR (Mean Time To Resolve): time between Ticket creation and the
  ticket reaching status "Closed" (using `updated_at` at the moment
  the status flips, i.e. the ticket's current `updated_at` for tickets
  that are currently Closed). Reopened/closed-again tickets aren't
  distinguished since there's no status-history table.
"""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.alert import Alert
from app.models.ticket import Ticket
from app.models.monitoring import Monitoring
from app.models.notification import Notification, NotificationDelivery
from app.models.user import User
from app.schemas.report import ReportFilters


def resolve_date_range(filters: ReportFilters) -> tuple[datetime, datetime]:
    end = filters.end_date or datetime.utcnow()
    start = filters.start_date or (end - timedelta(days=30))
    return start, end


# ==========================================================
# Dashboard summary
# ==========================================================

def get_dashboard_report(db: Session, filters: ReportFilters) -> dict:
    start, end = resolve_date_range(filters)

    total_assets = db.query(Asset).count()
    online_assets = db.query(Asset).filter(Asset.is_online.is_(True)).count()
    offline_assets = total_assets - online_assets
    healthy_assets = db.query(Asset).filter(Asset.health_status == "Healthy").count()
    critical_assets = db.query(Asset).filter(Asset.health_status == "Critical").count()

    total_alerts = db.query(Alert).filter(Alert.created_at.between(start, end)).count()
    critical_alerts = (
        db.query(Alert)
        .filter(Alert.created_at.between(start, end), Alert.severity == "Critical")
        .count()
    )
    warning_alerts = (
        db.query(Alert)
        .filter(Alert.created_at.between(start, end), Alert.severity == "Warning")
        .count()
    )

    open_tickets = db.query(Ticket).filter(Ticket.status != "Closed").count()
    closed_tickets = (
        db.query(Ticket)
        .filter(Ticket.status == "Closed", Ticket.updated_at.between(start, end))
        .count()
    )

    avg_cpu = db.query(func.avg(Monitoring.cpu_usage)).scalar() or 0
    avg_ram = db.query(func.avg(Monitoring.ram_usage)).scalar() or 0
    avg_disk = db.query(func.avg(Monitoring.disk_usage)).scalar() or 0

    availability_pct = (online_assets / total_assets * 100) if total_assets else 0.0

    monthly_incidents = (
        db.query(Alert)
        .filter(Alert.created_at >= datetime.utcnow() - timedelta(days=30))
        .count()
    )

    def breakdown(column) -> list[dict]:
        rows = (
            db.query(column, func.count(Asset.id))
            .group_by(column)
            .all()
        )
        return [
            {"label": label or "Unknown", "count": count}
            for label, count in rows
        ]

    return {
        "total_assets": total_assets,
        "online_assets": online_assets,
        "offline_assets": offline_assets,
        "healthy_assets": healthy_assets,
        "critical_assets": critical_assets,
        "total_alerts": total_alerts,
        "critical_alerts": critical_alerts,
        "warning_alerts": warning_alerts,
        "open_tickets": open_tickets,
        "closed_tickets": closed_tickets,
        "avg_cpu_usage": round(avg_cpu, 2),
        "avg_ram_usage": round(avg_ram, 2),
        "avg_disk_usage": round(avg_disk, 2),
        "asset_availability_pct": round(availability_pct, 2),
        "monthly_incidents": monthly_incidents,
        "assets_by_type": breakdown(Asset.asset_type),
        "assets_by_location": breakdown(Asset.location),
        "assets_by_os": breakdown(Asset.operating_system),
        "assets_by_department": breakdown(Asset.department),
    }


# ==========================================================
# Asset report
# ==========================================================

def get_asset_report(db: Session, filters: ReportFilters) -> dict:
    query = db.query(Asset)

    if filters.asset_type:
        query = query.filter(Asset.asset_type == filters.asset_type)
    if filters.operating_system:
        query = query.filter(Asset.operating_system == filters.operating_system)
    if filters.location:
        query = query.filter(Asset.location == filters.location)
    if filters.department:
        query = query.filter(Asset.department == filters.department)
    if filters.asset_status:
        query = query.filter(Asset.status == filters.asset_status)
    if filters.start_date:
        query = query.filter(Asset.created_at >= filters.start_date)
    if filters.end_date:
        query = query.filter(Asset.created_at <= filters.end_date)

    assets = query.all()

    warranty_soon = [
        a for a in assets
        if a.warranty_expiry and a.warranty_expiry <= datetime.utcnow() + timedelta(days=30)
    ]

    return {
        "total": len(assets),
        "assets": [
            {
                "id": a.id,
                "asset_tag": a.asset_tag,
                "asset_name": a.asset_name,
                "asset_type": a.asset_type,
                "operating_system": a.operating_system,
                "location": a.location,
                "department": a.department,
                "status": a.status,
                "health_status": a.health_status,
                "is_online": a.is_online,
                "warranty_expiry": a.warranty_expiry,
            }
            for a in assets
        ],
        "warranty_expiring_soon": len(warranty_soon),
    }


# ==========================================================
# Alert report
# ==========================================================

def get_alert_report(db: Session, filters: ReportFilters) -> dict:
    start, end = resolve_date_range(filters)

    query = db.query(Alert).filter(Alert.created_at.between(start, end))
    if filters.severity:
        query = query.filter(Alert.severity == filters.severity)

    alerts = query.all()

    per_day: dict[str, int] = {}
    severity_counts = {"Critical": 0, "Warning": 0, "Info": 0}

    for alert in alerts:
        day_key = alert.created_at.strftime("%Y-%m-%d")
        per_day[day_key] = per_day.get(day_key, 0) + 1
        severity_counts[alert.severity] = severity_counts.get(alert.severity, 0) + 1

    resolved = [a for a in alerts if a.resolved_at]
    avg_resolution_minutes = (
        sum((a.resolved_at - a.created_at).total_seconds() for a in resolved) / len(resolved) / 60
        if resolved else 0
    )

    return {
        "total": len(alerts),
        "alerts_per_day": [{"date": d, "count": c} for d, c in sorted(per_day.items())],
        "by_severity": [{"label": k, "count": v} for k, v in severity_counts.items()],
        "avg_resolution_minutes": round(avg_resolution_minutes, 1),
        "alerts": [
            {
                "id": a.id,
                "asset_id": a.asset_id,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "status": a.status,
                "created_at": a.created_at,
                "resolved_at": a.resolved_at,
            }
            for a in alerts
        ],
    }


# ==========================================================
# Ticket report
# ==========================================================

def get_ticket_report(db: Session, filters: ReportFilters) -> dict:
    start, end = resolve_date_range(filters)

    query = db.query(Ticket).filter(Ticket.created_at.between(start, end))
    if filters.priority:
        query = query.filter(Ticket.priority == filters.priority)

    tickets = query.all()

    by_status: dict[str, int] = {}
    by_priority: dict[str, int] = {}

    for t in tickets:
        by_status[t.status] = by_status.get(t.status, 0) + 1
        by_priority[t.priority] = by_priority.get(t.priority, 0) + 1

    closed = [t for t in tickets if t.status == "Closed"]
    avg_resolution_hours = (
        sum((t.updated_at - t.created_at).total_seconds() for t in closed) / len(closed) / 3600
        if closed else 0
    )

    return {
        "total": len(tickets),
        "by_status": [{"label": k, "count": v} for k, v in by_status.items()],
        "by_priority": [{"label": k, "count": v} for k, v in by_priority.items()],
        "avg_resolution_hours": round(avg_resolution_hours, 1),
        "tickets": [
            {
                "id": t.id,
                "title": t.title,
                "priority": t.priority,
                "status": t.status,
                "assigned_to": t.assigned_to,
                "created_at": t.created_at,
                "updated_at": t.updated_at,
            }
            for t in tickets
        ],
    }


# ==========================================================
# Performance report
# ==========================================================

def get_performance_report(db: Session, filters: ReportFilters) -> dict:
    start, end = resolve_date_range(filters)

    rows = (
        db.query(
            Monitoring.asset_id,
            func.avg(Monitoring.cpu_usage),
            func.max(Monitoring.cpu_usage),
            func.avg(Monitoring.ram_usage),
            func.max(Monitoring.ram_usage),
            func.avg(Monitoring.disk_usage),
            func.max(Monitoring.disk_usage),
        )
        .filter(Monitoring.created_at.between(start, end))
        .group_by(Monitoring.asset_id)
        .all()
    )

    assets_by_id = {a.id: a for a in db.query(Asset).all()}

    per_asset = []
    for asset_id, avg_cpu, peak_cpu, avg_ram, peak_ram, avg_disk, peak_disk in rows:
        asset = assets_by_id.get(asset_id)
        per_asset.append({
            "asset_id": asset_id,
            "asset_name": asset.asset_name if asset else f"Asset {asset_id}",
            "avg_cpu": round(avg_cpu or 0, 2),
            "peak_cpu": round(peak_cpu or 0, 2),
            "avg_ram": round(avg_ram or 0, 2),
            "peak_ram": round(peak_ram or 0, 2),
            "avg_disk": round(avg_disk or 0, 2),
            "peak_disk": round(peak_disk or 0, 2),
        })

    return {
        "per_asset": per_asset,
        "top_cpu": sorted(per_asset, key=lambda r: r["peak_cpu"], reverse=True)[:10],
        "top_ram": sorted(per_asset, key=lambda r: r["peak_ram"], reverse=True)[:10],
        "top_disk": sorted(per_asset, key=lambda r: r["peak_disk"], reverse=True)[:10],
    }


# ==========================================================
# Security report (derived from Notification rows in the
# "security_alerts" category -- see app/services/notification_events.py)
# ==========================================================

SECURITY_EVENT_TYPES = {"security_incident", "login_new_device", "failed_login_attempts"}


def get_security_report(db: Session, filters: ReportFilters) -> dict:
    start, end = resolve_date_range(filters)

    query = db.query(Notification).filter(
        Notification.event_type.in_(SECURITY_EVENT_TYPES),
        Notification.created_at.between(start, end),
    )
    events = query.all()

    by_type: dict[str, int] = {}
    for e in events:
        by_type[e.event_type] = by_type.get(e.event_type, 0) + 1

    return {
        "total": len(events),
        "by_type": [{"label": k, "count": v} for k, v in by_type.items()],
        "events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "title": e.title,
                "severity": e.severity,
                "created_at": e.created_at,
            }
            for e in events
        ],
    }


# ==========================================================
# Notification delivery report
# ==========================================================

def get_notification_report(db: Session, filters: ReportFilters) -> dict:
    start, end = resolve_date_range(filters)

    rows = (
        db.query(NotificationDelivery.channel, NotificationDelivery.status, func.count())
        .join(Notification, Notification.id == NotificationDelivery.notification_id)
        .filter(Notification.created_at.between(start, end))
        .group_by(NotificationDelivery.channel, NotificationDelivery.status)
        .all()
    )

    by_channel: dict[str, dict[str, int]] = {}
    for channel, status, count in rows:
        by_channel.setdefault(channel, {})[status] = count

    return {"by_channel": by_channel}


# ==========================================================
# Compliance report
# ==========================================================
# "Compliance" here means: assets that are out of policy against
# simple, objectively-checkable rules this schema actually supports
# (expired warranty/license, overdue maintenance, critical health,
# long-offline). There's no external compliance framework (SOC2/ISO)
# integration -- this is an internal asset-hygiene check, not an
# audit-framework mapping.

def get_compliance_report(db: Session, filters: ReportFilters) -> dict:
    now = datetime.utcnow()
    assets = db.query(Asset).all()

    warranty_expired = [a for a in assets if a.warranty_expiry and a.warranty_expiry < now]
    license_expired = [a for a in assets if a.license_expiry and a.license_expiry < now]
    maintenance_overdue = [a for a in assets if a.next_maintenance_date and a.next_maintenance_date < now]
    critical_health = [a for a in assets if a.health_status == "Critical"]
    long_offline = [
        a for a in assets
        if not a.is_online and a.last_seen and a.last_seen < now - timedelta(days=7)
    ]

    total_flags = (
        len(warranty_expired) + len(license_expired) + len(maintenance_overdue)
        + len(critical_health) + len(long_offline)
    )
    compliant_assets = len(assets) - len({
        a.id for a in warranty_expired + license_expired + maintenance_overdue + critical_health + long_offline
    })

    def summarize(items):
        return [{"id": a.id, "asset_name": a.asset_name, "asset_tag": a.asset_tag} for a in items]

    return {
        "total_assets": len(assets),
        "compliant_assets": compliant_assets,
        "flagged_assets": len(assets) - compliant_assets,
        "compliance_pct": round((compliant_assets / len(assets) * 100) if assets else 100.0, 2),
        "total_flags": total_flags,
        "warranty_expired": summarize(warranty_expired),
        "license_expired": summarize(license_expired),
        "maintenance_overdue": summarize(maintenance_overdue),
        "critical_health": summarize(critical_health),
        "long_offline": summarize(long_offline),
    }


# ==========================================================
# User activity report (admin only -- see router)
# ==========================================================

def get_user_activity_report(db: Session, filters: ReportFilters) -> dict:
    start, end = resolve_date_range(filters)
    users = db.query(User).all()

    rows = []
    for user in users:
        tickets_assigned = (
            db.query(Ticket)
            .filter(Ticket.assigned_to == user.username, Ticket.created_at.between(start, end))
            .count()
        )
        tickets_closed = (
            db.query(Ticket)
            .filter(
                Ticket.assigned_to == user.username,
                Ticket.status == "Closed",
                Ticket.updated_at.between(start, end),
            )
            .count()
        )
        rows.append({
            "user_id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "last_login_at": user.last_login_at,
            "last_login_ip": user.last_login_ip,
            "tickets_assigned": tickets_assigned,
            "tickets_closed": tickets_closed,
        })

    return {"total_users": len(users), "users": rows}
