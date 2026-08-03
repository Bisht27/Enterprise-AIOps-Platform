from datetime import datetime

from sqlalchemy.orm import Session

from app.models.ticket import Ticket
from app.models.alert import Alert
from app.schemas.ticket import TicketCreate, TicketUpdate
from app.services.notification_service import notify

ESCALATED_PRIORITIES = {"critical", "urgent"}
RESOLVED_STATUSES = {"resolved", "closed"}


def _ticket_fields(ticket: Ticket) -> list[dict]:
    return [
        {"label": "Ticket", "value": ticket.title},
        {"label": "Priority", "value": ticket.priority},
        {"label": "Status", "value": ticket.status},
        {"label": "Assigned To", "value": ticket.assigned_to or "Unassigned"},
    ]


def create_ticket(db: Session, data: TicketCreate, background_tasks=None):
    ticket = Ticket(**data.model_dump())

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    notify(
        db,
        background_tasks,
        event_type="ticket_created",
        title=f"Ticket Created: {ticket.title}",
        message=ticket.description or "A new ticket has been created.",
        ticket_id=ticket.id,
        alert_id=ticket.alert_id,
        extra_fields=_ticket_fields(ticket),
        dashboard_path="/tickets",
    )

    return ticket


def get_all_tickets(db: Session):
    return (
        db.query(Ticket)
        .order_by(Ticket.created_at.desc())
        .all()
    )


def get_ticket(db: Session, ticket_id: int):
    return (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id)
        .first()
    )


def update_ticket(
    db: Session,
    ticket_id: int,
    data: TicketUpdate,
    background_tasks=None,
):
    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id)
        .first()
    )

    if not ticket:
        return None

    update_data = data.model_dump(exclude_unset=True)

    previous_assigned_to = ticket.assigned_to
    previous_status = ticket.status
    previous_priority = ticket.priority

    for key, value in update_data.items():
        setattr(ticket, key, value)

    db.commit()
    db.refresh(ticket)

    newly_assigned = (
        "assigned_to" in update_data
        and ticket.assigned_to
        and ticket.assigned_to != previous_assigned_to
    )
    newly_resolved = (
        "status" in update_data
        and ticket.status.lower() in RESOLVED_STATUSES
        and previous_status.lower() not in RESOLVED_STATUSES
    )
    newly_escalated = (
        ("priority" in update_data and ticket.priority.lower() in ESCALATED_PRIORITIES
         and previous_priority.lower() not in ESCALATED_PRIORITIES)
        or ("status" in update_data and ticket.status.lower() == "escalated")
    )

    if newly_assigned:
        notify(
            db, background_tasks,
            event_type="ticket_assigned",
            title=f"Ticket Assigned: {ticket.title}",
            message=f"Ticket has been assigned to {ticket.assigned_to}.",
            ticket_id=ticket.id,
            alert_id=ticket.alert_id,
            extra_fields=_ticket_fields(ticket),
            dashboard_path="/tickets",
        )

    if newly_resolved:
        # Resolving/closing a ticket also stops the alert that spawned
        # it, if that alert is still open -- otherwise the alert would
        # keep firing "still active" reminders for an issue the ticket
        # says is already handled.
        linked_alert = (
            db.query(Alert)
            .filter(Alert.id == ticket.alert_id, Alert.status == "Open")
            .first()
        )
        if linked_alert:
            linked_alert.status = "Resolved"
            linked_alert.resolved_at = datetime.utcnow()
            db.commit()

        notify(
            db, background_tasks,
            event_type="ticket_closed",
            title=f"Ticket {ticket.status}: {ticket.title}",
            message=ticket.resolution_notes or f"Ticket has been {ticket.status.lower()}.",
            ticket_id=ticket.id,
            alert_id=ticket.alert_id,
            extra_fields=_ticket_fields(ticket),
            dashboard_path="/tickets",
        )

    if newly_escalated:
        notify(
            db, background_tasks,
            event_type="ticket_escalated",
            title=f"Ticket Escalated: {ticket.title}",
            message="Ticket priority has been escalated and needs attention.",
            severity="Warning",
            ticket_id=ticket.id,
            alert_id=ticket.alert_id,
            extra_fields=_ticket_fields(ticket),
            dashboard_path="/tickets",
        )

    return ticket


def resolve_ticket(db: Session, ticket_id: int, background_tasks=None):
    """Convenience wrapper around update_ticket for the frontend's
    Resolve button -- avoids the client needing to know the exact
    status string the backend expects."""
    return update_ticket(
        db, ticket_id, TicketUpdate(status="Resolved"), background_tasks,
    )


def delete_ticket(
    db: Session,
    ticket_id: int,
):
    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id)
        .first()
    )

    if not ticket:
        return None

    db.delete(ticket)
    db.commit()

    return True