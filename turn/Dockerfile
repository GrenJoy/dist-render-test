FROM ubuntu:22.04

# Установка зависимостей
RUN apt-get update && apt-get install -y \
    wget \
    build-essential \
    libssl-dev \
    libevent-dev \
    libhiredis-dev \
    python3 \
    python3-pip \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Скачивание и компиляция CoTURN
WORKDIR /tmp
RUN wget https://github.com/coturn/coturn/releases/download/4.6.2/coturn-4.6.2.tar.gz \
    && tar -xzf coturn-4.6.2.tar.gz \
    && cd coturn-4.6.2 \
    && ./configure \
    && make \
    && make install

# Создание пользователя
RUN useradd -r -s /bin/false turnserver

# Создание директорий
RUN mkdir -p /var/log/turnserver /etc/turnserver \
    && chown -R turnserver:turnserver /var/log/turnserver /etc/turnserver

# Копирование файлов
COPY turnserver.conf /etc/turnserver/
COPY start_turn.sh /usr/local/bin/
COPY health_check.py /usr/local/bin/

# Установка прав
RUN chmod +x /usr/local/bin/start_turn.sh \
    && chmod +x /usr/local/bin/health_check.py \
    && chown turnserver:turnserver /etc/turnserver/turnserver.conf

# Открытие портов
EXPOSE 3478 3478/udp 5349 5349/udp 8080

# Переключение на пользователя
USER turnserver

# Запуск TURN сервера и health check
CMD ["/usr/local/bin/start_turn.sh"]
