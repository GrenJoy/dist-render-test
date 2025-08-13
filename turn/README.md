# 🎯 TURN Server для голосового чата

CoTURN TURN сервер для WebRTC голосового чата, развернутый на Render.

## 🚀 Что это

TURN (Traversal Using Relays around NAT) сервер помогает WebRTC соединениям работать через:
- NAT (Network Address Translation)
- Корпоративные файрволы
- Сложные сетевые конфигурации

## 🔧 Конфигурация

### Переменные окружения:
- `TURN_USERNAME`: имя пользователя (по умолчанию: voicechat)
- `TURN_PASSWORD`: пароль (установите вручную)
- `EXTERNAL_IP`: внешний IP (Render автоматически установит)

### Порты:
- **3478**: основной порт для STUN/TURN
- **5349**: TLS порт (если включен)

## 📁 Структура файлов

```
turn/
├── Dockerfile          # Docker образ
├── turnserver.conf     # Конфигурация CoTURN
├── start_turn.sh       # Скрипт запуска
├── .dockerignore       # Исключения для Docker
└── README.md           # Этот файл
```

## 🐳 Docker

Сервер упакован в Docker контейнер:
- **Base image**: Ubuntu 22.04
- **CoTURN version**: 4.6.2
- **Security**: запуск от непривилегированного пользователя

## 🔒 Безопасность

- Аутентификация через username/password
- Ограничения на количество соединений
- Логирование всех операций
- Изоляция в Docker контейнере

## 📊 Мониторинг

### Логи:
- Все TURN операции логируются
- Доступны в Render Dashboard
- Включают информацию о подключениях

### Health Check:
- Endpoint: `/health`
- Проверка доступности сервера
- Автоматический restart при падении

## 🌐 Использование в WebRTC

### Frontend конфигурация:
```javascript
const configuration = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { 
      urls: 'turn:voice-chat-turn.onrender.com:3478',
      username: 'voicechat',
      credential: 'ваш_пароль'
    }
  ]
};
```

## 🚨 Troubleshooting

### Сервер не запускается:
1. Проверьте переменные окружения
2. Убедитесь, что Docker образ собрался
3. Проверьте логи в Render Dashboard

### WebRTC не подключается:
1. Убедитесь, что TURN сервер доступен
2. Проверьте username/password в frontend
3. Проверьте консоль браузера на ошибки

## 📚 Документация

- [CoTURN Official](https://github.com/coturn/coturn)
- [WebRTC TURN](https://webrtc.org/getting-started/turn-server)
- [Render Docker](https://render.com/docs/deploy-docker)

## 🆘 Поддержка

При проблемах:
1. Проверьте логи в Render Dashboard
2. Убедитесь, что все переменные окружения установлены
3. Проверьте доступность портов
4. Обратитесь к документации CoTURN
