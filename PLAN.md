# MVP план: Telegram-бот для онлайн-записи

## Этапы разработки

### Этап 1: Backend Core (День 1)
- [ ] Структура проекта и конфигурация
- [ ] PostgreSQL + SQLAlchemy + Alembic
- [ ] Модели: Мастер, Клиент, Услуга, Запись, Расписание
- [ ] API endpoints для регистрации и данных

### Этап 2: Бизнес-логика расписания (День 1-2)
- [ ] Вычисление доступных слотов с учётом графика и перерывов
- [ ] Проверка пересечений записей
- [ ] Защита от двойного бронирования (транзакции БД)
- [ ] Тесты расписания

### Этап 3: Telegram Bot (День 2)
- [ ] Регистрация мастера
- [ ] Создание услуг и графика работы
- [ ] Команды управления расписанием
- [ ] Уведомления

### Этап 4: Mini App для клиентов (День 3)
- [ ] Интерфейс выбора услуги и даты
- [ ] Календарь и слоты
- [ ] Бронирование

### Этап 5: Панель мастера в Mini App (День 3)
- [ ] Просмотр записей
- [ ] Управление графиком
- [ ] Отмена/перенос записей

### Этап 6: Лист ожидания (День 4)
- [ ] Добавление в очередь
- [ ] Автоматические уведомления при освобождении
- [ ] Защита от двойного бронирования

### Этап 7: Тестирование и документация (День 4)
- [ ] Автотесты для критических сценариев
- [ ] README с инструкциями
- [ ] Docker Compose для локального запуска

## Структура проекта
```
b2b/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Конфигурация
│   │   ├── database.py          # SQLAlchemy session
│   │   ├── models/              # ORM модели
│   │   ├── schemas/             # Pydantic схемы
│   │   ├── api/                 # API endpoints
│   │   ├── services/            # Бизнес-логика
│   │   ├── bot/                 # Telegram bot
│   │   └── tasks/               # Фоновые задачи
│   ├── migrations/              # Alembic миграции
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── docker-compose.yml
├── README.md
└── .gitignore
```

## Схема БД (основное)
- `masters` (id, telegram_id, name, description, timezone)
- `clients` (id, telegram_id, name, phone)
- `services` (id, master_id, name, duration_minutes, price)
- `work_schedules` (id, master_id, day_of_week, start_time, end_time)
- `breaks` (id, master_id, date, start_time, end_time)
- `bookings` (id, master_id, client_id, service_id, start_time, end_time, status)
- `waitlist` (id, master_id, client_id, service_id, preferred_date_from, preferred_date_to, preferred_time, status)
- `notifications` (id, recipient_telegram_id, message, sent_at, retry_count)

## Ключевые моменты
1. **Защита от двойного бронирования**: SELECT FOR UPDATE, уникальные ограничения
2. **Часовые пояса**: Хранить в UTC, отображать в timezone мастера
3. **Асинхронность**: async/await для БД и Telegram API
4. **Безопасность**: Проверка прав на каждый запрос, валидация initData для Mini App
5. **Уведомления**: Отправка с повторными попытками, idempotency ключи
