# Инструкции по деплою TURN сервера на Render

## 🚨 Проблема решена!

Мы создали несколько вариантов Dockerfile для решения проблемы с `curl: command not found`.

## 📁 Доступные варианты:

### 1. `Dockerfile.minimal` (РЕКОМЕНДУЕТСЯ)
- ✅ Минимальные зависимости
- ✅ Работает без curl
- ✅ Простой и надежный
- ✅ Используется в render.yaml

### 2. `Dockerfile.simple`
- ✅ Устанавливает curl, wget, dnsutils
- ✅ Автоматическое получение IP
- ✅ Может не работать на некоторых системах

### 3. `Dockerfile.ultra-simple`
- ✅ Базовый вариант
- ✅ Может иметь проблемы с curl

## 🚀 Как деплоить:

### Шаг 1: В Render Dashboard
1. Перейдите в ваш TURN сервис `voice-chat-turn`
2. Убедитесь, что используется `Dockerfile.minimal`
3. Проверьте переменные окружения:

```bash
TURN_USERNAME=voicechat
TURN_PASSWORD=turn123456
EXTERNAL_IP= (оставьте пустым)
```

### Шаг 2: Manual Deploy
1. Нажмите "Manual Deploy"
2. Дождитесь завершения сборки
3. Проверьте логи

### Шаг 3: Проверка работы
В логах должно быть:
```
✅ TURN_PASSWORD: [SET]
✅ TURN_USERNAME: voicechat
✅ EXTERNAL_IP not set or invalid, removing from config
✅ TURN server started with PID: [число]
```

## 🔧 Что происходит:

1. **Скрипт проверяет переменные окружения**
2. **Если EXTERNAL_IP не задан - убирает его из конфига**
3. **TURN сервер сам определяет свой IP**
4. **Заменяет пароль в конфигурации**
5. **Запускает TURN сервер и health check**

## ❌ Если все еще не работает:

### Вариант A: Установить EXTERNAL_IP вручную
1. В Render Dashboard → Environment Variables
2. Добавить: `EXTERNAL_IP=ваш_реальный_ip`
3. Получить IP можно через: https://whatismyipaddress.com/

### Вариант B: Использовать другой Dockerfile
1. Изменить в render.yaml:
```yaml
dockerfilePath: ./turn/Dockerfile.simple
```

### Вариант C: Простой запуск без скрипта
1. Изменить в render.yaml:
```yaml
env: docker
dockerfilePath: ./turn/Dockerfile
```

## 🧪 Тестирование:

После успешного деплоя:
1. Проверьте логи TURN сервера
2. Используйте [WebRTC ICE trickle tool](https://webrtc.github.io/samples/src/content/peerconnection/trickle-ice/)
3. Введите: `turn:turn-dist.onrender.com:3478`
4. Username: `voicechat`, Password: `turn123456`

## 📞 Поддержка:

Если проблемы остаются:
1. Проверьте логи в Render Dashboard
2. Убедитесь, что порт 3478 открыт
3. Проверьте, что TURN сервер запустился
4. Используйте fallback TURN серверы в коде фронтенда
