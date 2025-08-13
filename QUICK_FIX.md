# 🚨 Быстрое исправление голосового чата

## Проблема
TURN сервер работает, но пользователи не слышат друг друга.

## ⚡ Быстрое решение (5 минут)

### 1. Перезапустить TURN сервер в Render
- Dashboard → TURN сервер → Manual Deploy
- Дождаться завершения

### 2. Проверить переменные окружения
```
TURN_USERNAME=voicechat
TURN_PASSWORD=твой_пароль
EXTERNAL_IP= (пусто)
```

### 3. Обновить frontend код
В React компоненте WebRTC добавить:

```javascript
const configuration = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { 
      urls: 'turn:turn-dist.onrender.com:3478',
      username: 'voicechat',
      credential: 'твой_пароль'
    }
  ]
};
```

### 4. Перезапустить frontend
- Dashboard → Frontend → Manual Deploy

## 🔍 Проверка

### В логах TURN сервера должно быть:
```
INFO: session: new, username=voicechat
INFO: session: bound, username=voicechat
```

### В консоли браузера:
- WebRTC ICE candidates
- TURN server connection

## ✅ Результат
Голосовой чат должен заработать!

**Подробная инструкция в `WEBRTC_TURN_SETUP.md`** 📖
