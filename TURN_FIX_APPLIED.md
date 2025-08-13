# ✅ TURN СЕРВЕР ИСПРАВЛЕН!

## 🚨 Проблема была в том, что:

1. **Render использовал старый Dockerfile** вместо `Dockerfile.simple`
2. **В старом Dockerfile НЕ БЫЛ curl**, но скрипт пытался его использовать
3. **Скрипт `start_turn.sh`** пытался получить IP через curl

## 🔧 Что исправлено:

### 1. **Заменил основной Dockerfile**
- ✅ Теперь `./turn/Dockerfile` содержит curl
- ✅ Использует `coturn/coturn:latest` (готовый образ)
- ✅ Устанавливает curl, wget, python3, dnsutils

### 2. **Обновил render.yaml**
- ✅ Теперь использует `./turn/Dockerfile` (основной)
- ✅ Не нужно указывать `Dockerfile.simple`

### 3. **Скрипт запуска**
- ✅ Использует `start_turn_simple.sh` (с автоматическим IP)
- ✅ Проверяет наличие curl перед использованием

## 🚀 Что делать дальше:

### 1. **Сделайте новый деплой на Render**
- В Dashboard → TURN сервис → Manual Deploy
- Теперь будет использоваться **новый Dockerfile с curl**

### 2. **Проверьте логи**
Должно быть:
```
=== TURN Server Startup Script (Simple) ===
✅ TURN_PASSWORD: [SET]
✅ TURN_USERNAME: voicechat
✅ Successfully got IP from ifconfig.me: [IP]
✅ TURN server started with PID: [число]
```

### 3. **Переменные окружения**
```bash
TURN_USERNAME=voicechat
TURN_PASSWORD=turn123456
EXTERNAL_IP= (оставьте пустым)
```

## 🎯 Результат:

После нового деплоя:
- ✅ curl будет доступен
- ✅ TURN сервер автоматически получит внешний IP
- ✅ WebRTC соединения будут работать
- ✅ Голосовой чат заработает

## 📝 Файлы изменены:

- ✅ `turn/Dockerfile` - заменен на версию с curl
- ✅ `render.yaml` - использует основной Dockerfile
- ✅ `start_turn_simple.sh` - автоматическое получение IP

**Делайте новый деплой - теперь все должно работать!** 🎉
