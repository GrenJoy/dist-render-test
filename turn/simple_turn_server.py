#!/usr/bin/env python3
"""
Простой TURN сервер на Python
Работает без сложных Docker зависимостей
"""

import os
import subprocess
import signal
import sys
import time
from pathlib import Path

def log(message):
    """Логирование с временной меткой"""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def check_environment():
    """Проверка переменных окружения"""
    log("Checking environment variables...")
    
    turn_password = os.environ.get('TURN_PASSWORD')
    if not turn_password:
        log("ERROR: TURN_PASSWORD not set")
        return False
    
    log("✅ TURN_PASSWORD: [SET]")
    log(f"✅ TURN_USERNAME: {os.environ.get('TURN_USERNAME', 'voicechat')}")
    return True

def update_config():
    """Обновление конфигурации TURN сервера"""
    log("Updating TURN server configuration...")
    
    config_file = "/etc/turnserver/turnserver.conf"
    
    # Читаем конфигурацию
    with open(config_file, 'r') as f:
        config = f.read()
    
    # Заменяем пароль
    config = config.replace('${TURN_PASSWORD}', os.environ.get('TURN_PASSWORD', 'turn123456'))
    
    # Обрабатываем EXTERNAL_IP
    external_ip = os.environ.get('EXTERNAL_IP')
    if external_ip and external_ip != "0.0.0.0":
        log(f"Using EXTERNAL_IP: {external_ip}")
        config = config.replace('$EXTERNAL_IP', external_ip)
    else:
        log("EXTERNAL_IP not set, TURN server will auto-detect")
        # Убираем строку external-ip
        lines = config.split('\n')
        lines = [line for line in lines if not line.startswith('external-ip=')]
        config = '\n'.join(lines)
    
    # Записываем обновленную конфигурацию
    with open(config_file, 'w') as f:
        f.write(config)
    
    log("Configuration updated successfully")
    return True

def start_health_check():
    """Запуск health check сервера"""
    log("Starting health check server...")
    try:
        health_check = subprocess.Popen([
            'python3', '/usr/local/bin/health_check.py'
        ])
        log(f"Health check server started with PID: {health_check.pid}")
        return health_check
    except Exception as e:
        log(f"Failed to start health check: {e}")
        return None

def start_turn_server():
    """Запуск TURN сервера"""
    log("Starting TURN server...")
    try:
        turn_server = subprocess.Popen([
            'turnserver', '-c', '/etc/turnserver/turnserver.conf'
        ])
        log(f"TURN server started with PID: {turn_server.pid}")
        return turn_server
    except Exception as e:
        log(f"Failed to start TURN server: {e}")
        return None

def cleanup(health_check, turn_server):
    """Очистка при завершении"""
    log("Cleaning up...")
    
    if health_check:
        log("Stopping health check server...")
        health_check.terminate()
        health_check.wait()
    
    if turn_server:
        log("Stopping TURN server...")
        turn_server.terminate()
        turn_server.wait()
    
    log("Cleanup completed")

def main():
    """Основная функция"""
    log("=== Simple TURN Server Startup ===")
    
    # Проверяем переменные окружения
    if not check_environment():
        sys.exit(1)
    
    # Обновляем конфигурацию
    if not update_config():
        log("Failed to update configuration")
        sys.exit(1)
    
    # Запускаем сервисы
    health_check = start_health_check()
    turn_server = start_turn_server()
    
    if not turn_server:
        log("ERROR: Failed to start TURN server")
        cleanup(health_check, None)
        sys.exit(1)
    
    log("All services started successfully")
    log("Waiting for processes...")
    
    # Обработка сигналов
    def signal_handler(signum, frame):
        log(f"Received signal {signum}")
        cleanup(health_check, turn_server)
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Ожидаем завершения TURN сервера
        turn_server.wait()
    except KeyboardInterrupt:
        log("Interrupted by user")
    finally:
        cleanup(health_check, turn_server)

if __name__ == "__main__":
    main()
