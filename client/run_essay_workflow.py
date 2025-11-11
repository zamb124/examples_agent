#!/usr/bin/env python3
"""
A2A клиент для запуска рабочего процесса написания эссе.
"""
import asyncio
from pathlib import Path

from a2a.client import ClientFactory, create_text_message_object
from a2a.types import TaskState


async def main():
    # Проверка наличия файла конфигурации
    config_path = Path(__file__).parent.parent / "config.json"
    if not config_path.exists():
        print("Ошибка: файл config.json не найден. Создайте его на основе config.json.example")  # noqa: T201
        return

    # Запрос темы эссе у пользователя  # noqa: RUF003
    topic = input("Введите тему эссе: ").strip()
    if not topic:
        print("Тема не указана")  # noqa: T201
        return

    print("Подключение к A2A агенту...")  # noqa: T201

    try:
        # Подключение к A2A агенту
        client = await ClientFactory.connect("http://localhost:8000")

        # Создание текстового сообщения
        message = create_text_message_object(content=topic)

        print(f"Отправка запроса на тему: {topic}")  # noqa: T201

        # Отправка сообщения и обработка ответа
        async for event in client.send_message(message):
            if isinstance(event, tuple):
                task, update = event
                if task.status.state == TaskState.completed:
                    if task.status.message:
                        response_text = task.status.message.parts[0].root.text
                        print("\nЭссе готово:")  # noqa: T201
                        print("=" * 50)  # noqa: T201
                        print(response_text)  # noqa: T201
                        print("=" * 50)  # noqa: T201
                    break
                if task.status.state == TaskState.failed:
                    print(f"Ошибка выполнения задачи: {task.status.message}")  # noqa: T201
                    break
            else:
                # Прямой ответ (не streaming)
                print(f"Прямой ответ: {event.parts[0].root.text}")  # noqa: T201
                break

        await client.close()

    except Exception as e:  # noqa: BLE001
        print(f"Ошибка: {e}")  # noqa: T201

# Запуск основной функции
if __name__ == "__main__":
    asyncio.run(main())
