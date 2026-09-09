from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import (
    RESERVATION_OVERLAP_CONSTRAINT,
    Equipment,
    Reservation,
    ReservationStatus,
)
from backend.app.schemas import ReservationCreate, ReservationRead
from backend.app.security import CurrentUser


router = APIRouter(prefix="/reservations", tags=["reservations"])
DatabaseSession = Annotated[Session, Depends(get_db)]
RESERVATION_CONFLICT_DETAIL = "Equipment is already reserved for this time"


def raise_reservation_conflict() -> None:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=RESERVATION_CONFLICT_DETAIL,
    )


@router.post("", response_model=ReservationRead, status_code=status.HTTP_201_CREATED)
def create_reservation(
    reservation_data: ReservationCreate,
    database: DatabaseSession,
    current_user: CurrentUser,
):
    equipment = database.scalar(
        select(Equipment).where(
            Equipment.id == reservation_data.equipment_id,
            Equipment.is_active.is_(True),
        )
    )

    if equipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    overlapping_reservation_id = database.scalar(
        select(Reservation.id)
        .where(
            Reservation.equipment_id == equipment.id,
            Reservation.status == ReservationStatus.CONFIRMED,
            Reservation.starts_at < reservation_data.ends_at,
            Reservation.ends_at > reservation_data.starts_at,
        )
        .limit(1)
    )

    if overlapping_reservation_id is not None:
        raise_reservation_conflict()

    reservation = Reservation(
        user_id=current_user.id,
        equipment_id=equipment.id,
        starts_at=reservation_data.starts_at,
        ends_at=reservation_data.ends_at,
    )
    database.add(reservation)
    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        constraint_name = getattr(
            getattr(error.orig, "diag", None),
            "constraint_name",
            None,
        )

        if constraint_name == RESERVATION_OVERLAP_CONSTRAINT:
            raise_reservation_conflict()

        raise

    database.refresh(reservation)
    return reservation
