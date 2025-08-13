#!/usr/bin/env python3
"""
Простой health check сервер для TURN сервера
Проверяет доступность CoTURN процесса
"""

import os
import subprocess
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Проверяем статус TURN сервера
            status = self.check_turn_server()
            
            response = {
                'status': 'healthy' if status else 'unhealthy',
                'timestamp': time.time(),
                'turn_server': 'running' if status else 'stopped',
                'service': 'voice-chat-turn'
            }
            
            self.wfile.write(json.dumps(response, indent=2).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def check_turn_server(self):
        """Проверяет, запущен ли TURN сервер"""
        try:
            # Проверяем процесс turnserver
            result = subprocess.run(
                ['pgrep', 'turnserver'], 
                capture_output=True, 
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def log_message(self, format, *args):
        # Отключаем логирование для health check
        pass

def run_health_server():
    """Запускает health check сервер"""
    port = int(os.environ.get('PORT', 8080))
    
    # Запускаем health check сервер в фоне
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"Health check server running on port {port}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Health check server stopped")
        server.server_close()

if __name__ == '__main__':
    run_health_server()
