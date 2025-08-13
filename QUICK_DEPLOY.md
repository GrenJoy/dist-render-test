# 🚀 Быстрый деплой голосового чата на Render

## ⚡ 3 простых шага

### 1. MongoDB Atlas (5 минут)
- Зарегистрируйся на https://cloud.mongodb.com/
- Создай кластер M0 Sandbox (бесплатно)
- Получи connection string

### 2. GitHub (2 минуты)
```bash
git init
git add .
git commit -m "Voice chat app"
git remote add origin https://github.com/ТВОЙ_USERNAME/voice-chat-app.git
git push -u origin main
```

### 3. Render (10 минут)
1. **Backend**: New → Web Service → Python
2. **TURN Server**: New → Web Service → Docker  
3. **Frontend**: New → Static Site

## 🔑 Ключевые переменные

**Backend:**
- `MONGO_URL`: твоя MongoDB строка
- `CORS_ORIGINS`: `*`

**TURN Server:**
- `TURN_USERNAME`: `voicechat`
- `TURN_PASSWORD`: `turn123456`

**Frontend:**
- `REACT_APP_BACKEND_URL`: URL backend
- `REACT_APP_TURN_SERVER_URL`: URL TURN

## 📱 Результат
- 🌐 Голосовой чат работает из любой страны
- 🔐 Полная безопасность WebRTC
- 💰 Полностью бесплатно
- 📱 Работает на всех устройствах

**Подробная инструкция в `RENDER_MANUAL_DEPLOY.md`** 📖
