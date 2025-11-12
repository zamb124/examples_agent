FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install uv && uv sync --frozen --no-install-project

COPY app/ ./app/
COPY config.json.example ./config.json.example

RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

EXPOSE 8001 8002

CMD ["uv", "run", "uvicorn", "app.essay_writer_server:app", "--host", "0.0.0.0", "--port", "8001"]
