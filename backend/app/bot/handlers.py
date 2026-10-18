from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import time
import logging
from app.config import settings
from app.database import async_session
from app.models import Master, Client
from sqlalchemy import select

logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


# FSM States
class MasterRegistration(StatesGroup):
    waiting_for_first_name = State()
    waiting_for_last_name = State()
    waiting_for_phone = State()
    waiting_for_description = State()
    waiting_for_specialization = State()
    waiting_for_timezone = State()


class ServiceCreation(StatesGroup):
    waiting_for_name = State()
    waiting_for_duration = State()
    waiting_for_price = State()


class ScheduleSetup(StatesGroup):
    waiting_for_day = State()
    waiting_for_start_time = State()
    waiting_for_end_time = State()


# Main menu keyboards
def get_master_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Услуги")],
            [KeyboardButton(text="⏰ График работы")],
            [KeyboardButton(text="📅 Мои записи")],
            [KeyboardButton(text="👥 Клиенты")],
            [KeyboardButton(text="🔗 Моя ссылка")],
            [KeyboardButton(text="⚙️ Настройки")],
        ],
        resize_keyboard=True,
    )


async def get_or_create_master(telegram_id: str, first_name: str) -> Master:
    async with async_session() as session:
        stmt = select(Master).where(Master.telegram_id == telegram_id)
        master = await session.scalar(stmt)

        if master:
            return master

        # Create new master
        import uuid
        slug = f"{first_name.lower()}-{str(uuid.uuid4())[:8]}"
        master = Master(
            telegram_id=telegram_id,
            first_name=first_name,
            registration_link_slug=slug,
        )
        session.add(master)
        await session.commit()
        return master


@dp.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext):
    """Handle /start command"""
    user_id = message.from_user.id
    user_first_name = message.from_user.first_name or "User"

    # For MVP, we'll treat all users as potential masters
    # Later we can add a choice screen
    async with async_session() as session:
        stmt = select(Master).where(Master.telegram_id == str(user_id))
        master = await session.scalar(stmt)

        if master:
            await message.answer(
                f"👋 Привет, {master.first_name}!\n\n"
                f"Добро пожаловать в сервис онлайн-записи.",
                reply_markup=get_master_menu(),
            )
        else:
            await message.answer(
                f"👋 Привет, {user_first_name}!\n\n"
                f"Давай зарегистрируем тебя как мастера.\n\n"
                f"Введи своё имя:",
            )
            await state.set_state(MasterRegistration.waiting_for_first_name)


@dp.message(MasterRegistration.waiting_for_first_name)
async def process_first_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await message.answer("Твоя фамилия (или пропусти):")
    await state.set_state(MasterRegistration.waiting_for_last_name)


@dp.message(MasterRegistration.waiting_for_last_name)
async def process_last_name(message: types.Message, state: FSMContext):
    await state.update_data(last_name=message.text if message.text != "пропусти" else None)
    await message.answer("Твой номер телефона (или пропусти):")
    await state.set_state(MasterRegistration.waiting_for_phone)


@dp.message(MasterRegistration.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text if message.text != "пропусти" else None)
    await message.answer("Расскажи о себе (описание услуг):")
    await state.set_state(MasterRegistration.waiting_for_description)


@dp.message(MasterRegistration.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Твоя специализация (например, 'Лэшмейкер'):")
    await state.set_state(MasterRegistration.waiting_for_specialization)


@dp.message(MasterRegistration.waiting_for_specialization)
async def process_specialization(message: types.Message, state: FSMContext):
    await state.update_data(specialization=message.text)
    await message.answer(
        "Временная зона (например, 'Europe/Moscow' или 'UTC'). "
        "По умолчанию UTC."
    )
    await state.set_state(MasterRegistration.waiting_for_timezone)


@dp.message(MasterRegistration.waiting_for_timezone)
async def process_timezone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    timezone = message.text if message.text != "пропусти" else "UTC"

    # Create master in database
    async with async_session() as session:
        import uuid
        first_name = data.get("first_name")
        slug = f"{first_name.lower()}-{str(uuid.uuid4())[:8]}"

        master = Master(
            telegram_id=str(message.from_user.id),
            first_name=first_name,
            last_name=data.get("last_name"),
            phone=data.get("phone"),
            description=data.get("description"),
            specialization=data.get("specialization"),
            timezone=timezone,
            registration_link_slug=slug,
        )
        session.add(master)
        await session.commit()

        await message.answer(
            f"✅ Регистрация завершена!\n\n"
            f"Твоя личная ссылка для клиентов:\n"
            f"https://yourapp.com/book/{slug}\n\n"
            f"Теперь давай настроим твои услуги и график работы.",
            reply_markup=get_master_menu(),
        )

    await state.clear()


@dp.message(F.text == "🔗 Моя ссылка")
async def show_link(message: types.Message):
    """Show master's booking link"""
    async with async_session() as session:
        stmt = select(Master).where(Master.telegram_id == str(message.from_user.id))
        master = await session.scalar(stmt)

        if not master:
            await message.answer("Ты ещё не зарегистрирован. Напиши /start")
            return

        await message.answer(
            f"🔗 Твоя ссылка для клиентов:\n\n"
            f"`https://yourapp.com/book/{master.registration_link_slug}`\n\n"
            f"Отправь её своим клиентам!",
            parse_mode="Markdown",
        )


@dp.message(F.text == "📋 Услуги")
async def manage_services(message: types.Message):
    """Show services management"""
    async with async_session() as session:
        stmt = select(Master).where(Master.telegram_id == str(message.from_user.id))
        master = await session.scalar(stmt)

        if not master:
            await message.answer("Ты ещё не зарегистрирован. Напиши /start")
            return

        # Show services list (TODO: implement full management)
        await message.answer(
            "📋 Управление услугами:\n\n"
            "Функция добавления услуг будет доступна в web-панели.\n\n"
            "API готов к использованию: POST /api/services",
        )


@dp.message(F.text == "⏰ График работы")
async def manage_schedule(message: types.Message):
    """Show schedule management"""
    async with async_session() as session:
        stmt = select(Master).where(Master.telegram_id == str(message.from_user.id))
        master = await session.scalar(stmt)

        if not master:
            await message.answer("Ты ещё не зарегистрирован. Напиши /start")
            return

        await message.answer(
            "⏰ Управление графиком работы:\n\n"
            "Функция доступна в web-панели.\n\n"
            "API готов: POST /api/work-schedules",
        )


@dp.message(F.text == "📅 Мои записи")
async def show_bookings(message: types.Message):
    """Show bookings for master"""
    async with async_session() as session:
        stmt = select(Master).where(Master.telegram_id == str(message.from_user.id))
        master = await session.scalar(stmt)

        if not master:
            await message.answer("Ты ещё не зарегистрирован. Напиши /start")
            return

        await message.answer(
            "📅 Твои записи:\n\n"
            "Полный список записей будет доступен в web-панели.",
        )


@dp.message(F.text == "👥 Клиенты")
async def show_clients(message: types.Message):
    """Show clients for master"""
    await message.answer("👥 Список клиентов будет доступен в web-панели.")


@dp.message(F.text == "⚙️ Настройки")
async def show_settings(message: types.Message):
    """Show settings"""
    await message.answer("⚙️ Настройки:\n\nТа затычка на потом.")


@dp.message()
async def echo(message: types.Message):
    """Echo handler"""
    await message.answer("Мне не понял 🤷‍♂️. Используй кнопки меню или напиши /start")


async def send_notification(telegram_id: str, message_text: str):
    """Send notification to user"""
    try:
        await bot.send_message(chat_id=telegram_id, text=message_text)
        logger.info(f"Notification sent to {telegram_id}")
    except Exception as e:
        logger.error(f"Failed to send notification to {telegram_id}: {e}")


async def start_bot():
    """Start polling"""
    logger.info("Bot started")
    await dp.start_polling(bot)


async def stop_bot():
    """Stop bot"""
    await bot.session.close()
