from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Reservation, ReservationStatus
from backend.app.schemas import ReservationRead
from backend.app.security import AdminUser


router = APIRouter(prefix="/admin/reservations", tags=["admin reservations"])
DatabaseSession = Annotated[Session, Depends(get_db)]


def get_reservation_or_404(
    reservation_id: int,
    database: DatabaseSession,
) -> Reservation:
    reservation = database.get(Reservation, reservation_id)

    if reservation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found",
        )

    return reservation


@router.get("", response_model=list[ReservationRead])
def list_all_reservations(
    database: DatabaseSession,
    admin_user: AdminUser,
):
    statement = select(Reservation).order_by(Reservation.starts_at, Reservation.id)
    return list(database.scalars(statement))


@router.get("/{reservation_id}", response_model=ReservationRead)
def get_any_reservation(
    reservation_id: int,
    database: DatabaseSession,
    admin_user: AdminUser,
):
    return get_reservation_or_404(reservation_id, database)


@router.post("/{reservation_id}/cancel", response_model=ReservationRead)
def cancel_any_reservation(
    reservation_id: int,
    database: DatabaseSession,
    admin_user: AdminUser,
):
    reservation = get_reservation_or_404(reservation_id, database)

    if reservation.status == ReservationStatus.CANCELLED:
        return reservation

    reservation.status = ReservationStatus.CANCELLED
    database.commit()
    database.refresh(reservation)
    return reservation
