# Deployment Guide - Booking Service

## 🎯 Deployment Overview

This guide covers deploying to cloud platforms. Current recommendation: **Render** (free tier + PostgreSQL, good for MVP).

## ☁️ Supported Platforms

| Platform | Database | Bot | Cost | Pros | Cons |
|----------|----------|-----|------|------|------|
| **Render** | PostgreSQL | Polling | Free tier available | Simple, integrated DB, good docs | Limited free tier |
| **Railway** | PostgreSQL | Polling | ~$5-10/mo | Easy deployments, clean UI | Pricing per service |
| **Fly.io** | PostgreSQL | Polling | ~$5-10/mo | Fast deploys, global regions | More complex setup |
| **Heroku** | PostgreSQL | Polling | ~~Free~~ (paid only) | Mature platform | Expensive |

## 🚀 Quick Deploy to Render

### Prerequisites
- GitHub account with this repo pushed
- Render account (render.com)
- Telegram bot token from @BotFather

### Step 1: Prepare Repository

```bash
# Ensure .env is in .gitignore (should be already)
grep ".env" .gitignore

# Push to GitHub
git push origin main
```

### Step 2: Create PostgreSQL Database on Render

1. Go to https://dashboard.render.com
2. Click "New +" → "PostgreSQL"
3. Fill in:
   - **Name**: `booking-db`
   - **Database**: `booking_db`
   - **User**: `booking_user`
   - **Region**: closest to your users
   - **PostgreSQL Version**: 16
4. Create and copy the connection string (looks like `postgresql://user:pass@host:port/dbname`)

### Step 3: Create Web Service on Render

1. Click "New +" → "Web Service"
2. Connect your GitHub repo
3. Fill in:
   - **Name**: `booking-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Click "Advanced" and add Environment Variables:

```
DATABASE_URL=postgresql://user:pass@host:port/dbname
TELEGRAM_BOT_TOKEN=your_token_here
API_DOMAIN=https://booking-api.onrender.com
SECRET_KEY=generate_random_string_here
DEBUG=False
```

5. Create service

### Step 4: Create Background Worker for Telegram Bot

1. Click "New +" → "Background Worker"
2. Connect same repo
3. Fill in:
   - **Name**: `booking-bot`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && python -m app.bot.handlers`
4. Add same Environment Variables as Web Service
5. Create service

### Step 5: Test Deployment

Wait 2-3 minutes for builds to complete, then:

```bash
# Test API health
curl https://booking-api.onrender.com/health

# Test API docs
open https://booking-api.onrender.com/docs

# Test master dashboard
open "https://booking-api.onrender.com/dashboard?telegram_id=123&slug=test"
```

### Step 6: Configure Telegram Bot

```bash
# Set webhook for production (optional, if you use webhook mode)
curl -X POST "https://api.telegram.org/botYOUR_TOKEN/setWebhook" \
  -d "url=https://booking-api.onrender.com/webhook"

# Or use polling (default) - bot already running in background worker
```

## 🔍 Monitoring After Deploy

### Check Logs

```bash
# Via Render dashboard
Dashboard → booking-api → Logs
Dashboard → booking-bot → Logs

# Or via CLI
render logs --service-id=your_service_id
```

### Common Issues

**1. Migrations fail**
```
Error: alembic upgrade head failed
```
**Fix**: Check DATABASE_URL in environment variables, ensure PostgreSQL is accessible

**2. Bot doesn't respond**
```
No messages in bot logs
```
**Fix**: 
- Verify TELEGRAM_BOT_TOKEN is valid (check @BotFather)
- Check bot logs for errors
- Restart background worker

**3. Bookings fail with 500 error**
```
POST /api/bookings returns 500
```
**Fix**: Check API logs, likely database or business logic error

**4. Frontend shows 404**
```
Booking page: 404 Not Found
```
**Fix**: Verify frontend HTML files are included in Docker/deployment

## 🗄️ Database Management

### Backup Production Data

```bash
# Download from Render dashboard
# Or via CLI
pg_dump postgresql://user:pass@host:port/dbname > backup.sql
```

### Restore Database

```bash
# If you need to restore
psql postgresql://user:pass@host:port/dbname < backup.sql
```

### Run Migrations in Production

Migrations run automatically on service start (see Start Command above). To manually trigger:

```bash
# Via Render Shell (if available)
cd backend && alembic upgrade head
```

## 📱 Telegram Bot Configuration

### For Polling Mode (Current)

No additional setup needed. Bot runs continuously in background worker.

### For Webhook Mode (Optional)

1. Update `config.py`:
```python
TELEGRAM_WEBHOOK_URL = "https://booking-api.onrender.com/webhook"
```

2. Set webhook:
```bash
curl -X POST "https://api.telegram.org/bot{TOKEN}/setWebhook" \
  -d "url=https://booking-api.onrender.com/webhook"
```

3. Bot handlers will receive updates via HTTP POST instead of polling

**Note**: Webhook requires valid HTTPS certificate (Render provides this automatically)

## 🔐 Security Checklist

Before going live:

- [ ] `SECRET_KEY` is strong random string (not placeholder)
- [ ] `DEBUG=False` in production
- [ ] Database password is strong
- [ ] `.env` is in `.gitignore`
- [ ] HTTPS enabled (automatic on Render)
- [ ] CORS configured appropriately
- [ ] Rate limiting enabled (TODO)
- [ ] Sensitive data not logged
- [ ] Telegram token not exposed in logs

## 📊 Performance & Scaling

### For MVP (< 1000 active masters)

Current setup is sufficient:
- Single Render web instance (0.5 CPU, 512MB RAM)
- Single PostgreSQL instance
- Single background worker for bot

### For Growth (1000+ masters)

Consider:
- Scale web service to multiple instances (auto-scaling)
- Add Redis for caching/sessions
- Separate bot into dedicated service (already done)
- Add database read replicas
- CDN for static files

## 🔄 CI/CD Pipeline

### GitHub Actions (Recommended)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Render

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Trigger Render Deploy
        run: |
          curl -X POST "${{ secrets.RENDER_DEPLOY_HOOK }}" \
            -H "Content-Type: application/json"
```

Get `RENDER_DEPLOY_HOOK` from Render dashboard (Settings → Deploy Hook)

## 📝 Environment Variables Reference

| Variable | Example | Required | Notes |
|----------|---------|----------|-------|
| `TELEGRAM_BOT_TOKEN` | `123:ABC...` | Yes | From @BotFather |
| `DATABASE_URL` | `postgresql://...` | Yes | Cloud DB connection |
| `API_DOMAIN` | `https://yourapp.com` | Yes | For booking links in bot |
| `SECRET_KEY` | Random string | Yes | Should be 32+ chars |
| `DEBUG` | `False` | Yes | Never `True` in production |
| `API_HOST` | `0.0.0.0` | No | Default: 0.0.0.0 |
| `API_PORT` | `8000` | No | Default: 8000 (set by platform) |

## 🛠️ Troubleshooting

### Service won't start

```bash
# Check Start Command syntax
# Common error: Missing `cd backend &&`
# Should be: cd backend && alembic upgrade head && uvicorn ...
```

### Database connection fails

```bash
# Verify DATABASE_URL format:
postgresql+asyncpg://user:password@host:port/dbname

# Ensure:
# - No spaces
# - Password is URL-encoded if it contains special chars
# - Host is Render's private IP (not localhost)
```

### Bot doesn't send messages

```bash
# Check if bot is running in background worker
# Verify TELEGRAM_BOT_TOKEN is valid
# Check logs for aiogram errors
# Ensure network allows outbound HTTPS to Telegram API
```

### High database latency

```bash
# Check active connections:
SELECT count(*) FROM pg_stat_activity;

# Add connection pooling (TODO)
# Consider read replicas for analytics queries
```

## 📞 Support

- **Render Docs**: https://render.com/docs
- **Telegram Bot API**: https://core.telegram.org/bots/api
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org

---

**Last Updated**: Oct 18, 2024  
**Status**: Production-ready for MVP  
**Next Steps**: Test on actual cloud platform, monitor performance, gather feedback
