import pytest
import pytest_asyncio
from datetime import datetime, date, time, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.database import Base
from app.models import Master, Client, Service, WorkSchedule, Booking, BookingStatus
from app.services.schedule import ScheduleService
import pytz


# Test database setup
@pytest_asyncio.fixture
async def test_db():
    """Create test database"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    yield async_session

    await engine.dispose()


@pytest_asyncio.fixture
async def session(test_db):
    """Get test session"""
    async with test_db() as s:
        yield s


@pytest_asyncio.fixture
async def master(session: AsyncSession):
    """Create test master"""
    master = Master(
        telegram_id="123456789",
        first_name="Анна",
        specialization="Лэшмейкер",
        timezone="Europe/Moscow",
        registration_link_slug="anna-test",
    )
    session.add(master)
    await session.flush()
    return master


@pytest_asyncio.fixture
async def service(session: AsyncSession, master: Master):
    """Create test service"""
    service = Service(
        master_id=master.id,
        name="Наращивание ресниц",
        duration_minutes=120,
        price=2500.0,
    )
    session.add(service)
    await session.flush()
    return service


@pytest_asyncio.fixture
async def work_schedule(session: AsyncSession, master: Master):
    """Create work schedule"""
    # Monday to Friday, 10:00 - 20:00
    for day in range(5):
        schedule = WorkSchedule(
            master_id=master.id,
            day_of_week=day,
            start_time=time(10, 0),
            end_time=time(20, 0),
        )
        session.add(schedule)
    await session.flush()


@pytest_asyncio.fixture
async def client(session: AsyncSession):
    """Create test client"""
    client = Client(
        telegram_id="987654321",
        first_name="Клиент",
    )
    session.add(client)
    await session.flush()
    return client


# Tests
@pytest.mark.asyncio
async def test_master_registration(session: AsyncSession):
    """Test master registration"""
    master = Master(
        telegram_id="test123",
        first_name="Тест",
        timezone="UTC",
        registration_link_slug="test-slug",
    )
    session.add(master)
    await session.commit()

    # Verify
    from sqlalchemy import select
    stmt = select(Master).where(Master.telegram_id == "test123")
    found = await session.scalar(stmt)

    assert found is not None
    assert found.first_name == "Тест"
    assert found.timezone == "UTC"


@pytest.mark.asyncio
async def test_get_available_slots(
    session: AsyncSession,
    master: Master,
    service: Service,
    work_schedule: WorkSchedule,
):
    """Test available slots calculation"""
    # Get Monday's available slots
    from datetime import datetime, date
    import pytz

    tz = pytz.timezone("Europe/Moscow")
    target_date = date(2024, 10, 21)  # A Monday

    slots = await ScheduleService.get_available_slots(
        session, master.id, target_date, service.id
    )

    assert len(slots) > 0
    # Should have slots from 10:00 to 20:00 in 30-minute increments for a 2-hour service
    # (20:00 - 10:00 - 2:00 service) * 2 slots per hour = ~20 slots
    assert len(slots) >= 10


@pytest.mark.asyncio
async def test_double_booking_protection(
    session: AsyncSession,
    master: Master,
    service: Service,
    work_schedule: WorkSchedule,
    client: Client,
):
    """Test protection against double booking"""
    import pytz
    from datetime import datetime

    tz = pytz.timezone("Europe/Moscow")
    target_date = date(2024, 10, 21)
    start_time = datetime(2024, 10, 21, 10, 0)
    start_time = tz.localize(start_time)

    # Create first booking
    booking1 = await ScheduleService.create_booking(
        session, master.id, client.id, service.id, start_time
    )
    await session.commit()

    assert booking1 is not None

    # Try to create overlapping booking
    with pytest.raises(ValueError, match="not available"):
        await ScheduleService.create_booking(
            session, master.id, client.id, service.id, start_time
        )


@pytest.mark.asyncio
async def test_booking_respects_schedule(
    session: AsyncSession,
    master: Master,
    service: Service,
    work_schedule: WorkSchedule,
    client: Client,
):
    """Test that booking respects work schedule"""
    # Try to book before work hours
    tz = pytz.timezone("Europe/Moscow")
    target_date = date(2024, 10, 21)
    start_time = datetime(2024, 10, 21, 8, 0)  # 08:00, before 10:00 start
    start_time = tz.localize(start_time)

    with pytest.raises(ValueError):
        await ScheduleService.create_booking(
            session, master.id, client.id, service.id, start_time
        )


@pytest.mark.asyncio
async def test_booking_respects_service_duration(
    session: AsyncSession,
    master: Master,
    service: Service,
    work_schedule: WorkSchedule,
):
    """Test that booking end time = start time + service duration"""
    tz = pytz.timezone("Europe/Moscow")
    target_date = date(2024, 10, 21)

    slots = await ScheduleService.get_available_slots(
        session, master.id, target_date, service.id
    )

    assert len(slots) > 0
    first_slot_start, first_slot_end = slots[0]

    # Duration should be 120 minutes (2 hours)
    duration = (first_slot_end - first_slot_start).total_seconds() / 60
    assert duration == 120


@pytest.mark.asyncio
async def test_cancel_booking(
    session: AsyncSession,
    master: Master,
    service: Service,
    work_schedule: WorkSchedule,
    client: Client,
):
    """Test booking cancellation"""
    tz = pytz.timezone("Europe/Moscow")
    start_time = datetime(2024, 10, 21, 10, 0)
    start_time = tz.localize(start_time)

    # Create booking
    booking = await ScheduleService.create_booking(
        session, master.id, client.id, service.id, start_time
    )
    await session.commit()

    # Cancel it
    cancelled = await ScheduleService.cancel_booking(session, booking.id, master.id)
    assert cancelled.status == BookingStatus.CANCELLED


@pytest.mark.asyncio
async def test_reschedule_booking(
    session: AsyncSession,
    master: Master,
    service: Service,
    work_schedule: WorkSchedule,
    client: Client,
):
    """Test booking rescheduling"""
    tz = pytz.timezone("Europe/Moscow")
    start_time = datetime(2024, 10, 21, 10, 0)
    start_time = tz.localize(start_time)

    # Create booking
    booking = await ScheduleService.create_booking(
        session, master.id, client.id, service.id, start_time
    )
    await session.commit()

    # Reschedule to later
    new_start_time = datetime(2024, 10, 21, 14, 0)
    new_start_time = tz.localize(new_start_time)

    rescheduled = await ScheduleService.reschedule_booking(
        session, booking.id, new_start_time, master.id
    )

    assert rescheduled.start_time == new_start_time
    assert (rescheduled.end_time - rescheduled.start_time).total_seconds() == 2 * 60 * 60


@pytest.mark.asyncio
async def test_no_overlapping_bookings(
    session: AsyncSession,
    master: Master,
    service: Service,
    work_schedule: WorkSchedule,
    client: Client,
):
    """Test that no overlapping bookings are allowed"""
    tz = pytz.timezone("Europe/Moscow")

    # Create first booking at 10:00-12:00
    start_time1 = datetime(2024, 10, 21, 10, 0)
    start_time1 = tz.localize(start_time1)
    booking1 = await ScheduleService.create_booking(
        session, master.id, client.id, service.id, start_time1
    )
    await session.commit()

    # Try to create overlapping booking at 11:00-13:00
    start_time2 = datetime(2024, 10, 21, 11, 0)
    start_time2 = tz.localize(start_time2)

    with pytest.raises(ValueError):
        await ScheduleService.create_booking(
            session, master.id, client.id, service.id, start_time2
        )
