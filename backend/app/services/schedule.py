from datetime import datetime, timedelta, date, time
from typing import List, Optional, Tuple
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.models import (
    Master, Service, WorkSchedule, Break, Booking, Waitlist,
    BookingStatus, WaitlistStatus
)
import pytz


class ScheduleService:
    """Core scheduling logic for calculating available slots and managing bookings."""

    @staticmethod
    def get_time_range_for_preference(preferred_time: Optional[str]) -> Tuple[time, time]:
        """Convert time preference to time range.

        Args:
            preferred_time: 'morning', 'afternoon', 'evening', or None

        Returns:
            Tuple of (start_time, end_time)
        """
        preferences = {
            'morning': (time(9, 0), time(12, 0)),
            'afternoon': (time(12, 0), time(17, 0)),
            'evening': (time(17, 0), time(21, 0)),
        }
        return preferences.get(preferred_time, (time(0, 0), time(23, 59)))

    @staticmethod
    async def get_available_slots(
        session: AsyncSession,
        master_id: int,
        date_: date,
        service_id: int,
    ) -> List[Tuple[datetime, datetime]]:
        """Get available time slots for a specific date.

        This is the core logic for availability calculation.

        Args:
            session: Database session
            master_id: ID of the master
            date_: Target date
            service_id: Service ID (for duration)

        Returns:
            List of (start_datetime, end_datetime) tuples for available slots

        Raises:
            ValueError: If master or service not found
        """
        # Get service duration
        service_stmt = select(Service).where(Service.id == service_id)
        service = await session.scalar(service_stmt)
        if not service:
            raise ValueError(f"Service {service_id} not found")

        # Get master timezone
        master_stmt = select(Master).where(Master.id == master_id)
        master = await session.scalar(master_stmt)
        if not master:
            raise ValueError(f"Master {master_id} not found")

        # Get work schedule for this day of week
        day_of_week = date_.weekday()
        schedule_stmt = select(WorkSchedule).where(
            and_(
                WorkSchedule.master_id == master_id,
                WorkSchedule.day_of_week == day_of_week,
                WorkSchedule.is_active == True,
            )
        )
        schedule = await session.scalar(schedule_stmt)
        if not schedule:
            return []  # No work on this day

        # Get all breaks for this date
        breaks_stmt = select(Break).where(
            and_(
                Break.master_id == master_id,
                Break.date == date_,
            )
        )
        breaks_result = await session.scalars(breaks_stmt)
        breaks = list(breaks_result)

        # Get all bookings for this date (confirmed and pending)
        bookings_stmt = select(Booking).where(
            and_(
                Booking.master_id == master_id,
                func.date(Booking.start_time) == date_,
                Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING]),
            )
        )
        bookings_result = await session.scalars(bookings_stmt)
        bookings = list(bookings_result)

        # Build list of occupied intervals
        occupied_intervals = []

        # Add breaks
        tz = pytz.timezone(master.timezone)
        for brk in breaks:
            start_dt = datetime.combine(date_, brk.start_time)
            start_dt = tz.localize(start_dt)
            end_dt = datetime.combine(date_, brk.end_time)
            end_dt = tz.localize(end_dt)
            occupied_intervals.append((start_dt, end_dt))

        # Add existing bookings
        for booking in bookings:
            occupied_intervals.append((booking.start_time, booking.end_time))

        # Generate potential slots
        work_start = datetime.combine(date_, schedule.start_time)
        work_end = datetime.combine(date_, schedule.end_time)
        work_start = tz.localize(work_start)
        work_end = tz.localize(work_end)

        service_duration = timedelta(minutes=service.duration_minutes)
        available_slots = []

        current = work_start
        while current + service_duration <= work_end:
            slot_end = current + service_duration

            # Check if this slot intersects with any occupied interval
            is_available = True
            for occ_start, occ_end in occupied_intervals:
                if not (slot_end <= occ_start or current >= occ_end):
                    is_available = False
                    break

            if is_available:
                available_slots.append((current, slot_end))

            current += timedelta(minutes=30)  # 30-minute slot increments

        return available_slots

    @staticmethod
    async def create_booking(
        session: AsyncSession,
        master_id: int,
        client_id: int,
        service_id: int,
        start_time: datetime,
    ) -> Booking:
        """Create a booking with transaction protection against double-booking.

        This uses database-level constraints to prevent race conditions.

        Args:
            session: Database session (should be in transaction)
            master_id: ID of the master
            client_id: ID of the client
            service_id: ID of the service
            start_time: Desired start time (datetime)

        Returns:
            Created Booking object

        Raises:
            ValueError: If the time slot is not available
            IntegrityError: If unique constraint is violated (double-booking)
        """
        # Verify availability one more time
        service = await session.get(Service, service_id)
        if not service:
            raise ValueError("Service not found")

        available_slots = await ScheduleService.get_available_slots(
            session, master_id, start_time.date(), service_id
        )

        # Check if requested time is in available slots
        slot_found = False
        for slot_start, slot_end in available_slots:
            if slot_start == start_time:
                slot_found = True
                end_time = slot_end
                break

        if not slot_found:
            raise ValueError("Selected time slot is not available")

        # Create booking
        booking = Booking(
            master_id=master_id,
            client_id=client_id,
            service_id=service_id,
            start_time=start_time,
            end_time=end_time,
            status=BookingStatus.CONFIRMED,
        )

        session.add(booking)

        try:
            await session.flush()  # Flush to check constraints
        except IntegrityError as e:
            await session.rollback()
            raise ValueError("Time slot is already booked") from e

        return booking

    @staticmethod
    async def cancel_booking(
        session: AsyncSession,
        booking_id: int,
        master_id: int,
    ) -> Booking:
        """Cancel a booking and update its status.

        Args:
            session: Database session
            booking_id: ID of booking to cancel
            master_id: Master ID (for authorization check)

        Returns:
            Updated Booking object

        Raises:
            ValueError: If booking not found or doesn't belong to master
        """
        booking = await session.get(Booking, booking_id)
        if not booking:
            raise ValueError("Booking not found")

        if booking.master_id != master_id:
            raise ValueError("Booking does not belong to this master")

        if booking.status == BookingStatus.CANCELLED:
            raise ValueError("Booking is already cancelled")

        booking.status = BookingStatus.CANCELLED
        await session.flush()

        return booking

    @staticmethod
    async def reschedule_booking(
        session: AsyncSession,
        booking_id: int,
        new_start_time: datetime,
        master_id: int,
    ) -> Booking:
        """Reschedule a booking to a new time.

        Args:
            session: Database session
            booking_id: ID of booking
            new_start_time: New start time
            master_id: Master ID (for authorization)

        Returns:
            Updated Booking object

        Raises:
            ValueError: If booking not found or new time is unavailable
        """
        booking = await session.get(Booking, booking_id)
        if not booking:
            raise ValueError("Booking not found")

        if booking.master_id != master_id:
            raise ValueError("Booking does not belong to this master")

        # Verify new slot availability
        available_slots = await ScheduleService.get_available_slots(
            session, master_id, new_start_time.date(), booking.service_id
        )

        slot_found = False
        for slot_start, slot_end in available_slots:
            if slot_start == new_start_time:
                slot_found = True
                new_end_time = slot_end
                break

        if not slot_found:
            raise ValueError("New time slot is not available")

        # Update booking
        booking.start_time = new_start_time
        booking.end_time = new_end_time
        await session.flush()

        return booking
