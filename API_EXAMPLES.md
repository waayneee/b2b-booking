# Примеры использования API

## 1️⃣ Создание мастера

```bash
curl -X POST http://localhost:8000/api/masters/register \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_id": "123456789",
    "first_name": "Анна",
    "last_name": "Сергеева",
    "phone": "+7 (999) 123-45-67",
    "description": "Мастер по наращиванию ресниц с опытом",
    "specialization": "Лэшмейкер",
    "timezone": "Europe/Moscow"
  }'
```

**Ответ**:
```json
{
  "id": 1,
  "telegram_id": "123456789",
  "first_name": "Анна",
  "last_name": "Сергеева",
  "phone": "+7 (999) 123-45-67",
  "description": "Мастер по наращиванию ресниц с опытом",
  "specialization": "Лэшмейкер",
  "timezone": "Europe/Moscow",
  "registration_link_slug": "anna-ab12cd34",
  "is_active": true,
  "created_at": "2024-10-18T12:00:00"
}
```

## 2️⃣ Создание услуги

```bash
curl -X POST http://localhost:8000/api/services \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_id": "123456789",
    "name": "Наращивание ресниц 1D",
    "description": "Классическое наращивание",
    "duration_minutes": 120,
    "price": 2500
  }'
```

**Ответ**:
```json
{
  "id": 1,
  "master_id": 1,
  "name": "Наращивание ресниц 1D",
  "description": "Классическое наращивание",
  "duration_minutes": 120,
  "price": 2500.0,
  "is_active": true,
  "created_at": "2024-10-18T12:00:00"
}
```

## 3️⃣ Создание второй услуги

```bash
curl -X POST http://localhost:8000/api/services \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_id": "123456789",
    "name": "Коррекция ресниц",
    "description": "Коррекция через 3 недели",
    "duration_minutes": 60,
    "price": 1500
  }'
```

## 4️⃣ Устанавливаем график работы

Понедельник (0) с 10:00 до 20:00:

```bash
curl -X POST http://localhost:8000/api/work-schedules \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_id": "123456789",
    "day_of_week": 0,
    "start_time": "10:00",
    "end_time": "20:00"
  }'
```

Вторник (1) с 10:00 до 20:00:

```bash
curl -X POST http://localhost:8000/api/work-schedules \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_id": "123456789",
    "day_of_week": 1,
    "start_time": "10:00",
    "end_time": "20:00"
  }'
```

Среда (2) с 10:00 до 20:00:

```bash
curl -X POST http://localhost:8000/api/work-schedules \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_id": "123456789",
    "day_of_week": 2,
    "start_time": "10:00",
    "end_time": "20:00"
  }'
```

## 5️⃣ Добавляем перерыв в среду

```bash
curl -X POST http://localhost:8000/api/breaks \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_id": "123456789",
    "date": "2024-10-23",
    "start_time": "13:00",
    "end_time": "14:00",
    "reason": "Обеденный перерыв"
  }'
```

## 6️⃣ Получить доступные слоты

Для понедельника 2024-10-21 для услуги #1:

```bash
curl "http://localhost:8000/api/available-slots/anna-ab12cd34?service_id=1&target_date=2024-10-21"
```

**Ответ**:
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
    },
    {
      "start_time": "2024-10-21T14:00:00",
      "end_time": "2024-10-21T16:00:00"
    },
    {
      "start_time": "2024-10-21T16:00:00",
      "end_time": "2024-10-21T18:00:00"
    },
    {
      "start_time": "2024-10-21T18:00:00",
      "end_time": "2024-10-21T20:00:00"
    }
  ]
}
```

## 7️⃣ Клиент бронирует время

Клиент Петр (telegram_id=987654321) хочет забронировать в 14:00:

```bash
curl -X POST http://localhost:8000/api/bookings \
  -H "Content-Type: application/json" \
  -d '{
    "master_slug": "anna-ab12cd34",
    "telegram_id": "987654321",
    "service_id": 1,
    "start_time": "2024-10-21T14:00:00",
    "client_phone": "+7 (999) 987-65-43"
  }'
```

**Ответ**:
```json
{
  "id": 1,
  "master_id": 1,
  "client_id": 1,
  "service_id": 1,
  "start_time": "2024-10-21T14:00:00",
  "end_time": "2024-10-21T16:00:00",
  "status": "confirmed",
  "client_phone": "+7 (999) 987-65-43",
  "notes": null,
  "created_at": "2024-10-18T12:00:00"
}
```

## 8️⃣ Получить доступные слоты после первого бронирования

Теперь 14:00-16:00 должен быть недоступен:

```bash
curl "http://localhost:8000/api/available-slots/anna-ab12cd34?service_id=1&target_date=2024-10-21"
```

**Ответ**: только 10:00, 12:00, 16:00, 18:00 (14:00-16:00 занято!)

## 9️⃣ Клиент отменяет запись

```bash
curl -X POST http://localhost:8000/api/bookings/1/cancel \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_id": "123456789"
  }'
```

После отмены 14:00-16:00 снова становится доступным.

## 🔟 Добавление в лист ожидания

Клиент хочет забронировать между 20-25 октября в вечернее время:

```bash
curl -X POST http://localhost:8000/api/waitlist \
  -H "Content-Type: application/json" \
  -d '{
    "master_slug": "anna-ab12cd34",
    "telegram_id": "555666777",
    "service_id": 2,
    "preferred_date_from": "2024-10-20",
    "preferred_date_to": "2024-10-25",
    "preferred_time": "evening"
  }'
```

## 🎯 Проверить мою запись (для клиента)

```bash
curl "http://localhost:8000/api/bookings?telegram_id=987654321&role=client"
```

## 👨‍💼 Получить свои записи (для мастера)

```bash
curl "http://localhost:8000/api/bookings?telegram_id=123456789&role=master"
```

## 🌐 Открыть UI в браузере

```
http://localhost:8000/book/anna-ab12cd34
```

Вы увидите:
1. Профиль Анны
2. Список услуг (Наращивание и Коррекция)
3. Выбор даты
4. Доступные времена
5. Форма подтверждения
6. Успешное сообщение

---

## 📝 Тестовые данные для быстрого старта

### Мастер 1: Анна (Лэшмейкер)
- telegram_id: 123456789
- Услуга: Наращивание ресниц 2500₽ (120 мин)
- График: Пн-Чт 10:00-20:00
- Ссылка: /book/anna-*

### Мастер 2: Мария (Бровист)
```bash
curl -X POST http://localhost:8000/api/masters/register \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_id": "999888777",
    "first_name": "Мария",
    "specialization": "Бровист",
    "timezone": "Europe/Moscow"
  }'
```

### Клиент: Иван
- telegram_id: 987654321
- Готов забронировать в любое время

---

**Версия**: 1.0.0-MVP  
**Дата**: Октябрь 2024
