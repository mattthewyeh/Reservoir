from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Equipment
from backend.app.schemas import EquipmentRead


router = APIRouter(prefix="/equipment", tags=["equipment"])
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[EquipmentRead])
def list_equipment(database: DatabaseSession):
    statement = (
        select(Equipment)
        .where(Equipment.is_active.is_(True))
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
