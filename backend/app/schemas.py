from datetime import datetime, timezone
from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)

from backend.app.models import ReservationStatus, UserRole


class EquipmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    is_active: bool
    created_at: datetime


class EquipmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def normalize_name(cls, name: str) -> str:
        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError("Equipment name cannot be blank")

        return normalized_name


class EquipmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, name: str | None) -> str:
        if name is None:
            raise ValueError("Equipment name cannot be null")

        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError("Equipment name cannot be blank")

        return normalized_name

    @field_validator("is_active")
    @classmethod
    def require_active_state(cls, is_active: bool | None) -> bool:
        if is_active is None:
            raise ValueError("Active state cannot be null")

        return is_active

    @model_validator(mode="after")
    def require_at_least_one_change(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one equipment field is required")

        return self


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=200)
    password: SecretStr = Field(min_length=8, max_length=128)

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, full_name: str) -> str:
        normalized_name = full_name.strip()

        if not normalized_name:
            raise ValueError("Full name cannot be blank")

        return normalized_name


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ReservationTimeRange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    starts_at: datetime
    ends_at: datetime

    @field_validator("starts_at", "ends_at")
    @classmethod
    def require_timezone(cls, timestamp: datetime) -> datetime:
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("Reservation times must include a timezone")

        return timestamp.astimezone(timezone.utc)

    @model_validator(mode="after")
    def require_end_after_start(self) -> Self:
        if self.ends_at <= self.starts_at:
            raise ValueError("Reservation end must be after its start")

        return self


class EquipmentAvailabilityQuery(ReservationTimeRange):
    pass


class ReservationCreate(ReservationTimeRange):
    equipment_id: int = Field(gt=0)


class ReservationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    equipment_id: int
    starts_at: datetime
    ends_at: datetime
    status: ReservationStatus
    created_at: datetime
