# 🎙️ Голосовой чат - Деплой на Render

Полная инструкция для деплоя голосового приложения на Render за несколько команд.

## 🚀 Быстрый старт (3 шага)

### 1. Настройка MongoDB Atlas (бесплатно)

MongoDB Atlas - это облачная MongoDB, бесплатно до 512MB.

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

### 2. Подготовка репозитория

```bash
# Загрузи код в свой GitHub репозиторий
git init
git add .
git commit -m "Initial voice chat app"
git branch -M main
git remote add origin https://github.com/ТВОЙ_USERNAME/voice-chat-app.git
git push -u origin main
```

### 3. Деплой на Render

1. **Заходи на Render**: https://render.com/
2. **Подключи GitHub**: Dashboard → "New" → "Blueprint"
3. **Выбери репозиторий**: твой voice-chat-app репозиторий
4. **Настрой переменные окружения**:

   **Для Backend сервиса:**
   - `MONGO_URL`: твоя строка подключения из MongoDB Atlas
   - `CORS_ORIGINS`: `*` (или конкретный домен фронтенда)

5. **Нажми Deploy**: Render автоматически создаст оба сервиса
6. **Готово!** Через 5-10 минут получишь рабочий сайт

## 🔧 Переменные окружения

### Backend Environment Variables
```
MONGO_URL=mongodb+srv://voicechat:ТВОЙ_ПАРОЛЬ@voice-chat-cluster.xxxxx.mongodb.net/voice_chat_db
DB_NAME=voice_chat_db
CORS_ORIGINS=*
```

### Frontend (автоматически)
```
REACT_APP_BACKEND_URL=https://voice-chat-backend.onrender.com
```

## 📋 Что включено в проект

### ✅ Готовые конфигурации:
- `render.yaml` - автоматическая настройка сервисов
- `requirements.txt` - Python зависимости
- `package.json` - Node.js зависимости
- Production настройки для FastAPI и React

### ✅ Автоматические фичи:
- HTTPS сертификаты
- Автоматические билды при push в GitHub
- Мониторинг и логи
- Restart при падении

## 🌍 После деплоя

### Использование:
1. **Открой фронтенд URL** (что-то вроде `https://voice-chat-frontend.onrender.com`)
2. **Создай комнату** или введи ID существующей
3. **Поделись ссылкой** с друзьями
4. **Разреши доступ к микрофону** в браузере
5. **Общайтесь!** 🎉

### Возможности:
- 🌍 **Международные звонки** - работает из любой страны
- 🔐 **Полная безопасность** - WebRTC шифрование
- 🎤 **Контроль звука** - mute, громкость, индикаторы
- 📱 **Кроссплатформенность** - ПК, телефон, планшет
- ⚡ **Мгновенное подключение** - без регистрации

## 🚨 Важные моменты

### Render Limitations:
- **Бесплатный план**: сервис засыпает через 15 минут неактивности
- **Первое подключение**: может занять 30-60 секунд (cold start)
- **Трафик**: 100GB/месяц бесплатно (хватит на тысячи часов)

### WebRTC Requirements:
- **HTTPS обязателен** - Render автоматически предоставляет
- **Микрофон разрешения** - браузер спросит автоматически
- **Современный браузер** - Chrome, Firefox, Safari, Edge

## 🔧 Troubleshooting

### Если что-то не работает:

1. **Проверь логи**:
   - Render Dashboard → твой сервис → Logs
   
2. **Проверь переменные**:
   - Environment → убедись что MONGO_URL правильный
   
3. **Проверь MongoDB**:
   - Atlas → Network Access → 0.0.0.0/0 должен быть разрешен
   
4. **Микрофон не работает**:
   - Браузер → Settings → Privacy → Microphone → разреши для сайта

### Частые ошибки:
- `Connection failed` → проверь MONGO_URL
- `WebSocket error` → проверь что backend запущен
- `Microphone blocked` → разреши доступ в браузере

## 💰 Стоимость

### Render Free Tier:
- **Web Services**: 750 часов/месяц бесплатно
- **Static Sites**: безлимитно и бесплатно  
- **Bandwidth**: 100GB/месяц бесплатно
- **Автоматический SSL**: бесплатно

### MongoDB Atlas Free:
- **Storage**: 512MB бесплатно
- **Connections**: безлимитно
- **Bandwidth**: без ограничений

**💡 Итого: полностью бесплатно для личного использования!**

## 🎯 Следующие шаги

После успешного деплоя можешь добавить:
- 🔐 Аутентификацию пользователей
- 📝 Сохранение истории комнат
- 🎨 Кастомизацию интерфейса
- 📊 Аналитику использования
- 🌍 Мультиязычность

**Удачи с деплоем! 🚀**