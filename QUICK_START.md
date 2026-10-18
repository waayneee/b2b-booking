# 🚀 QUICK START

## За 5 минут с Docker

```bash
# 1. Установить токен бота
cd backend
cp .env.example .env
# Отредактировать .env: TELEGRAM_BOT_TOKEN=ваш_токен

# 2. Запустить Docker Compose
cd ..
docker-compose up -d

# 3. Проверить здоровье
curl http://localhost:8000/health

# 4. Создать мастера (ниже примеры)
```

## За 10 минут локально (Windows)

```powershell
# 1. Установить PostgreSQL и создать БД
psql -U postgres -c "CREATE DATABASE booking_db;"

# 2. Токен бота
cd backend
Copy-Item .env.example .env
# Редактировать: .env -> TELEGRAM_BOT_TOKEN

# 3. Виртуальное окружение
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 4. Миграции БД
alembic upgrade head

# 5. Запустить сервер (терминал 1)
uvicorn app.main:app --reload --port 8000

# 6. Бот (терминал 2)
python -m app.bot.handlers

# 7. Проверить
curl http://localhost:8000/health
```

## Первый тест

Создать мастера (PowerShell):

```powershell
$body = @{
    telegram_id = "123456789"
    first_name = "Анна"
    specialization = "Лэшмейкер"
    timezone = "Europe/Moscow"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/masters/register" `
    -Method POST -Headers @{"Content-Type"="application/json"} -Body $body
```

Должен вернуть JSON с ID и ссылкой типа `anna-abc12345`.

Откройте в браузере: `http://localhost:8000/book/anna-abc12345`

## Документация

- **[SETUP.md](SETUP.md)** — полная инструкция по настройке
- **[README.md](README.md)** — описание API и функций
- **[LIMITATIONS.md](LIMITATIONS.md)** — что реализовано, что нет
- **[PLAN.md](PLAN.md)** — архитектура и план разработки

## Основные файлы

```
backend/
  app/
    main.py              ← FastAPI endpoints
    models/              ← ORM модели
    services/schedule.py ← Бизнес-логика расписания
    bot/handlers.py      ← Telegram бот
    schemas/             ← Pydantic валидация
frontend/
  templates/booking.html ← HTML UI
  static/js/app.js       ← JavaScript логика
  static/css/style.css   ← Стили
```

## Команды

```bash
# Тесты
pytest tests/ -v

# Миграции
alembic upgrade head
alembic downgrade -1

# FastAPI документация
http://localhost:8000/docs

# Логи Docker
docker-compose logs -f backend
```

## Проблемы?

1. БД не подключается → проверить DATABASE_URL в .env
2. Port 8000 занят → `netstat -ano | findstr :8000` и `taskkill /PID <PID> /F`
3. Бот не работает → `TELEGRAM_BOT_TOKEN=123...` должен быть валидным

---

**Готово!** Теперь у вас есть рабочий MVP.
