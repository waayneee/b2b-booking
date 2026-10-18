# B2B Booking Service - Project Documentation

## 🎯 Project Overview

Multi-master booking service for beauty professionals (lash makers, eyebrow artists, manicurists, hairdressers) to manage schedules and accept client appointments through Telegram.

**Current Status**: MVP with core API, modern UI, and local testing infrastructure ready.

## 🏗️ Architecture

### Backend
- **Framework**: FastAPI + SQLAlchemy 2.0 (async)
- **Database**: PostgreSQL (production) / SQLite (testing)
- **Migrations**: Alembic
- **Bot**: aiogram 3 (Telegram)
- **Async**: asyncpg driver for PostgreSQL

### Frontend
- **Client Booking**: Modern HTML5/JS with Telegram Mini App support
- **Master Dashboard**: Responsive web interface for schedule & booking management
- **Design**: Mobile-first, safe-area aware for Telegram integration

### Deployment
- **Container**: Docker & Docker Compose
- **Target**: Cloud (Render, Railway, Heroku, or similar)

## 📁 Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application & routes
│   ├── config.py            # Settings & environment config
│   ├── database.py          # SQLAlchemy setup
│   ├── models/              # ORM models
│   ├── schemas/             # Pydantic validators
│   ├── services/
│   │   └── schedule.py      # Core booking & slot logic
│   └── bot/
│       └── handlers.py      # Telegram bot handlers
├── migrations/              # Alembic migrations
├── tests/                   # Pytest test suite
├── requirements.txt         # Dependencies
├── .env.example             # Config template
└── Dockerfile               # Container image

frontend/
├── index.html               # Master dashboard
├── templates/
│   └── booking.html         # Client booking Mini App
└── static/
    ├── css/                 # Styling
    └── js/                  # Frontend logic
```

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- pip / venv

### 1. Setup

```bash
# Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Create .env from example
cp .env.example .env
# Edit .env and set:
# - TELEGRAM_BOT_TOKEN=your_token_from_botfather
```

### 2. Database Setup

**Option A: SQLite (for local testing)**
```bash
# Already configured in .env.test
export $(cat .env.test | xargs)
```

**Option B: PostgreSQL**
```bash
# Run PostgreSQL container
docker run --name booking-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=booking_db \
  -p 5432:5432 -d postgres:16-alpine

# Apply migrations
alembic upgrade head
```

### 3. Run Application

```bash
# Terminal 1: FastAPI server
uvicorn app.main:app --reload

# Terminal 2: Telegram bot (requires valid token)
python -m app.bot.handlers

# Terminal 3 (optional): Test script
python test_local.py
```

### 4. Access

- API docs: http://localhost:8000/docs
- Master dashboard: http://localhost:8000/dashboard?telegram_id=123456&slug=anna-a1b2c3d4
- Booking page: http://localhost:8000/book/anna-a1b2c3d4

## 📊 Core Features

### Master Features
- ✅ Telegram registration with auto-generated booking link
- ✅ Service management (name, price, duration)
- ✅ Work schedule per day of week
- ✅ Breaks & exceptions
- ✅ View all bookings
- ✅ Cancel & reschedule bookings
- ✅ Master dashboard with stats
- ✅ Dynamic booking link in bot

### Client Features
- ✅ Open booking link from Telegram
- ✅ View master profile & services
- ✅ Select service, date, time
- ✅ Confirm booking with contact info
- ✅ View own bookings
- ✅ Cancel/reschedule (per master rules)
- 🟡 Waitlist (MVP version implemented, unotifications TBD)

### Critical Business Logic
- ✅ Slot availability with service duration
- ✅ Double-booking prevention (DB unique constraint)
- ✅ Timezone awareness
- ✅ Work schedule & breaks enforcement
- ✅ Atomic transactions

## 🔐 Security

### Implemented
- ✅ Master authorization via telegram_id
- ✅ Data isolation per master
- ✅ Unique constraints prevent double-booking
- ✅ No secrets in Git (.env in .gitignore)
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ Production-ready CORS config

### TODO
- ⚠️ Telegram Mini App `initData` validation (server-side)
- ⚠️ Rate limiting on sensitive endpoints
- ⚠️ HTTPS + domain setup for Telegram
- ⚠️ Webhook signature validation

## 🗄️ Database Schema

- **masters**: Base user with auto-generated booking slug
- **services**: Master's offerings with price & duration
- **work_schedules**: Weekly schedule per day
- **breaks**: Specific date/time blocks off
- **bookings**: Client appointments (with unique constraint on master_id, start_time, end_time)
- **clients**: Client contact info
- **waitlist**: Queue for unavailable times
- **notifications**: Message queue for Telegram

## 🧪 Testing

```bash
# Run existing tests
pytest tests/ -v

# Run local validation
python test_local.py
```

Tests verify:
- Double-booking prevention
- Schedule conflicts
- Timezone handling
- Data isolation

## 🐳 Docker & Cloud Deployment

### Local Docker Compose

```bash
docker-compose up -d
# Automatically:
# - Creates PostgreSQL container
# - Runs migrations
# - Starts FastAPI server
# - Sets health checks
```

### Environment Variables (Production)

```
TELEGRAM_BOT_TOKEN=<token_from_botfather>
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/booking_db
API_DOMAIN=https://yourdomain.com
SECRET_KEY=<strong-random-key>
DEBUG=False
```

### Deployment Checklist

- [ ] Domain configured
- [ ] HTTPS certificates ready
- [ ] PostgreSQL provisioned (persistent)
- [ ] Environment variables set
- [ ] Migrations auto-run before app start
- [ ] Bot starts via separate process or webhook
- [ ] Health check endpoint `/health` returns 200
- [ ] Logs redirected to cloud provider's system

## 🚨 Known Limitations

- No payment processing (ready for integration)
- Waitlist sends one notification per available slot
- No analytics/reports yet
- No automatic reminders (needs background task scheduler)
- No rating system
- Telegram Mini App requires real HTTPS domain

## 📝 API Examples

### Register Master
```bash
curl -X POST http://localhost:8000/api/masters/register \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_id": "123456789",
    "first_name": "Anna",
    "specialization": "Lash Artist",
    "timezone": "Europe/Moscow"
  }'
```

### Create Service
```bash
curl -X POST http://localhost:8000/api/services \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_id": "123456789",
    "name": "Lash Extensions",
    "duration_minutes": 120,
    "price": 2500
  }'
```

### Get Available Slots
```bash
curl "http://localhost:8000/api/available-slots/anna-a1b2c3d4?service_id=1&target_date=2024-10-21"
```

### Create Booking
```bash
curl -X POST http://localhost:8000/api/bookings \
  -H "Content-Type: application/json" \
  -d '{
    "master_slug": "anna-a1b2c3d4",
    "telegram_id": "987654321",
    "service_id": 1,
    "start_time": "2024-10-21T10:00:00",
    "client_phone": "+79991234567"
  }'
```

## 🔧 Maintenance

### Migrations
```bash
# Create new migration
alembic revision -m "Description"

# Auto-create (if schema changes)
alembic revision --autogenerate -m "Description"

# Apply
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Database Backup (Production)
```bash
# PostgreSQL dump
pg_dump booking_db > backup.sql

# Restore
psql booking_db < backup.sql
```

### Monitoring

Key endpoints to watch:
- `GET /health` - Server health
- `GET /docs` - API documentation
- Telegram webhook status (if using webhook mode)

## 🎓 Key Design Decisions

1. **Async SQLAlchemy**: Handles concurrent bookings safely
2. **Unique constraint on (master_id, start_time, end_time)**: DB-level double-booking prevention
3. **Timezone-aware timestamps**: Supports global masters
4. **Work schedule per day-of-week**: Simplifies recurring patterns
5. **Soft delete via status enum**: Preserves audit trail
6. **Polling over webhook for bot**: Easier local dev, simpler infrastructure

## 📞 Support & Development

- See README.md for quick start
- See API_EXAMPLES.md for detailed API reference
- Check logs for errors: `docker-compose logs backend`
- Database issues: `docker-compose logs db`

---

**Last Updated**: Oct 18, 2024  
**Version**: 1.0.0-MVP  
**Maintainer**: Development Team
