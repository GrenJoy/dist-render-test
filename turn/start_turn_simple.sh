#!/bin/bash

# Упрощенный скрипт запуска TURN сервера
# Работает даже без curl

echo "=== TURN Server Startup Script (Simple) ==="
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

# Получаем внешний IP несколькими способами
log "Getting external IP address..."

EXTERNAL_IP=""

# Способ 1: Через переменную окружения
if [ -n "$EXTERNAL_IP" ] && [ "$EXTERNAL_IP" != "0.0.0.0" ]; then
    log "Using EXTERNAL_IP from environment: $EXTERNAL_IP"
else
    # Способ 2: Через curl (если доступен)
    if command -v curl >/dev/null 2>&1; then
        log "Trying curl to get external IP..."
        for service in "ifconfig.me" "icanhazip.com" "ipinfo.io/ip"; do
            log "Trying $service with curl..."
            EXTERNAL_IP=$(curl -s --max-time 10 "$service" 2>/dev/null || echo "")
            if [ -n "$EXTERNAL_IP" ] && [ "$EXTERNAL_IP" != "0.0.0.0" ]; then
                log "Successfully got IP from $service: $EXTERNAL_IP"
                break
            fi
        done
    fi
    
    # Способ 3: Через wget (если доступен)
    if [ -z "$EXTERNAL_IP" ] && command -v wget >/dev/null 2>&1; then
        log "Trying wget to get external IP..."
        for service in "ifconfig.me" "icanhazip.com" "ipinfo.io/ip"; do
            log "Trying $service with wget..."
            EXTERNAL_IP=$(wget -qO- --timeout=10 "$service" 2>/dev/null || echo "")
            if [ -n "$EXTERNAL_IP" ] && [ "$EXTERNAL_IP" != "0.0.0.0" ]; then
                log "Successfully got IP from $service: $EXTERNAL_IP"
                break
            fi
        done
    fi
    
    # Способ 4: Через DNS (последний резерв)
    if [ -z "$EXTERNAL_IP" ]; then
        log "Trying DNS method to get external IP..."
        # Используем внешний DNS сервер для определения нашего IP
        EXTERNAL_IP=$(dig +short TXT o-o.myaddr.l.google.com @ns1.google.com 2>/dev/null | tr -d '"' || echo "")
        if [ -n "$EXTERNAL_IP" ] && [ "$EXTERNAL_IP" != "0.0.0.0" ]; then
            log "Successfully got IP via DNS: $EXTERNAL_IP"
        fi
    fi
fi

# Если все способы не сработали, используем fallback
if [ -z "$EXTERNAL_IP" ] || [ "$EXTERNAL_IP" = "0.0.0.0" ]; then
    log "WARNING: Could not determine external IP automatically"
    log "Using fallback: will let TURN server auto-detect"
    EXTERNAL_IP=""
fi

# Обновляем конфигурацию
log "Updating TURN server configuration..."
if [ -n "$EXTERNAL_IP" ]; then
    sed -i "s/\$EXTERNAL_IP/$EXTERNAL_IP/g" /etc/turnserver/turnserver.conf
    log "Set external-ip to: $EXTERNAL_IP"
else
    # Убираем строку external-ip, чтобы TURN сервер сам определил
    sed -i '/external-ip=/d' /etc/turnserver/turnserver.conf
    log "Removed external-ip line, TURN server will auto-detect"
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
