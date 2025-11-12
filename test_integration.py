import asyncio
import httpx
from datetime import datetime


def print_step(step_num: int, title: str):
    print(f"\n{'='*60}")
    print(f"ШАГ {step_num}: {title}")
    print(f"{'='*60}")


def print_request(url: str, payload: dict):
    print(f"\n📤 Отправляем запрос:")
    print(f"   URL: {url}")
    print(f"   Метод: {payload['method']}")
    print(f"   Сообщение: {payload['params']['message']['parts'][0]['text']}")


def print_response(result: dict, response_time: float):
    status = result["result"]["status"]["state"]
    message = result["result"]["status"]["message"]["parts"][0]["text"]
    
    print(f"\n📥 Получен ответ за {response_time:.2f} сек:")
    print(f"   Статус: {status}")
    print(f"   Длина ответа: {len(message)} символов")
    print(f"\n📝 Текст ответа:")
    print("-" * 60)
    if len(message) > 500:
        print(message[:500] + "\n...(текст обрезан)")
    else:
        print(message)
    print("-" * 60)


async def test_agent_cards():
    print_step(0, "Проверка доступности агентов")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        print("\n🔍 Проверяем Essay Writer Agent (порт 8001)...")
        essay_response = await client.get("http://localhost:8001/.well-known/agent-card.json")
        essay_card = essay_response.json()
        print(f"   ✅ {essay_card['name']}")
        print(f"   📋 Описание: {essay_card['description']}")
        print(f"   🎯 Навыки: {', '.join([s['name'] for s in essay_card['skills']])}")
        
        print("\n🔍 Проверяем Style Editor Agent (порт 8002)...")
        style_response = await client.get("http://localhost:8002/.well-known/agent-card.json")
        style_card = style_response.json()
        print(f"   ✅ {style_card['name']}")
        print(f"   📋 Описание: {style_card['description']}")
        print(f"   🎯 Навыки: {', '.join([s['name'] for s in style_card['skills']])}")


async def test_style_editor_direct():
    print_step(1, "Тестирование Style Editor агента напрямую")
    
    input_text = "me go store yesterday and buy many thing"
    payload = {
        "jsonrpc": "2.0",
        "id": "test-1",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "messageId": "msg-1",
                "parts": [{"text": input_text, "mime_type": "text/plain"}]
            }
        }
    }
    
    print_request("http://localhost:8002/", payload)
    print("\n⏳ Ожидаем ответ от Style Editor...")
    
    start_time = datetime.now()
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "http://localhost:8002/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
    response_time = (datetime.now() - start_time).total_seconds()
    
    result = response.json()
    assert response.status_code == 200, f"❌ Неверный HTTP статус: {response.status_code}"
    assert result["result"]["status"]["state"] == "completed", "❌ Задача не завершена"
    
    print_response(result, response_time)
    
    edited_text = result["result"]["status"]["message"]["parts"][0]["text"]
    assert "Текст отредактирован:" in edited_text
    print("\n✅ Style Editor успешно отредактировал текст!")


async def test_essay_writer_chain():
    print_step(2, "Тестирование A2A цепочки: Essay Writer → Style Editor")
    
    topic = "квантовые компьютеры"
    payload = {
        "jsonrpc": "2.0",
        "id": "test-2",
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "messageId": "msg-2",
                "parts": [{"text": topic, "mime_type": "text/plain"}]
            }
        }
    }
    
    print_request("http://localhost:8001/", payload)
    print("\n⏳ Ожидаем ответ от Essay Writer...")
    print("   (Essay Writer сгенерирует эссе и вызовет Style Editor для редактирования)")
    
    start_time = datetime.now()
    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(
            "http://localhost:8001/",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
    response_time = (datetime.now() - start_time).total_seconds()
    
    result = response.json()
    assert response.status_code == 200, f"❌ Неверный HTTP статус: {response.status_code}"
    assert result["result"]["status"]["state"] == "completed", "❌ Задача не завершена"
    
    print_response(result, response_time)
    
    final_text = result["result"]["status"]["message"]["parts"][0]["text"]
    
    # Проверяем что оба агента участвовали
    print("\n🔍 Проверяем участие обоих агентов:")
    
    essay_marker = "написано и отредактировано" in final_text
    style_marker = "Текст отредактирован:" in final_text
    
    print(f"   {'✅' if essay_marker else '❌'} Essay Writer обработал запрос: {essay_marker}")
    print(f"   {'✅' if style_marker else '❌'} Style Editor отредактировал текст: {style_marker}")
    print(f"   📏 Итоговая длина эссе: {len(final_text)} символов")
    
    assert essay_marker, "❌ Essay Writer не участвовал в обработке"
    assert style_marker, "❌ Style Editor не участвовал в обработке"
    assert len(final_text) > 300, "❌ Текст слишком короткий"
    
    print("\n✅ A2A цепочка работает корректно!")
    print("   Essay Writer → сгенерировал эссе")
    print("   Essay Writer → вызвал Style Editor через A2A")
    print("   Style Editor → отредактировал эссе")
    print("   Essay Writer → вернул итоговый результат")


async def main():
    print("\n" + "🚀" * 30)
    print("ИНТЕРАКТИВНЫЙ ИНТЕГРАЦИОННЫЙ ТЕСТ A2A ЭКОСИСТЕМЫ")
    print("🚀" * 30)
    print(f"\n⏰ Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        await test_agent_cards()
        await test_style_editor_direct()
        await test_essay_writer_chain()
        
        print("\n" + "="*60)
        print("✅ ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("="*60)
        print("\n📊 Итоги:")
        print("   ✅ Агенты доступны и корректно настроены")
        print("   ✅ Style Editor работает напрямую")
        print("   ✅ A2A цепочка Essay Writer → Style Editor функционирует")
        print("   ✅ Экосистема полностью работоспособна")
        print("\n" + "🎉" * 30 + "\n")
        
    except AssertionError as e:
        print(f"\n{'='*60}")
        print(f"❌ ТЕСТ ПРОВАЛЕН")
        print(f"{'='*60}")
        print(f"Причина: {e}\n")
        raise
    except httpx.ConnectError as e:
        print(f"\n{'='*60}")
        print(f"❌ ОШИБКА ПОДКЛЮЧЕНИЯ")
        print(f"{'='*60}")
        print(f"Не удалось подключиться к агентам.")
        print(f"Убедитесь что docker-compose up -d запущен!\n")
        print(f"Детали: {e}\n")
        raise
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ НЕОЖИДАННАЯ ОШИБКА")
        print(f"{'='*60}")
        print(f"{type(e).__name__}: {e}\n")
        raise


if __name__ == "__main__":
    asyncio.run(main())
