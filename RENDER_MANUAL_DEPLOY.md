# 🎙️ Голосовой чат - Ручной деплой на Render

Полная инструкция для ручного деплоя голосового приложения на Render (без Blueprint).

## 🚀 Пошаговый деплой

### 1. Подготовка MongoDB Atlas (бесплатно)

1. **Создай аккаунт**: https://cloud.mongodb.com/
2. **Создай кластер**:
   - Выбери "M0 Sandbox" (бесплатно)
   - Выбери регион (например, AWS/Europe-West-1)
   - Назови кластер: `voice-chat-cluster`
3. **Настрой доступ**:
   - Database Access → Add New Database User
   - Username: `voicechat` 
   - Password: сгенерируй надежный пароль
   - Database User Privileges: "Read and write to any database"
4. **Настрой IP доступ**:
   - Network Access → Add IP Address
   - Выбери "Allow access from anywhere" (0.0.0.0/0)
5. **Получи connection string**:
   - Clusters → Connect → Connect your application
   - Скопируй строку: `mongodb+srv://voicechat:<password>@voice-chat-cluster.xxxxx.mongodb.net/`

### 2. Загрузка кода в GitHub

```bash
# Загрузи код в свой GitHub репозиторий
git init
git add .
git commit -m "Initial voice chat app with TURN server"
git branch -M main
git remote add origin https://github.com/ТВОЙ_USERNAME/voice-chat-app.git
git push -u origin main
```

### 3. Деплой на Render (ручной, без Blueprint)

#### Шаг 1: Создание Backend сервиса

1. **Заходи на Render**: https://render.com/
2. **Создай новый Web Service**:
   - Dashboard → "New" → "Web Service"
   - Connect Repository: выбери твой GitHub репозиторий
   - Name: `voice-chat-backend`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn server:app --host 0.0.0.0 --port $PORT`
   - Root Directory: `backend`

3. **Настрой переменные окружения**:
   - `MONGO_URL`: твоя строка подключения из MongoDB Atlas
   - `DB_NAME`: `voice_chat_db`
   - `CORS_ORIGINS`: `*`

4. **Нажми Create Web Service**

#### Шаг 2: Создание TURN сервера

1. **Создай еще один Web Service**:
   - Dashboard → "New" → "Web Service"
   - Connect Repository: тот же репозиторий
   - Name: `voice-chat-turn`
   - Environment: `Docker`
   - **Dockerfile Path**: `./turn/Dockerfile.simple` ⚠️ **ВАЖНО!**
   - Root Directory: `turn`

2. **Настрой переменные окружения**:
   - `TURN_USERNAME`: `voicechat`
   - `TURN_PASSWORD`: сгенерируй надежный пароль (например, `turn123456`)
   - `EXTERNAL_IP`: оставь пустым (Render автоматически установит)

3. **Нажми Create Web Service**

**💡 Примечание**: Используем `Dockerfile.simple` для быстрой и надежной сборки!

#### Шаг 3: Создание Frontend

1. **Создай Static Site**:
   - Dashboard → "New" → "Static Site"
   - Connect Repository: тот же репозиторий
   - Name: `voice-chat-frontend`
   - Root Directory: `frontend`
   - Build Command: `yarn install && yarn build`
   - Publish Directory: `build`

2. **Настрой переменные окружения**:
   - `REACT_APP_BACKEND_URL`: URL твоего backend сервиса
   - `REACT_APP_TURN_SERVER_URL`: URL твоего TURN сервера

3. **Нажми Create Static Site**

### 4. Настройка CORS в Backend

После создания всех сервисов, обнови `CORS_ORIGINS` в backend:

```
https://voice-chat-frontend.onrender.com
```

## 🔧 Переменные окружения

### Backend Service
```
MONGO_URL=mongodb+srv://voicechat:ТВОЙ_ПАРОЛЬ@voice-chat-cluster.xxxxx.mongodb.net/voice_chat_db
DB_NAME=voice_chat_db
CORS_ORIGINS=https://voice-chat-frontend.onrender.com
TURN_SERVER_URL=https://voice-chat-turn.onrender.com
```

### TURN Server
```
TURN_USERNAME=voicechat
TURN_PASSWORD=твой_надежный_пароль
EXTERNAL_IP= (оставь пустым)
```

### Frontend
```
REACT_APP_BACKEND_URL=https://voice-chat-backend.onrender.com
REACT_APP_TURN_SERVER_URL=https://voice-chat-turn.onrender.com
```

## 📋 Порядок деплоя

**Важно соблюдать порядок:**

1. **Backend** (первым, так как другие сервисы зависят от него)
2. **TURN Server** (вторым, для WebRTC)
3. **Frontend** (последним, после получения URL backend и TURN)

## 🌍 После деплоя

### Проверка работы:

1. **Backend**: открой `/api/` - должно показать API информацию
2. **TURN Server**: проверь логи - должен запуститься без ошибок
3. **Frontend**: открой главную страницу - должен загрузиться интерфейс

### Тестирование голосового чата:

1. Создай комнату на одном устройстве
2. Введи ID комнаты на другом устройстве
3. Разреши доступ к микрофону
4. Проверь голосовое соединение

## 🚨 Troubleshooting

### Если TURN сервер не запускается:

1. **Проверь логи** в Render Dashboard
2. **Убедись**, что используешь `Dockerfile.simple`
3. **Проверь переменные окружения**

### Если голос не работает:

1. **Проверь TURN сервер** - должен быть доступен
2. **Проверь консоль браузера** на ошибки WebRTC
3. **Убедись**, что микрофон разрешен

### Если backend не подключается к MongoDB:

1. **Проверь MONGO_URL** - должен быть правильным
2. **Проверь Network Access** в MongoDB Atlas (0.0.0.0/0)
3. **Проверь username/password** в connection string

## 💰 Стоимость

### Render Free Tier:
- **Web Services**: 750 часов/месяц бесплатно (3 сервиса)
- **Static Sites**: безлимитно и бесплатно
- **Bandwidth**: 100GB/месяц бесплатно
- **Автоматический SSL**: бесплатно

### MongoDB Atlas Free:
- **Storage**: 512MB бесплатно
- **Connections**: безлимитно

**💡 Итого: полностью бесплатно для личного использования!**

## 🎯 Следующие шаги

После успешного деплоя:
- 🔐 Добавь аутентификацию пользователей
- 📝 Сохраняй историю комнат
- 🎨 Кастомизируй интерфейс
- 📊 Добавь аналитику использования

**Удачи с деплоем! 🚀**
