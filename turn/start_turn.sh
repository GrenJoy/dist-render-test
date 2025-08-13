#!/bin/bash

# Скрипт запуска TURN сервера и health check
# Получаем внешний IP из переменной окружения или определяем автоматически

if [ -z "$EXTERNAL_IP" ]; then
    # Если EXTERNAL_IP не задан, используем 0.0.0.0
    EXTERNAL_IP="0.0.0.0"
fi

# Заменяем переменную в конфигурации
sed -i "s/\$EXTERNAL_IP/$EXTERNAL_IP/g" /etc/turnserver/turnserver.conf

# Запуск health check сервера в фоне
echo "Starting health check server..."
python3 /usr/local/bin/health_check.py &
HEALTH_CHECK_PID=$!

# Запуск TURN сервера
echo "Starting TURN server with external IP: $EXTERNAL_IP"
echo "TURN server configuration:"
cat /etc/turnserver/turnserver.conf

# Запуск с конфигурацией
turnserver -c /etc/turnserver/turnserver.conf &
TURN_PID=$!

# Функция для graceful shutdown
cleanup() {
    echo "Shutting down services..."
    kill $HEALTH_CHECK_PID 2>/dev/null
    kill $TURN_PID 2>/dev/null
    wait
    exit 0
}

# Обработка сигналов для graceful shutdown
trap cleanup SIGTERM SIGINT

# Ожидание завершения процессов
wait
