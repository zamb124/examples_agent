# Используем Python 3.11 slim образ
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY pyproject.toml uv.lock ./

# Устанавливаем uv и зависимости
RUN pip install uv && uv sync --frozen --no-install-project

# Копируем исходный код
COPY app/ ./app/
COPY client/ ./client/
COPY config.json.example ./config.json.example

# Создаем пользователя для безопасности
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Открываем порт
EXPOSE 8000

# Команда запуска
CMD ["uv", "run", "uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]
