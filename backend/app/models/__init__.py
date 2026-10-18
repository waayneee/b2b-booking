from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Time, Date, Boolean, Float,
    ForeignKey, Enum as SQLEnum, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, time
import enum
from app.database import Base


class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class WaitlistStatus(str, enum.Enum):
    ACTIVE = "active"
    MATCHED = "matched"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class Master(Base):
    __tablename__ = "masters"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255))
    phone = Column(String(20))
    description = Column(Text)
    specialization = Column(String(255))
    timezone = Column(String(50), default="UTC")
    registration_link_slug = Column(String(255), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    services = relationship("Service", back_populates="master", cascade="all, delete-orphan")
    work_schedules = relationship("WorkSchedule", back_populates="master", cascade="all, delete-orphan")
    breaks = relationship("Break", back_populates="master", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="master", cascade="all, delete-orphan")
    waitlist_entries = relationship("Waitlist", back_populates="master", cascade="all, delete-orphan")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255))
    phone = Column(String(20))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    bookings = relationship("Booking", back_populates="client", cascade="all, delete-orphan")
    waitlist_entries = relationship("Waitlist", back_populates="client", cascade="all, delete-orphan")


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True)
    master_id = Column(Integer, ForeignKey("masters.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    duration_minutes = Column(Integer, nullable=False)  # Duration of service
    price = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_services_master_id", "master_id"),
        Index("ix_services_master_id_active", "master_id", "is_active"),
    )

    master = relationship("Master", back_populates="services")
    bookings = relationship("Booking", back_populates="service", cascade="all, delete-orphan")
    waitlist_entries = relationship("Waitlist", back_populates="service", cascade="all, delete-orphan")


class WorkSchedule(Base):
    __tablename__ = "work_schedules"

    id = Column(Integer, primary_key=True)
    master_id = Column(Integer, ForeignKey("masters.id"), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("master_id", "day_of_week", name="uq_master_day"),
        Index("ix_work_schedules_master_day", "master_id", "day_of_week"),
        CheckConstraint("start_time < end_time", name="ck_work_schedule_times"),
    )

    master = relationship("Master", back_populates="work_schedules")


class Break(Base):
    __tablename__ = "breaks"

    id = Column(Integer, primary_key=True)
    master_id = Column(Integer, ForeignKey("masters.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    reason = Column(String(255))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_breaks_master_date", "master_id", "date"),
        CheckConstraint("start_time < end_time", name="ck_break_times"),
    )

    master = relationship("Master", back_populates="breaks")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True)
    master_id = Column(Integer, ForeignKey("masters.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(SQLEnum(BookingStatus), default=BookingStatus.CONFIRMED, nullable=False)
    client_phone = Column(String(20))
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_bookings_master_date", "master_id", "start_time"),
        Index("ix_bookings_status", "status"),
        Index("ix_bookings_client", "client_id"),
        UniqueConstraint("master_id", "start_time", "end_time", name="uq_master_time_slot"),
        CheckConstraint("start_time < end_time", name="ck_booking_times"),
    )

    master = relationship("Master", back_populates="bookings")
    client = relationship("Client", back_populates="bookings")
    service = relationship("Service", back_populates="bookings")


class Waitlist(Base):
    __tablename__ = "waitlist"

    id = Column(Integer, primary_key=True)
    master_id = Column(Integer, ForeignKey("masters.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False, index=True)
    preferred_date_from = Column(Date, nullable=False)
    preferred_date_to = Column(Date, nullable=False)
    preferred_time_start = Column(Time)  # e.g., 09:00 for morning
    preferred_time_end = Column(Time)    # e.g., 12:00 for morning
    status = Column(SQLEnum(WaitlistStatus), default=WaitlistStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_waitlist_master_status", "master_id", "status"),
        Index("ix_waitlist_client", "client_id"),
        CheckConstraint("preferred_date_from <= preferred_date_to", name="ck_waitlist_dates"),
    )

    master = relationship("Master", back_populates="waitlist_entries")
    client = relationship("Client", back_populates="waitlist_entries")
    service = relationship("Service", back_populates="waitlist_entries")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    recipient_telegram_id = Column(String(50), nullable=False, index=True)
    notification_type = Column(String(50), nullable=False)  # new_booking, cancellation, etc.
    message = Column(Text, nullable=False)
    data = Column(String(1000))  # JSON with additional data
    sent_at = Column(DateTime)
    retry_count = Column(Integer, default=0)
    is_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_notifications_recipient_sent", "recipient_telegram_id", "is_sent"),
    )
