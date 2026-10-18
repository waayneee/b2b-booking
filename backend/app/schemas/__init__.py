from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, date, time
from typing import Optional, List
from enum import Enum


class TimeOfDay(str, Enum):
    MORNING = "morning"      # 09:00-12:00
    AFTERNOON = "afternoon"  # 12:00-17:00
    EVENING = "evening"      # 17:00-21:00


# === Master Schemas ===
class MasterRegisterRequest(BaseModel):
    telegram_id: str
    first_name: str
    last_name: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    specialization: Optional[str] = None
    timezone: str = "UTC"


class MasterUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    specialization: Optional[str] = None
    timezone: Optional[str] = None


class MasterResponse(BaseModel):
    id: int
    telegram_id: str
    first_name: str
    last_name: Optional[str]
    phone: Optional[str]
    description: Optional[str]
    specialization: Optional[str]
    timezone: str
    registration_link_slug: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# === Service Schemas ===
class ServiceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    duration_minutes: int = Field(..., gt=0)
    price: Optional[float] = Field(None, ge=0)


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, gt=0)
    price: Optional[float] = Field(None, ge=0)


class ServiceResponse(BaseModel):
    id: int
    master_id: int
    name: str
    description: Optional[str]
    duration_minutes: int
    price: Optional[float]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# === Work Schedule Schemas ===
class WorkScheduleCreate(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6)  # 0=Monday, 6=Sunday
    start_time: time
    end_time: time


class WorkScheduleResponse(BaseModel):
    id: int
    master_id: int
    day_of_week: int
    start_time: time
    end_time: time
    is_active: bool

    class Config:
        from_attributes = True


# === Break Schemas ===
class BreakCreate(BaseModel):
    date: date
    start_time: time
    end_time: time
    reason: Optional[str] = None


class BreakResponse(BaseModel):
    id: int
    master_id: int
    date: date
    start_time: time
    end_time: time
    reason: Optional[str]

    class Config:
        from_attributes = True


# === Booking Schemas ===
class BookingCreate(BaseModel):
    service_id: int
    start_time: datetime
    client_phone: Optional[str] = None
    notes: Optional[str] = None


class BookingResponse(BaseModel):
    id: int
    master_id: int
    client_id: int
    service_id: int
    start_time: datetime
    end_time: datetime
    status: str
    client_phone: Optional[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class BookingCancelRequest(BaseModel):
    booking_id: int


# === Waitlist Schemas ===
class WaitlistAddRequest(BaseModel):
    service_id: int
    preferred_date_from: date
    preferred_date_to: date
    preferred_time: Optional[TimeOfDay] = None


class WaitlistResponse(BaseModel):
    id: int
    master_id: int
    client_id: int
    service_id: int
    preferred_date_from: date
    preferred_date_to: date
    preferred_time_start: Optional[time]
    preferred_time_end: Optional[time]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# === Client Schemas ===
class ClientResponse(BaseModel):
    id: int
    telegram_id: str
    first_name: str
    last_name: Optional[str]
    phone: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# === Available Slots Response ===
class TimeSlot(BaseModel):
    start_time: datetime
    end_time: datetime


class AvailableSlotsResponse(BaseModel):
    date: date
    slots: List[TimeSlot]
