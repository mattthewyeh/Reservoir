from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Equipment, Reservation, ReservationStatus
from backend.app.schemas import (
    EquipmentAvailabilityQuery,
    EquipmentCreate,
    EquipmentRead,
    EquipmentUpdate,
)
from backend.app.security import AdminUser


router = APIRouter(prefix="/equipment", tags=["equipment"])
DatabaseSession = Annotated[Session, Depends(get_db)]
AvailabilityQuery = Annotated[EquipmentAvailabilityQuery, Query()]


@router.post("", response_model=EquipmentRead, status_code=status.HTTP_201_CREATED)
def create_equipment(
    equipment_data: EquipmentCreate,
    database: DatabaseSession,
    admin_user: AdminUser,
):
    equipment = Equipment(**equipment_data.model_dump())
    database.add(equipment)
    database.commit()
    database.refresh(equipment)
    return equipment


@router.get("", response_model=list[EquipmentRead])
def list_equipment(database: DatabaseSession):
    statement = (
        select(Equipment)
        .where(Equipment.is_active.is_(True))
        .order_by(Equipment.name, Equipment.id)
    )

    return list(database.scalars(statement))


@router.get("/availability", response_model=list[EquipmentRead])
def list_available_equipment(
    availability: AvailabilityQuery,
    database: DatabaseSession,
):
    overlapping_reservation = (
        select(Reservation.id)
        .where(
            Reservation.equipment_id == Equipment.id,
            Reservation.status == ReservationStatus.CONFIRMED,
            Reservation.starts_at < availability.ends_at,
            Reservation.ends_at > availability.starts_at,
        )
        .exists()
    )
    statement = (
        select(Equipment)
        .where(
            Equipment.is_active.is_(True),
            ~overlapping_reservation,
        )
        .order_by(Equipment.name, Equipment.id)
    )
    return list(database.scalars(statement))


@router.get("/{equipment_id}", response_model=EquipmentRead)
def get_equipment(equipment_id: int, database: DatabaseSession):
    statement = select(Equipment).where(
        Equipment.id == equipment_id,
        Equipment.is_active.is_(True),
    )
    equipment = database.scalar(statement)

    if equipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    return equipment


@router.patch("/{equipment_id}", response_model=EquipmentRead)
def update_equipment(
    equipment_id: int,
    equipment_data: EquipmentUpdate,
    database: DatabaseSession,
    admin_user: AdminUser,
):
    equipment = database.get(Equipment, equipment_id)

    if equipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found",
        )

    for field_name, value in equipment_data.model_dump(exclude_unset=True).items():
        setattr(equipment, field_name, value)

    database.commit()
    database.refresh(equipment)
    return equipment
