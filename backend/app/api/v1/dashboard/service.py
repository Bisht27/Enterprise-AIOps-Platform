from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.alert import Alert
from app.models.ticket import Ticket
from app.models.monitoring import Monitoring
from app.models.monitoring import Monitoring


def get_monitoring_history(
    db: Session,
    asset_id: int,
    limit: int = 20,
):
    records = (
        db.query(Monitoring)
        .filter(Monitoring.asset_id == asset_id)
        .order_by(Monitoring.created_at.desc())
        .limit(limit)
        .all()
    )

    records.reverse()

    return {
        "asset_id": asset_id,
        "history": records,
    }

def get_dashboard_summary(db: Session):

    total_assets = db.query(Asset).count()

    online_assets = (
        db.query(Asset)
        .filter(Asset.is_online.is_(True))
        .count()
    )
    offline_assets = total_assets - online_assets

    total_alerts = db.query(Alert).count()

    open_alerts = (
        db.query(Alert)
        .filter(Alert.status == "Open")
        .count()
    )

    critical_alerts = (
        db.query(Alert)
        .filter(Alert.severity == "Critical")
        .count()
    )

    total_tickets = db.query(Ticket).count()

    open_tickets = (
        db.query(Ticket)
        .filter(Ticket.status == "Open")
        .count()
    )

    cpu_average = (
        db.query(func.avg(Monitoring.cpu_usage)).scalar() or 0
    )

    ram_average = (
        db.query(func.avg(Monitoring.ram_usage)).scalar() or 0
    )

    disk_average = (
        db.query(func.avg(Monitoring.disk_usage)).scalar() or 0
    )

    return {
        "total_assets": total_assets,
        "online_assets": online_assets,
        "offline_assets": offline_assets,

        "total_alerts": total_alerts,
        "open_alerts": open_alerts,
        "critical_alerts": critical_alerts,

        "total_tickets": total_tickets,
        "open_tickets": open_tickets,

        "cpu_average": round(cpu_average, 2),
        "ram_average": round(ram_average, 2),
        "disk_average": round(disk_average, 2),
    }