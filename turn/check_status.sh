#!/bin/bash

# Скрипт для проверки статуса TURN сервера

echo "=== TURN Server Status Check ==="
echo "Timestamp: $(date)"
echo

# Проверяем переменные окружения
echo "Environment Variables:"
echo "TURN_USERNAME: ${TURN_USERNAME:-NOT_SET}"
echo "TURN_PASSWORD: ${TURN_PASSWORD:+[SET]}"
echo "EXTERNAL_IP: ${EXTERNAL_IP:-NOT_SET}"
echo

# Проверяем процессы
echo "Running Processes:"
if pgrep -f "turnserver" > /dev/null; then
    echo "✅ TURN server: RUNNING"
    pgrep -f "turnserver" | xargs ps -p
else
    echo "❌ TURN server: NOT RUNNING"
fi

if pgrep -f "health_check.py" > /dev/null; then
    echo "✅ Health check: RUNNING"
    pgrep -f "health_check.py" | xargs ps -p
else
    echo "❌ Health check: NOT RUNNING"
fi

echo

# Проверяем порты
echo "Port Status:"
if netstat -tuln | grep ":3478 " > /dev/null; then
    echo "✅ Port 3478 (TCP): LISTENING"
else
    echo "❌ Port 3478 (TCP): NOT LISTENING"
fi

if netstat -tuln | grep ":3478 " > /dev/null; then
    echo "✅ Port 3478 (UDP): LISTENING"
else
    echo "❌ Port 3478 (UDP): NOT LISTENING"
fi

echo

# Проверяем конфигурацию
echo "Configuration:"
if [ -f "/etc/turnserver/turnserver.conf" ]; then
    echo "✅ Config file exists"
    echo "External IP in config:"
    grep "external-ip" /etc/turnserver/turnserver.conf || echo "No external-ip line found"
else
    echo "❌ Config file not found"
fi

echo

# Проверяем логи (последние 10 строк)
echo "Recent Logs (last 10 lines):"
if [ -f "/var/log/turnserver/turnserver.log" ]; then
    tail -10 /var/log/turnserver/turnserver.log
else
    echo "No log file found"
fi

echo
echo "=== Status Check Complete ==="
