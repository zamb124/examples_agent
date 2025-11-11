#!/usr/bin/env python3
"""
A2A клиент для запуска рабочего процесса написания эссе.
"""
import asyncio
import os

from a2a_sdk import A2AClient, TaskRequest


async def main():
    # Проверка наличия API ключа OpenAI
    if not os.getenv("OPENAI_API_KEY"):
        print("Ошибка: переменная окружения OPENAI_API_KEY не установлена")  # noqa: T201
        return

    # Создание A2A клиента
    client = A2AClient()

    # Запрос темы эссе у пользователя  # noqa: RUF003
    topic = input("Введите тему эссе: ").strip()
    if not topic:
        print("Тема не указана")  # noqa: T201
        return

    # Создание запроса к агенту-писателю эссе
    request = TaskRequest(
        agent_id="essay-writer-agent",
        capability_id="write_essay",
        parameters={"topic": topic},
    )

    print(f"Запрос эссе на тему: {topic}")  # noqa: T201

    try:
        # Отправка задачи и получение результата
        result = await client.send_task(request)
        print("\nЭссе готово:")  # noqa: T201,RUF001
        print("=" * 50)  # noqa: T201
        print(result["essay"])  # noqa: T201
        print("=" * 50)  # noqa: T201
    except Exception as e:  # noqa: BLE001
        print(f"Ошибка: {e}")  # noqa: T201

# Запуск основной функции
if __name__ == "__main__":
    asyncio.run(main())
