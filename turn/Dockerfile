FROM coturn/coturn:latest

# Устанавливаем необходимые инструменты
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    python3 \
    python3-pip \
    dnsutils \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов
COPY turnserver.conf /etc/turnserver/
COPY start_turn_simple.sh /usr/local/bin/
COPY health_check.py /usr/local/bin/

# Делаем скрипт исполняемым
RUN chmod +x /usr/local/bin/start_turn_simple.sh

# Открытие портов
EXPOSE 3478 3478/udp 5349 5349/udp

# Запуск через упрощенный скрипт
CMD ["/usr/local/bin/start_turn_simple.sh"]
