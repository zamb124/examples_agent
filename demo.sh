#!/bin/bash

# Демонстрация A2A Essay Pipeline через Docker и curl
# Запуск: ./demo.sh

set -e

echo "🚀 A2A Essay Pipeline - Docker Demo"
echo "===================================="

# Проверяем наличие config.json
if [ ! -f "config.json" ]; then
    echo "❌ Ошибка: config.json не найден!"
    echo "Создайте config.json на основе config.json.example"
    exit 1
fi

# Проверяем Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен!"
    exit 1
fi

# Проверяем docker-compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ docker-compose не установлен!"
    exit 1
fi

echo "📦 Сборка и запуск контейнера..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d --build
else
    docker compose up -d --build
fi

echo "⏳ Ожидание запуска сервиса..."
sleep 10

# Проверяем здоровье сервиса
echo "🏥 Проверка здоровья сервиса..."
if curl -f -s http://localhost:8000/.well-known/agent-card.json > /dev/null; then
    echo "✅ Сервис запущен и здоров!"
else
    echo "❌ Сервис не отвечает!"
    exit 1
fi

echo ""
echo "🤖 Демонстрация A2A API вызовов:"
echo "================================="

# 1. Получить карту агента
echo ""
echo "1️⃣ Получение карты агента:"
echo "curl http://localhost:8000/.well-known/agent-card.json"
curl -s http://localhost:8000/.well-known/agent-card.json | python3 -m json.tool

# 2. Отправить задачу на написание эссе через A2A RPC
echo ""
echo "2️⃣ Отправка задачи через A2A RPC:"
echo "curl -X POST http://localhost:8000/rpc -H 'Content-Type: application/json' -d @essay_request.json"

# Создаем JSON запрос
cat > essay_request.json << 'EOF'
{
  "jsonrpc": "2.0",
  "id": "demo-request-1",
  "method": "send_message",
  "params": {
    "message": {
      "role": "user",
      "parts": [
        {
          "root": {
            "text": "машинное обучение",
            "mime_type": "text/plain"
          }
        }
      ]
    },
    "streaming": true
  }
}
EOF

echo "📤 Отправка запроса..."
curl -s -X POST http://localhost:8000/rpc \
  -H "Content-Type: application/json" \
  -d @essay_request.json | python3 -m json.tool

# Очистка
rm -f essay_request.json

echo ""
echo "3️⃣ Проверка логов контейнера:"
if command -v docker-compose &> /dev/null; then
    docker-compose logs --tail=20 a2a-essay-agent
else
    docker compose logs --tail=20 a2a-essay-agent
fi

echo ""
echo "🛑 Для остановки выполните:"
echo "docker-compose down  # или docker compose down"

echo ""
echo "✅ Демонстрация завершена!"
echo "Контейнер продолжает работать на порту 8000"
