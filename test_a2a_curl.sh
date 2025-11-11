#!/bin/bash

# Тестирование A2A API через curl
# Использование: ./test_a2a_curl.sh [topic]

set -e

TOPIC="${1:-'искусственный интеллект'}"
BASE_URL="http://localhost:8000"

echo "🧪 Тестирование A2A Essay Pipeline через curl"
echo "=============================================="

# Функция для отправки A2A RPC запроса
send_a2a_request() {
    local topic="$1"
    local request_id="$(date +%s)"

    cat > /tmp/a2a_request.json << EOF
{
  "jsonrpc": "2.0",
  "id": "${request_id}",
  "method": "send_message",
  "params": {
    "message": {
      "role": "user",
      "parts": [
        {
          "root": {
            "text": "${topic}",
            "mime_type": "text/plain"
          }
        }
      ]
    },
    "streaming": true
  }
}
EOF

    echo "📤 Отправка запроса: '${topic}'"
    echo "🔗 URL: ${BASE_URL}/rpc"
    echo "📄 Запрос:"
    cat /tmp/a2a_request.json | python3 -m json.tool
    echo ""

    echo "📥 Ответ:"
    curl -s -X POST "${BASE_URL}/rpc" \
         -H "Content-Type: application/json" \
         -d @/tmp/a2a_request.json | python3 -m json.tool

    rm -f /tmp/a2a_request.json
}

# Проверяем доступность сервиса
echo "1️⃣ Проверка доступности сервиса..."
if curl -f -s "${BASE_URL}/.well-known/agent-card.json" > /dev/null; then
    echo "✅ Сервис доступен"
else
    echo "❌ Сервис недоступен на ${BASE_URL}"
    echo "Запустите: docker-compose up -d"
    exit 1
fi

# Получаем карту агента
echo ""
echo "2️⃣ Получение карты агента..."
curl -s "${BASE_URL}/.well-known/agent-card.json" | python3 -m json.tool

# Тестируем разные темы
echo ""
echo "3️⃣ Тестирование генерации эссе..."

send_a2a_request "${TOPIC}"

echo ""
echo "4️⃣ Тестирование редактирования стиля..."
echo "(Отправляем готовый текст для редактирования)"

cat > /tmp/style_request.json << 'EOF'
{
  "jsonrpc": "2.0",
  "id": "style-test-1",
  "method": "send_message",
  "params": {
    "message": {
      "role": "user",
      "parts": [
        {
          "root": {
            "text": "This text have many grammar mistake and need style improvement for better readability and flow.",
            "mime_type": "text/plain"
          }
        }
      ]
    },
    "streaming": true
  }
}
EOF

echo "📤 Отправка текста для редактирования стиля..."
curl -s -X POST "${BASE_URL}/rpc" \
     -H "Content-Type: application/json" \
     -d @/tmp/style_request.json | python3 -m json.tool

rm -f /tmp/style_request.json

echo ""
echo "✅ Тестирование завершено!"
echo ""
echo "💡 Примечание: Агент внутри контейнера:"
echo "   - Получает задачу через A2A RPC"
echo "   - EssayAgent вызывает OpenAI для генерации текста"
echo "   - StyleEditorAgent редактирует стиль через OpenAI"
echo "   - Возвращает результат через A2A streaming"
