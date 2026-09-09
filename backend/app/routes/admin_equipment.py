from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Equipment
from backend.app.schemas import EquipmentRead
from backend.app.security import AdminUser


router = APIRouter(prefix="/admin/equipment", tags=["admin equipment"])
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[EquipmentRead])
def list_all_equipment(
    database: DatabaseSession,
    admin_user: AdminUser,
):
    statement = select(Equipment).order_by(Equipment.name, Equipment.id)
    return list(database.scalars(statement))
