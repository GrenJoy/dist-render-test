# 🔧 Исправление ошибки MongoDB Atlas на Render

## Проблема
```
pymongo.errors.OperationFailure: bad auth : authentication failed
```

## Причина
Backend не может подключиться к MongoDB Atlas из-за неправильных учетных данных или неверного connection string.

## Решение

### Шаг 1: Проверить MongoDB Atlas
1. Зайдите в [MongoDB Atlas Dashboard](https://cloud.mongodb.com/)
2. Убедитесь, что кластер работает (зеленый статус)
3. Проверьте IP whitelist - добавьте `0.0.0.0/0` для доступа с любого IP

### Шаг 2: Получить правильный Connection String
1. В Atlas: **Database** → **Connect** → **Connect your application**
2. Скопируйте connection string
3. Замените `<password>` на ваш пароль
4. Формат: `mongodb+srv://username:password@cluster.mongodb.net/`

### Шаг 3: Настроить переменные окружения в Render
В Render Dashboard для сервиса `voice-chat-backend`:

1. **Environment** → **Environment Variables**
2. Установите `MONGO_URL` = ваш connection string
3. Установите `CORS_ORIGINS` = URL вашего frontend (например: `https://voice-chat-frontend.onrender.com`)

### Шаг 4: Перезапустить сервис
После изменения переменных окружения:
1. Render автоматически пересоберет проект
2. Или нажмите **Manual Deploy**

## Проверка
После исправления:
1. Backend должен запуститься без ошибок
2. В логах должно быть: `INFO: Application startup complete`
3. Frontend сможет подключиться к backend

## Альтернативное решение
Если MongoDB Atlas не работает, можно временно использовать MongoDB без аутентификации для тестирования.
