from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Equipment, Reservation
from backend.app.schemas import ReservationCreate, ReservationRead
from backend.app.security import CurrentUser


router = APIRouter(prefix="/reservations", tags=["reservations"])
DatabaseSession = Annotated[Session, Depends(get_db)]


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

    reservation = Reservation(
        user_id=current_user.id,
        equipment_id=equipment.id,
        starts_at=reservation_data.starts_at,
        ends_at=reservation_data.ends_at,
    )
    database.add(reservation)
    database.commit()
    database.refresh(reservation)
    return reservation
