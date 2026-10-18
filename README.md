# 📅 Booking Bot MVP - Telegram-сервис онлайн-записи

Полнофункциональный MVP сервиса для онлайн-записи к мастерам через Telegram.

## 🎯 Возможности

- ✅ Регистрация мастеров с персональной ссылкой
- ✅ Управление услугами, ценами и длительностью
- ✅ Гибкий график работы (дни, часы, перерывы)
- ✅ Вычисление доступных слотов с учётом графика
- ✅ Безопасное бронирование (защита от двойного бронирования)
- ✅ Уведомления в Telegram
- ✅ Отмена и перенос записей
- ✅ Лист ожидания и автоматические уведомления
- ✅ PostgreSQL для надёжного хранения данных

## 🏗️ Технологический стек

- **Backend**: FastAPI + SQLAlchemy 2.0
- **БД**: PostgreSQL с асинхронным драйвером
- **Bot**: aiogram 3
- **Миграции**: Alembic
- **Контейнеризация**: Docker Compose
- **Tests**: pytest + pytest-asyncio

## 📋 Требования

- Docker и Docker Compose
- Либо: Python 3.12+, PostgreSQL 14+

## 🚀 Быстрый старт (Docker)

### 1. Получить токен Telegram бота

1. Откройте Telegram и найдите `@BotFather`
2. Отправьте команду `/newbot`
3. Дайте имя и username своему боту
4. Скопируйте полученный токен

### 2. Подготовить окружение

```bash
cd backend
cp .env.example .env
```

Отредактируйте `.env`:
```
TELEGRAM_BOT_TOKEN=your_token_here
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/booking_db
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
```

### 3. Запустить через Docker Compose

```bash
cd /path/to/project
docker-compose up -d
```

Сервис будет доступен по адресу `http://localhost:8000`

Проверить здоровье:
```bash
curl http://localhost:8000/health
```

## 🖥️ Запуск локально (Windows)

### 1. Установить зависимости

```bash
# Создать виртуальное окружение
python -m venv venv

# Активировать
venv\Scripts\activate

# Установить зависимости
pip install -r backend/requirements.txt
```

### 2. Запустить PostgreSQL

Вариант 1: Установить PostgreSQL локально
- Скачайте с [postgresql.org](https://www.postgresql.org/download/windows/)
- При установке запомните пароль для пользователя `postgres`
- Создайте базу данных:
  ```bash
  psql -U postgres -c "CREATE DATABASE booking_db;"
  ```

Вариант 2: Использовать Docker только для БД
```bash
docker run --name booking-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=booking_db -p 5432:5432 -d postgres:16-alpine
```

### 3. Применить миграции

```bash
cd backend
alembic upgrade head
```

### 4. Запустить FastAPI сервер

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Сервис будет доступен по `http://localhost:8000`

### 5. Запустить Telegram бота (отдельный терминал)

```bash
# В папке backend/
python -m app.bot.handlers
```

## 📚 API Endpoints

### Для мастеров

```
POST   /api/masters/register              - Регистрация мастера
GET    /api/masters/me                    - Получить профиль
PUT    /api/masters/me                    - Обновить профиль
POST   /api/services                      - Создать услугу
PUT    /api/services/{id}                 - Обновить услугу
GET    /api/masters/{id}/services         - Список услуг
POST   /api/work-schedules                - Создать график
GET    /api/masters/{id}/work-schedules   - Получить график
POST   /api/breaks                        - Создать перерыв
GET    /api/bookings                      - Мои записи
POST   /api/bookings/{id}/cancel          - Отменить запись
POST   /api/bookings/{id}/reschedule      - Перенести запись
```

### Для клиентов

```
GET    /api/masters/{slug}                - Профиль мастера по ссылке
GET    /api/masters/{id}/services         - Услуги мастера
GET    /api/available-slots/{slug}        - Доступные слоты
POST   /api/bookings                      - Создать бронирование
POST   /api/waitlist                      - Добавиться в лист ожидания
GET    /api/bookings                      - Мои записи
```

## 🧪 Тестирование

```bash
cd backend
pytest tests/ -v
```

Тесты проверяют:
- Защита от двойного бронирования
- Соблюдение графика работы
- Длительность услуги
- Отмену и перенос записей
- Отсутствие пересекающихся бронирований

## 📝 Пример использования API

### 1. Зарегистрировать мастера

```bash
curl -X POST http://localhost:8000/api/masters/register \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_id": "123456789",
    "first_name": "Анна",
    "last_name": "Сергеева",
    "specialization": "Лэшмейкер",
    "timezone": "Europe/Moscow"
  }'
```

Ответ:
```json
{
  "id": 1,
  "telegram_id": "123456789",
  "first_name": "Анна",
  "specialization": "Лэшмейкер",
  "registration_link_slug": "anna-a1b2c3d4",
  "timezone": "Europe/Moscow",
  "created_at": "2024-10-18T12:00:00"
}
```

### 2. Создать услугу

```bash
curl -X POST http://localhost:8000/api/services \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_id": "123456789",
    "name": "Наращивание ресниц",
    "duration_minutes": 120,
    "price": 2500
  }'
```

### 3. Установить график работы

```bash
# Понедельник (день 0)
curl -X POST http://localhost:8000/api/work-schedules \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_id": "123456789",
    "day_of_week": 0,
    "start_time": "10:00",
    "end_time": "20:00"
  }'
```

День недели: 0=Пн, 1=Вт, 2=Ср, 3=Чт, 4=Пт, 5=Сб, 6=Вс

### 4. Получить доступные слоты

```bash
curl "http://localhost:8000/api/available-slots/anna-a1b2c3d4?service_id=1&target_date=2024-10-21"
```

Ответ:
```json
{
  "date": "2024-10-21",
  "slots": [
    {
      "start_time": "2024-10-21T10:00:00",
      "end_time": "2024-10-21T12:00:00"
    },
    {
      "start_time": "2024-10-21T12:00:00",
      "end_time": "2024-10-21T14:00:00"
    }
    // ... остальные слоты
  ]
}
```

### 5. Создать бронирование (как клиент)

```bash
curl -X POST http://localhost:8000/api/bookings \
  -H "Content-Type: application/json" \
  -d '{
    "master_slug": "anna-a1b2c3d4",
    "telegram_id": "987654321",
    "service_id": 1,
    "start_time": "2024-10-21T10:00:00",
    "client_phone": "+7-999-123-45-67"
  }'
```

## 📱 Telegram бот команды

```
/start               - Начать, регистрация мастера
🔗 Моя ссылка        - Показать ссылку для клиентов
📋 Услуги           - Управление услугами (в web-панели)
⏰ График работы     - Управление графиком (в web-панели)
📅 Мои записи       - Список бронирований
👥 Клиенты          - Список клиентов
⚙️ Настройки         - Настройки аккаунта
```

## 🗄️ Структура БД

### Masters
- `id` (PK)
- `telegram_id` (UNIQUE)
- `first_name`, `last_name`
- `description`, `specialization`
- `timezone`
- `registration_link_slug` (UNIQUE)
- `is_active`

### Services
- `id` (PK)
- `master_id` (FK)
- `name`, `description`
- `duration_minutes`
- `price`

### WorkSchedules
- `id` (PK)
- `master_id` (FK)
- `day_of_week` (0-6)
- `start_time`, `end_time`
- **UNIQUE** на (master_id, day_of_week)

### Bookings
- `id` (PK)
- `master_id`, `client_id`, `service_id` (FK)
- `start_time`, `end_time`
- `status` (pending, confirmed, completed, cancelled)
- **UNIQUE** на (master_id, start_time, end_time)
- **CHECK** start_time < end_time

### Breaks
- `id` (PK)
- `master_id` (FK)
- `date`, `start_time`, `end_time`
- `reason`

### Waitlist
- `id` (PK)
- `master_id`, `client_id`, `service_id` (FK)
- `preferred_date_from`, `preferred_date_to`
- `preferred_time_start`, `preferred_time_end`
- `status` (active, matched, cancelled, expired)

## 🔐 Безопасность

✅ **Реализовано:**
- Уникальные ограничения для предотвращения двойного бронирования
- Проверка прав: мастер не может видеть данные другого мастера
- Валидация входных данных (Pydantic)
- Сохранение критичных операций в транзакциях
- Логирование без утечки секретов
- `.env.example` без настоящих токенов

⚠️ **Требует реализации:**
- Валидация `initData` для Telegram Mini App
- Rate limiting для API
- HTTPS для production

## 📊 Ограничения MVP

- ❌ Нет приёма платежей (только интеграция)
- ❌ Нет сложной аналитики
- ❌ Нет рейтинговой системы
- ❌ Нет маркетплейса мастеров
- ❌ Нет отдельных мобильных приложений
- ⚠️ Лист ожидания: MVP отправляет уведомление одному клиенту, требует подтверждения в срок

## 🚀 Что дальше

1. **Web-интерфейс для мастеров** (React/Vue)
   - Управление услугами
   - Редактирование графика
   - Просмотр записей в виде календаря
   - Автоматические напоминания

2. **Telegram Mini App для клиентов**
   - Выбор услуги и времени
   - Визуальный календарь
   - История бронирований

3. **Расширенный лист ожидания**
   - Более умное распределение
   - Анализ предпочтений клиентов

4. **Интеграция платежей**
   - Stripe / YooMoney / ЮКасса

5. **Аналитика и отчёты**
   - Доход по дням/услугам
   - Популярные услуги
   - Метрики загруженности

## 📞 Поддержка

Если возникли вопросы, проверьте:
1. Логи: `docker-compose logs backend`
2. БД: `docker-compose logs db`
3. Все ли переменные окружения установлены

## 📄 Лицензия

MVP для личного и коммерческого использования.

---

**Версия**: 1.0.0-MVP  
**Дата**: Октябрь 2024
