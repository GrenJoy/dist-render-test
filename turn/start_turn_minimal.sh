#!/bin/bash

# Минимальный скрипт запуска TURN сервера
# Без автоматического получения IP

echo "=== TURN Server Startup Script (Minimal) ==="
echo "Timestamp: $(date)"

# Функция для логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Проверяем переменные окружения
log "Checking environment variables..."

if [ -z "$TURN_PASSWORD" ]; then
    log "ERROR: TURN_PASSWORD not set"
    exit 1
fi

log "TURN_PASSWORD: [SET]"
log "TURN_USERNAME: ${TURN_USERNAME:-voicechat}"

# Обрабатываем EXTERNAL_IP
if [ -n "$EXTERNAL_IP" ] && [ "$EXTERNAL_IP" != "0.0.0.0" ]; then
    log "Using EXTERNAL_IP from environment: $EXTERNAL_IP"
    # Заменяем переменную в конфигурации
    sed -i "s/\$EXTERNAL_IP/$EXTERNAL_IP/g" /etc/turnserver/turnserver.conf
else
    log "EXTERNAL_IP not set or invalid, removing from config"
    # Убираем строку external-ip, чтобы TURN сервер сам определил
    sed -i '/external-ip=/d' /etc/turnserver/turnserver.conf
fi

# Заменяем пароль
sed -i "s/\${TURN_PASSWORD}/$TURN_PASSWORD/g" /etc/turnserver/turnserver.conf

# Показываем финальную конфигурацию
log "Final TURN server configuration:"
echo "----------------------------------------"
cat /etc/turnserver/turnserver.conf
echo "----------------------------------------"

# Запускаем health check сервер
log "Starting health check server..."
python3 /usr/local/bin/health_check.py &
HEALTH_CHECK_PID=$!
log "Health check server started with PID: $HEALTH_CHECK_PID"

# Запускаем TURN сервер
log "Starting TURN server..."
turnserver -c /etc/turnserver/turnserver.conf &
TURN_PID=$!
log "TURN server started with PID: $TURN_PID"

# Функция для graceful shutdown
cleanup() {
    log "Received shutdown signal, cleaning up..."
    
    if [ -n "$HEALTH_CHECK_PID" ]; then
        log "Stopping health check server (PID: $HEALTH_CHECK_PID)..."
        kill $HEALTH_CHECK_PID 2>/dev/null || true
    fi
    
    if [ -n "$TURN_PID" ]; then
        log "Stopping TURN server (PID: $TURN_PID)..."
        kill $TURN_PID 2>/dev/null || true
    fi
    
    log "Waiting for processes to finish..."
    wait 2>/dev/null || true
    
    log "Cleanup completed"
    exit 0
}

# Обработка сигналов
trap cleanup SIGTERM SIGINT

log "All services started successfully"
log "Waiting for processes..."

# Ожидаем завершения процессов
wait
