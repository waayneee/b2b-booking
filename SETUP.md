# Инструкция по настройке и запуску MVP

## Часть 1: Подготовка Telegram Bot

### Шаг 1: Создание бота через BotFather

1. Откройте Telegram и найдите `@BotFather`
2. Отправьте команду `/newbot`
3. Следуйте инструкциям:
   - Дайте имя боту (например, "Booking Bot Test")
   - Задайте username (должен заканчиваться на `_bot`, например: `my_booking_bot_123`)
4. BotFather пришлёт вам токен вида: `123456789:ABCDEFGhijklmnop...`
5. **Скопируйте этот токен** — он понадобится на следующем шаге

### Шаг 2: Установка токена

1. Откройте `backend/.env`
2. Замените `TELEGRAM_BOT_TOKEN` на свой токен:
   ```
   TELEGRAM_BOT_TOKEN=123456789:ABCDEFGhijklmnop...
   ```
3. Сохраните файл

---

## Часть 2: Локальный запуск на Windows

### Требования

- Python 3.12+ ([загрузить](https://www.python.org/downloads/))
- PostgreSQL 14+ ([загрузить](https://www.postgresql.org/download/windows/)) или Docker
- Git (опционально)

### Вариант A: С PostgreSQL локально

#### Шаг 1: Установить PostgreSQL

1. Скачайте установщик с [postgresql.org](https://www.postgresql.org/download/windows/)
2. При установке:
   - Выберите пароль для пользователя `postgres` (запомните его!)
   - Используйте порт по умолчанию `5432`
3. После установки откройте PowerShell и проверьте:
   ```powershell
   psql -U postgres -c "SELECT 1"
   ```

#### Шаг 2: Создать базу данных

```powershell
psql -U postgres -c "CREATE DATABASE booking_db;"
```

Если запросит пароль — введите пароль, который указали при установке.

#### Шаг 3: Установить Python зависимости

```powershell
# Перейти в папку проекта
cd C:\Users\wayne\Documents\Projects\b2b\backend

# Создать виртуальное окружение
python -m venv venv

# Активировать
venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt
```

#### Шаг 4: Применить миграции БД

```powershell
alembic upgrade head
```

#### Шаг 5: Запустить FastAPI сервер

В одном окне PowerShell:
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Вы должны увидеть:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### Шаг 6: Проверить сервер

Откройте в браузере: `http://localhost:8000/health`

Должен вернуться ответ `{"status":"ok"}`

#### Шаг 7: Запустить Telegram бота (отдельное окно)

```powershell
# Убедитесь, что venv всё ещё активирована
cd C:\Users\wayne\Documents\Projects\b2b\backend
python -m app.bot.handlers
```

Бот будет работать и слушать Telegram API.

---

### Вариант B: С Docker (проще)

#### Шаг 1: Установить Docker Desktop

1. Скачайте [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
2. Установите и перезагрузитесь
3. Откройте PowerShell и проверьте:
   ```powershell
   docker --version
   docker-compose --version
   ```

#### Шаг 2: Запустить через Docker Compose

```powershell
cd C:\Users\wayne\Documents\Projects\b2b

# Запустить контейнеры
docker-compose up -d

# Проверить логи
docker-compose logs -f backend
```

Сервис будет доступен по `http://localhost:8000/health`

---

## Часть 3: Тестирование API

### Создать первого мастера

Откройте PowerShell и запустите:

```powershell
$body = @{
    telegram_id = "123456789"
    first_name = "Анна"
    last_name = "Сергеева"
    phone = "+7 (999) 123-45-67"
    description = "Мастер по наращиванию ресниц с 5-летним опытом"
    specialization = "Лэшмейкер"
    timezone = "Europe/Moscow"
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://localhost:8000/api/masters/register" `
    -Method POST `
    -Headers @{"Content-Type"="application/json"} `
    -Body $body

$response.Content | ConvertFrom-Json | ConvertTo-Json
```

Результат (пример):
```json
{
  "id": 1,
  "telegram_id": "123456789",
  "first_name": "Анна",
  "last_name": "Сергеева",
  "specialization": "Лэшмейкер",
  "registration_link_slug": "anna-a1b2c3d4",
  "timezone": "Europe/Moscow",
  "created_at": "2024-10-18T12:00:00"
}
```

**Запомните `registration_link_slug`** — это ссылка для клиентов: `http://localhost:8000/book/anna-a1b2c3d4`

### Создать услугу

```powershell
$body = @{
    telegram_id = "123456789"
    name = "Наращивание ресниц 1D"
    description = "Классическое наращивание на 1-1.5 часа"
    duration_minutes = 90
    price = 2500
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/services" `
    -Method POST `
    -Headers @{"Content-Type"="application/json"} `
    -Body $body | ForEach-Object { $_.Content | ConvertFrom-Json }
```

### Установить расписание работы

Понедельник 10:00-20:00 (день 0):

```powershell
$body = @{
    telegram_id = "123456789"
    day_of_week = 0
    start_time = "10:00"
    end_time = "20:00"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/work-schedules" `
    -Method POST `
    -Headers @{"Content-Type"="application/json"} `
    -Body $body | ForEach-Object { $_.Content | ConvertFrom-Json }
```

День недели: 0=Пн, 1=Вт, 2=Ср, 3=Чт, 4=Пт, 5=Сб, 6=Вс

Повторите для остальных рабочих дней.

### Получить доступные слоты

```powershell
$masterSlug = "anna-a1b2c3d4"  # Замените на вашу ссылку
$serviceId = 1                  # Замените на ID услуги
$targetDate = "2024-10-21"      # Замените на дату

$response = Invoke-WebRequest -Uri "http://localhost:8000/api/available-slots/$masterSlug?service_id=$serviceId&target_date=$targetDate"
$response.Content | ConvertFrom-Json | ConvertTo-Json
```

---

## Часть 4: Тестирование через Web UI

1. Откройте браузер
2. Перейдите на `http://localhost:8000/book/anna-a1b2c3d4` (используйте свой slug)
3. Вы должны увидеть профиль мастера и список услуг
4. Нажимайте "Выбирай" для тестирования потока бронирования

---

## Часть 5: Запуск тестов

```powershell
cd C:\Users\wayne\Documents\Projects\b2b\backend

# Активировать venv (если не активирована)
venv\Scripts\activate

# Запустить тесты
pytest tests/ -v
```

Вы должны увидеть зелёные галочки для всех тестов.

---

## Файлы, которые вам нужны

Самые важные:
- `backend/.env` — переменные окружения
- `backend/requirements.txt` — Python зависимости
- `docker-compose.yml` — Docker конфигурация
- `backend/app/main.py` — FastAPI сервер
- `backend/app/models/__init__.py` — ORM модели
- `backend/app/services/schedule.py` — Бизнес-логика расписания
- `frontend/templates/booking.html` — HTML UI для клиентов
- `frontend/static/js/app.js` — JavaScript логика

---

## Troubleshooting

### БД не подключается

**Ошибка**: `sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection failed`

**Решение**:
1. Проверьте, запущен ли PostgreSQL: `psql -U postgres -c "SELECT 1"`
2. Проверьте `DATABASE_URL` в `.env`
3. Проверьте пароль пользователя postgres

### Port 8000 занят

**Ошибка**: `Address already in use`

**Решение**:
```powershell
# Найти процесс на порту 8000
netstat -ano | findstr :8000

# Убить процесс (замените PID на число из выше)
taskkill /PID <PID> /F

# Или использовать другой порт
uvicorn app.main:app --port 8001
```

### Миграции не применяются

**Решение**:
```powershell
# Сбросить BD и пересоздать
# Внимание: потеряются все данные!
psql -U postgres -c "DROP DATABASE booking_db;"
psql -U postgres -c "CREATE DATABASE booking_db;"
alembic upgrade head
```

---

## Что дальше

1. **Telegram Mini App**: Интегрируйте `booking.html` как Mini App в Telegram
2. **Web панель для мастеров**: Создайте React приложение для управления
3. **Уведомления**: Настройте отправку уведомлений в Telegram
4. **Production**: Разверните на облачном сервере с HTTPS

---

**Версия**: 1.0.0-MVP  
**Дата**: Октябрь 2024
