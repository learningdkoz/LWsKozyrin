# Используем официальный образ Python 3.11 как базовый
FROM python:3.11-slim

# Устанавливаем переменные окружения
# PYTHONUNBUFFERED - отключает буферизацию вывода Python (логи сразу видны)
# PYTHONDONTWRITEBYTECODE - предотвращает создание .pyc файлов
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл с зависимостями
COPY requirements.txt .

# Обновляем pip и устанавливаем зависимости
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем весь проект в контейнер
COPY . .

# Делаем entrypoint.sh исполняемым
RUN chmod +x entrypoint.sh

# Открываем порт для приложения
EXPOSE 8000

# Указываем entrypoint скрипт для запуска приложения
ENTRYPOINT ["./entrypoint.sh"]
