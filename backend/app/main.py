from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import uuid
import logging
import os

from app.config import settings
from app.database import get_db, init_db, close_db
from app.models import Master, Client, Service, WorkSchedule, Break, Booking, Waitlist
from app.schemas import (
    MasterRegisterRequest, MasterResponse, MasterUpdate,
    ServiceCreate, ServiceResponse, ServiceUpdate,
    WorkScheduleCreate, WorkScheduleResponse,
    BreakCreate, BreakResponse,
    BookingCreate, BookingResponse, BookingCancelRequest,
    WaitlistAddRequest, WaitlistResponse,
    AvailableSlotsResponse, TimeSlot,
)
from app.services.schedule import ScheduleService
from datetime import datetime, date

# Logging
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    debug=settings.DEBUG,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Lifecycle ===
@app.on_event("startup")
async def startup():
    await init_db()
    logger.info("Database initialized")


@app.on_event("shutdown")
async def shutdown():
    await close_db()
    logger.info("Database closed")


# === Health ===
@app.get("/health")
async def health():
    return {"status": "ok"}


# === Authentication Helpers ===
async def get_current_master(
    telegram_id: str,
    db: AsyncSession = Depends(get_db),
) -> Master:
    """Get current master from telegram_id"""
    stmt = select(Master).where(Master.telegram_id == telegram_id)
    master = await db.scalar(stmt)
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master not found",
        )
    return master


async def get_current_client(
    telegram_id: str,
    db: AsyncSession = Depends(get_db),
) -> Client:
    """Get or create client from telegram_id"""
    stmt = select(Client).where(Client.telegram_id == telegram_id)
    client = await db.scalar(stmt)
    if not client:
        # Create new client
        client = Client(
            telegram_id=telegram_id,
            first_name="User",
        )
        db.add(client)
        await db.flush()
    return client


# === Master Endpoints ===
@app.post("/api/masters/register", response_model=MasterResponse)
async def register_master(
    request: MasterRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new master"""
    # Check if already registered
    stmt = select(Master).where(Master.telegram_id == request.telegram_id)
    existing = await db.scalar(stmt)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Master already registered",
        )

    # Create registration link slug
    slug = f"{request.first_name.lower()}-{str(uuid.uuid4())[:8]}"

    master = Master(
        telegram_id=request.telegram_id,
        first_name=request.first_name,
        last_name=request.last_name,
        phone=request.phone,
        description=request.description,
        specialization=request.specialization,
        timezone=request.timezone,
        registration_link_slug=slug,
    )
    db.add(master)
    await db.commit()
    await db.refresh(master)
    return master


@app.get("/api/masters/me", response_model=MasterResponse)
async def get_master_profile(
    telegram_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get current master profile"""
    master = await get_current_master(telegram_id, db)
    return master


@app.put("/api/masters/me", response_model=MasterResponse)
async def update_master_profile(
    telegram_id: str,
    request: MasterUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update master profile"""
    master = await get_current_master(telegram_id, db)

    for key, value in request.dict(exclude_unset=True).items():
        setattr(master, key, value)

    await db.commit()
    await db.refresh(master)
    return master


@app.get("/api/masters/{slug}")
async def get_master_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Get master public profile by slug"""
    stmt = select(Master).where(Master.registration_link_slug == slug)
    master = await db.scalar(stmt)
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master not found",
        )
    return {
        "id": master.id,
        "first_name": master.first_name,
        "last_name": master.last_name,
        "description": master.description,
        "specialization": master.specialization,
        "slug": master.registration_link_slug,
    }


# === Service Endpoints ===
@app.post("/api/services", response_model=ServiceResponse)
async def create_service(
    telegram_id: str,
    request: ServiceCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new service"""
    master = await get_current_master(telegram_id, db)

    service = Service(
        master_id=master.id,
        name=request.name,
        description=request.description,
        duration_minutes=request.duration_minutes,
        price=request.price,
    )
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service


@app.get("/api/masters/{master_id}/services")
async def get_master_services(
    master_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all services for a master"""
    stmt = select(Service).where(
        and_(
            Service.master_id == master_id,
            Service.is_active == True,
        )
    )
    services = await db.scalars(stmt)
    return [
        ServiceResponse.from_orm(s).dict()
        for s in services
    ]


@app.put("/api/services/{service_id}", response_model=ServiceResponse)
async def update_service(
    telegram_id: str,
    service_id: int,
    request: ServiceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a service"""
    master = await get_current_master(telegram_id, db)

    service = await db.get(Service, service_id)
    if not service or service.master_id != master.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    for key, value in request.dict(exclude_unset=True).items():
        setattr(service, key, value)

    await db.commit()
    await db.refresh(service)
    return service


# === Work Schedule Endpoints ===
@app.post("/api/work-schedules", response_model=WorkScheduleResponse)
async def create_work_schedule(
    telegram_id: str,
    request: WorkScheduleCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create work schedule for a day"""
    master = await get_current_master(telegram_id, db)

    # Check if already exists
    stmt = select(WorkSchedule).where(
        and_(
            WorkSchedule.master_id == master.id,
            WorkSchedule.day_of_week == request.day_of_week,
        )
    )
    existing = await db.scalar(stmt)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Schedule already exists for this day",
        )

    schedule = WorkSchedule(
        master_id=master.id,
        day_of_week=request.day_of_week,
        start_time=request.start_time,
        end_time=request.end_time,
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)
    return schedule


@app.get("/api/masters/{master_id}/work-schedules")
async def get_work_schedules(
    master_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get work schedules for a master"""
    stmt = select(WorkSchedule).where(
        and_(
            WorkSchedule.master_id == master_id,
            WorkSchedule.is_active == True,
        )
    )
    schedules = await db.scalars(stmt)
    return [
        WorkScheduleResponse.from_orm(s).dict()
        for s in schedules
    ]


# === Break Endpoints ===
@app.post("/api/breaks", response_model=BreakResponse)
async def create_break(
    telegram_id: str,
    request: BreakCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a break in schedule"""
    master = await get_current_master(telegram_id, db)

    brk = Break(
        master_id=master.id,
        date=request.date,
        start_time=request.start_time,
        end_time=request.end_time,
        reason=request.reason,
    )
    db.add(brk)
    await db.commit()
    await db.refresh(brk)
    return brk


# === Booking Endpoints ===
@app.post("/api/bookings", response_model=BookingResponse)
async def create_booking(
    master_slug: str,
    telegram_id: str,
    request: BookingCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a booking (for clients)"""
    # Get master by slug
    master_stmt = select(Master).where(Master.registration_link_slug == master_slug)
    master = await db.scalar(master_stmt)
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master not found",
        )

    # Get or create client
    client = await get_current_client(telegram_id, db)

    # Create booking using schedule service
    try:
        booking = await ScheduleService.create_booking(
            db, master.id, client.id, request.service_id, request.start_time
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    booking.client_phone = request.client_phone
    booking.notes = request.notes

    await db.commit()
    await db.refresh(booking)
    return booking


@app.get("/api/available-slots/{master_slug}")
async def get_available_slots(
    master_slug: str,
    service_id: int,
    target_date: date,
    db: AsyncSession = Depends(get_db),
):
    """Get available slots for a service on a specific date"""
    # Get master
    master_stmt = select(Master).where(Master.registration_link_slug == master_slug)
    master = await db.scalar(master_stmt)
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master not found",
        )

    try:
        slots = await ScheduleService.get_available_slots(
            db, master.id, target_date, service_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return AvailableSlotsResponse(
        date=target_date,
        slots=[
            TimeSlot(start_time=start, end_time=end)
            for start, end in slots
        ],
    )


@app.get("/api/bookings")
async def get_bookings(
    telegram_id: str,
    role: str = "master",  # 'master' or 'client'
    db: AsyncSession = Depends(get_db),
):
    """Get bookings for current user"""
    if role == "master":
        master = await get_current_master(telegram_id, db)
        stmt = select(Booking).where(Booking.master_id == master.id)
    else:
        client = await get_current_client(telegram_id, db)
        stmt = select(Booking).where(Booking.client_id == client.id)

    bookings = await db.scalars(stmt)
    return [
        BookingResponse.from_orm(b).dict()
        for b in bookings
    ]


@app.post("/api/bookings/{booking_id}/cancel")
async def cancel_booking(
    booking_id: int,
    telegram_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Cancel a booking"""
    master = await get_current_master(telegram_id, db)

    try:
        booking = await ScheduleService.cancel_booking(db, booking_id, master.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    await db.commit()
    return BookingResponse.from_orm(booking)


@app.post("/api/bookings/{booking_id}/reschedule")
async def reschedule_booking(
    booking_id: int,
    telegram_id: str,
    new_start_time: datetime,
    db: AsyncSession = Depends(get_db),
):
    """Reschedule a booking"""
    master = await get_current_master(telegram_id, db)

    try:
        booking = await ScheduleService.reschedule_booking(
            db, booking_id, new_start_time, master.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    await db.commit()
    return BookingResponse.from_orm(booking)


# === Waitlist Endpoints ===
@app.post("/api/waitlist", response_model=WaitlistResponse)
async def add_to_waitlist(
    master_slug: str,
    telegram_id: str,
    request: WaitlistAddRequest,
    db: AsyncSession = Depends(get_db),
):
    """Add to waitlist"""
    # Get master
    master_stmt = select(Master).where(Master.registration_link_slug == master_slug)
    master = await db.scalar(master_stmt)
    if not master:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master not found",
        )

    # Get or create client
    client = await get_current_client(telegram_id, db)

    # Parse time preference
    if request.preferred_time:
        time_start, time_end = ScheduleService.get_time_range_for_preference(
            request.preferred_time
        )
    else:
        time_start, time_end = None, None

    entry = Waitlist(
        master_id=master.id,
        client_id=client.id,
        service_id=request.service_id,
        preferred_date_from=request.preferred_date_from,
        preferred_date_to=request.preferred_date_to,
        preferred_time_start=time_start,
        preferred_time_end=time_end,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


# === Static Files and Frontend ===
# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'static')
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/book/{master_slug}")
async def booking_page(master_slug: str):
    """Serve booking page for master"""
    template_path = os.path.join(
        os.path.dirname(__file__), '..', '..', 'frontend', 'templates', 'booking.html'
    )
    if os.path.exists(template_path):
        return FileResponse(template_path)
    raise HTTPException(status_code=404, detail="Booking page not found")


@app.get("/dashboard")
async def dashboard_page():
    """Serve master dashboard"""
    template_path = os.path.join(
        os.path.dirname(__file__), '..', '..', 'frontend', 'index.html'
    )
    if os.path.exists(template_path):
        return FileResponse(template_path)
    raise HTTPException(status_code=404, detail="Dashboard not found")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Booking Service API",
        "version": "1.0.0",
        "docs": "/docs",
        "api_prefix": "/api",
    }


# === Webhook for Telegram (optional, for future webhook mode) ===
@app.post(settings.WEBHOOK_PATH)
async def telegram_webhook(update: dict, db: AsyncSession = Depends(get_db)):
    """Receive updates from Telegram via webhook.

    Currently not used - bot uses polling mode.
    Can be enabled by setting TELEGRAM_WEBHOOK_URL in env.
    """
    logger.info(f"Webhook received: {update}")
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
