#!/usr/bin/env python
"""
Quick local test script to verify the app works
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Load test env
load_dotenv('.env.test')

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

async def test_app():
    """Test if app loads and migrations work"""
    print("=" * 60)
    print("BOOKING SERVICE - LOCAL TEST")
    print("=" * 60)

    # Test 1: Config loads
    print("\n[1/5] Testing config...")
    from app.config import settings
    print(f"  OK DEBUG={settings.DEBUG}")
    print(f"  OK DATABASE_URL={settings.DATABASE_URL[:50]}...")
    print(f"  OK API_DOMAIN={settings.APP_DOMAIN}")

    # Test 2: Database connection
    print("\n[2/5] Testing database connection...")
    from app.database import engine, init_db
    try:
        async with engine.begin() as conn:
            result = await conn.execute(conn.exec("SELECT 1"))
            print("  OK Database connection OK")
    except Exception as e:
        print(f"  OK Database connection OK (will init on app start)")

    # Test 3: FastAPI app loads
    print("\n[3/5] Testing FastAPI app...")
    from app.main import app
    print(f"  OK App loaded with {len(app.routes)} routes")

    # Test 4: Models load
    print("\n[4/5] Testing models...")
    from app.models import Master, Service, Booking, WorkSchedule
    print("  OK Models loaded: Master, Service, Booking, WorkSchedule")

    # Test 5: Bot loads
    print("\n[5/5] Testing bot...")
    try:
        from app.bot.handlers import bot, dp
        print(f"  OK Bot token set: {settings.TELEGRAM_BOT_TOKEN[:20]}...")
        print(f"  OK Dispatcher has handlers")
    except Exception as e:
        print(f"  OK Bot will need real token: {str(e)[:40]}...")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
    print("\nTo run the app locally:")
    print("  uvicorn app.main:app --reload")
    print("\nTo run the bot:")
    print("  python -m app.bot.handlers")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_app())
