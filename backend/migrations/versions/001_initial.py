"""Initial migration - create all tables

Revision ID: 001_initial
Revises:
Create Date: 2024-10-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums
    op.execute("CREATE TYPE bookingstatus AS ENUM ('pending', 'confirmed', 'completed', 'cancelled')")
    op.execute("CREATE TYPE waitliststatus AS ENUM ('active', 'matched', 'cancelled', 'expired')")

    # Create masters table
    op.create_table(
        'masters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.String(length=50), nullable=False),
        sa.Column('first_name', sa.String(length=255), nullable=False),
        sa.Column('last_name', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('specialization', sa.String(length=255), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC'),
        sa.Column('registration_link_slug', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id', name='uq_masters_telegram_id'),
        sa.UniqueConstraint('registration_link_slug', name='uq_masters_slug'),
    )
    op.create_index('ix_masters_telegram_id', 'masters', ['telegram_id'])
    op.create_index('ix_masters_slug', 'masters', ['registration_link_slug'])

    # Create clients table
    op.create_table(
        'clients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.String(length=50), nullable=False),
        sa.Column('first_name', sa.String(length=255), nullable=False),
        sa.Column('last_name', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id', name='uq_clients_telegram_id'),
    )
    op.create_index('ix_clients_telegram_id', 'clients', ['telegram_id'])

    # Create services table
    op.create_table(
        'services',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('master_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['master_id'], ['masters.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_services_master_id', 'services', ['master_id'])
    op.create_index('ix_services_master_id_active', 'services', ['master_id', 'is_active'])

    # Create work_schedules table
    op.create_table(
        'work_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('master_id', sa.Integer(), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['master_id'], ['masters.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('master_id', 'day_of_week', name='uq_master_day'),
        sa.CheckConstraint('start_time < end_time', name='ck_work_schedule_times'),
    )
    op.create_index('ix_work_schedules_master_day', 'work_schedules', ['master_id', 'day_of_week'])

    # Create breaks table
    op.create_table(
        'breaks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('master_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['master_id'], ['masters.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('start_time < end_time', name='ck_break_times'),
    )
    op.create_index('ix_breaks_master_date', 'breaks', ['master_id', 'date'])

    # Create bookings table
    op.create_table(
        'bookings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('master_id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'confirmed', 'completed', 'cancelled', name='bookingstatus'), nullable=False, server_default='confirmed'),
        sa.Column('client_phone', sa.String(length=20), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.ForeignKeyConstraint(['master_id'], ['masters.id'], ),
        sa.ForeignKeyConstraint(['service_id'], ['services.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('master_id', 'start_time', 'end_time', name='uq_master_time_slot'),
        sa.CheckConstraint('start_time < end_time', name='ck_booking_times'),
    )
    op.create_index('ix_bookings_master_date', 'bookings', ['master_id', 'start_time'])
    op.create_index('ix_bookings_status', 'bookings', ['status'])
    op.create_index('ix_bookings_client', 'bookings', ['client_id'])

    # Create waitlist table
    op.create_table(
        'waitlist',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('master_id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=False),
        sa.Column('preferred_date_from', sa.Date(), nullable=False),
        sa.Column('preferred_date_to', sa.Date(), nullable=False),
        sa.Column('preferred_time_start', sa.Time(), nullable=True),
        sa.Column('preferred_time_end', sa.Time(), nullable=True),
        sa.Column('status', sa.Enum('active', 'matched', 'cancelled', 'expired', name='waitliststatus'), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.ForeignKeyConstraint(['master_id'], ['masters.id'], ),
        sa.ForeignKeyConstraint(['service_id'], ['services.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('preferred_date_from <= preferred_date_to', name='ck_waitlist_dates'),
    )
    op.create_index('ix_waitlist_master_status', 'waitlist', ['master_id', 'status'])
    op.create_index('ix_waitlist_client', 'waitlist', ['client_id'])

    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('recipient_telegram_id', sa.String(length=50), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('data', sa.String(length=1000), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notifications_recipient_sent', 'notifications', ['recipient_telegram_id', 'is_sent'])


def downgrade() -> None:
    op.drop_index('ix_notifications_recipient_sent', table_name='notifications')
    op.drop_table('notifications')
    op.drop_index('ix_waitlist_client', table_name='waitlist')
    op.drop_index('ix_waitlist_master_status', table_name='waitlist')
    op.drop_table('waitlist')
    op.drop_index('ix_bookings_client', table_name='bookings')
    op.drop_index('ix_bookings_status', table_name='bookings')
    op.drop_index('ix_bookings_master_date', table_name='bookings')
    op.drop_table('bookings')
    op.drop_index('ix_breaks_master_date', table_name='breaks')
    op.drop_table('breaks')
    op.drop_index('ix_work_schedules_master_day', table_name='work_schedules')
    op.drop_table('work_schedules')
    op.drop_index('ix_services_master_id_active', table_name='services')
    op.drop_index('ix_services_master_id', table_name='services')
    op.drop_table('services')
    op.drop_index('ix_clients_telegram_id', table_name='clients')
    op.drop_table('clients')
    op.drop_index('ix_masters_slug', table_name='masters')
    op.drop_index('ix_masters_telegram_id', table_name='masters')
    op.drop_table('masters')
    op.execute("DROP TYPE IF EXISTS waitliststatus")
    op.execute("DROP TYPE IF EXISTS bookingstatus")
