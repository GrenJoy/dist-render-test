#!/usr/bin/env python3
"""
Скрипт для тестирования подключения к TURN серверу
Проверяет доступность и аутентификацию
"""

import socket
import requests
import sys
import time

def test_tcp_connection(host, port):
    """Тестирует TCP подключение"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"TCP тест ошибка: {e}")
        return False

def test_udp_connection(host, port):
    """Тестирует UDP подключение"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(10)
        sock.sendto(b"test", (host, port))
        sock.close()
        return True
    except Exception as e:
        print(f"UDP тест ошибка: {e}")
        return False

def test_turn_credentials(host, port, username, password):
    """Тестирует TURN аутентификацию"""
    try:
        # Простой тест STUN (без TURN)
        import subprocess
        result = subprocess.run([
            'curl', '-s', '--max-time', '10',
            f'stun:{host}:{port}'
        ], capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"TURN тест ошибка: {e}")
        return False

def main():
    print("=== TURN Server Connection Test ===")
    
    # Конфигурация
    host = "turn-dist.onrender.com"
    port = 3478
    username = "voicechat"
    password = "turn123456"
    
    print(f"Тестируем: {host}:{port}")
    print(f"Username: {username}")
    print(f"Password: {password}")
    print()
    
    # Тест 1: DNS разрешение
    print("1. Проверка DNS...")
    try:
        ip = socket.gethostbyname(host)
        print(f"   ✅ DNS: {host} -> {ip}")
    except Exception as e:
        print(f"   ❌ DNS ошибка: {e}")
        return
    
    # Тест 2: TCP подключение
    print("2. Тест TCP подключения...")
    if test_tcp_connection(host, port):
        print(f"   ✅ TCP: {host}:{port} доступен")
    else:
        print(f"   ❌ TCP: {host}:{port} недоступен")
    
    # Тест 3: UDP подключения
    print("3. Тест UDP подключения...")
    if test_udp_connection(host, port):
        print(f"   ✅ UDP: {host}:{port} доступен")
    else:
        print(f"   ❌ UDP: {host}:{port} недоступен")
    
    # Тест 4: TURN аутентификация
    print("4. Тест TURN аутентификации...")
    if test_turn_credentials(host, port, username, password):
        print(f"   ✅ TURN: аутентификация прошла")
    else:
        print(f"   ❌ TURN: аутентификация не прошла")
    
    print()
    print("=== Результаты ===")
    
    # Рекомендации
    print("\nРекомендации:")
    print("- Если TCP/UDP недоступны: проверьте firewall в Render")
    print("- Если TURN не работает: проверьте логи TURN сервера")
    print("- Для полного теста используйте WebRTC ICE trickle tool")
    print("  https://webrtc.github.io/samples/src/content/peerconnection/trickle-ice/")

if __name__ == "__main__":
    main()
