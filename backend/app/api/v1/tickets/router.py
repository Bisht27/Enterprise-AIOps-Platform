from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.schemas.ticket import (
    TicketCreate,
    TicketResponse,
    TicketUpdate,
)
from app.api.v1.tickets.service import (
    create_ticket,
    get_all_tickets,
    get_ticket,
    update_ticket,
    resolve_ticket,
    delete_ticket,
)

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"],
)


@router.post(
    "/",
    response_model=TicketResponse,
)
def create_new_ticket(
    data: TicketCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    return create_ticket(db, data, background_tasks)


@router.get(
    "/",
    response_model=list[TicketResponse],
)
def list_tickets(
    db: Session = Depends(get_db),
):
    return get_all_tickets(db)


@router.get(
    "/{ticket_id}",
    response_model=TicketResponse,
)
def get_single_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
):
    ticket = get_ticket(db, ticket_id)

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    return ticket


@router.put(
    "/{ticket_id}",
    response_model=TicketResponse,
)
def update_single_ticket(
    ticket_id: int,
    data: TicketUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    ticket = update_ticket(
        db,
        ticket_id,
        data,
        background_tasks,
    )

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    return ticket


@router.put(
    "/{ticket_id}/resolve",
    response_model=TicketResponse,
)
def resolve_single_ticket(
    ticket_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    ticket = resolve_ticket(db, ticket_id, background_tasks)

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    return ticket


@router.delete(
    "/{ticket_id}",
)
def remove_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
):
    deleted = delete_ticket(db, ticket_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    return {
        "message": "Ticket deleted successfully"
    }