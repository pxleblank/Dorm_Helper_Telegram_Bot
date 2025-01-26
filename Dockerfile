# Используем базовый образ Python 3.11
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочий каталог
WORKDIR /app

# Копируем зависимости и исходный код
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект (исключения указаны в .dockerignore)
COPY . .

# Настраиваем Nginx
COPY nginx.conf /etc/nginx/sites-available/default

# Настраиваем Supervisor для управления процессами
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Собираем статические файлы Django (если используется)
RUN python manage.py collectstatic --noinput

# Открываем порты Для Nginx
EXPOSE 80
# (Порт бота зависит от конфигурации, обычно не требуется открывать)

# Запускаем Supervisor
CMD ["supervisord", "-n"]