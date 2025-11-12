# A2A Essay Ecosystem

Два A2A агента: один пишет эссе, второй редактирует стиль.

## Запуск

```bash
# 1. Создать config.json с вашим OpenAI ключом
cp config.json.example config.json
# Отредактировать config.json

# 2. Запустить агенты
docker-compose up -d --build

# 3. Запустить тест
uv run python test_integration.py
```

## Ручной тест

```bash
# Прямой вызов Style Editor
curl -X POST http://localhost:8002/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"message/send","params":{"message":{"role":"user","messageId":"m1","parts":[{"text":"me go store","mime_type":"text/plain"}]}}}'

# Essay Writer → Style Editor (A2A цепочка)
curl -X POST http://localhost:8001/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"2","method":"message/send","params":{"message":{"role":"user","messageId":"m2","parts":[{"text":"роботы","mime_type":"text/plain"}]}}}'
```

## Архитектура

```
Essay Writer (8001) --A2A--> Style Editor (8002)
       ↓                            ↓
   OpenAI GPT-4              OpenAI GPT-4
```

Готово.
