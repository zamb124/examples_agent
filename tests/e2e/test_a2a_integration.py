"""
End-to-end тесты для A2A Essay Pipeline согласно DoD.
Проверяют что контейнер агента можно встроить в A2A экосистему,
где клиент сможет найти и иницировать задачу.
"""
import asyncio
import pytest
import httpx
from unittest.mock import patch

from a2a.client import ClientFactory, create_text_message_object
from a2a.types import TaskState


class TestA2AIntegration:
    """Настоящие интеграционные тесты A2A экосистемы."""

    @pytest.fixture
    async def running_server(self):
        """Фикстура для запуска реального сервера."""
        # Импортируем здесь чтобы избежать проблем с конфигом при сборе тестов
        from app.server import app
        from app.config import OPENAI_API_KEY

        # Проверяем что API ключ настроен
        assert OPENAI_API_KEY, "OpenAI API ключ не настроен в config.json"

        # Запускаем сервер в фоне
        from uvicorn import Config, Server
        config = Config(app=app, host="127.0.0.1", port=8001, log_level="error")
        server = Server(config)

        # Запускаем сервер в отдельной задаче
        server_task = asyncio.create_task(server.serve())

        # Ждем запуска сервера
        await asyncio.sleep(1)

        try:
            yield "http://127.0.0.1:8001"
        finally:
            # Останавливаем сервер
            server.should_exit = True
            await server_task
            await asyncio.sleep(0.1)

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_a2a_agent_discovery(self, running_server):
        """Тест что клиент может найти агента в A2A экосистеме."""
        server_url = running_server

        # Подключаемся к агенту
        client = await ClientFactory.connect(server_url)

        try:
            # Проверяем что агент найден и имеет карту
            card = await client.get_card()
            assert card is not None
            assert card.name == "A2A Essay Pipeline"
            assert len(card.skills) == 2

            # Проверяем навыки
            skill_names = {skill.name for skill in card.skills}
            assert "Write Essay" in skill_names
            assert "Edit Style" in skill_names

        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_a2a_write_essay_workflow(self, running_server):
        """Тест полного рабочего процесса написания эссе через A2A."""
        server_url = running_server

        client = await ClientFactory.connect(server_url)

        try:
            # Отправляем задачу на написание эссе
            message = create_text_message_object(content="Write an essay about artificial intelligence")

            # Получаем ответ
            response_received = False
            async for event in client.send_message(message):
                if isinstance(event, tuple):
                    task, update = event
                    if task.status.state == TaskState.completed:
                        assert task.status.message is not None
                        response_text = task.status.message.parts[0].root.text
                        assert "эссе" in response_text.lower() or "essay" in response_text.lower()
                        assert len(response_text) > 50  # Проверяем что ответ не пустой
                        response_received = True
                        break
                    elif task.status.state == TaskState.failed:
                        pytest.fail(f"Задача завершилась с ошибкой: {task.status.message}")

            assert response_received, "Не получили ответ от агента"

        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_a2a_edit_style_workflow(self, running_server):
        """Тест рабочего процесса редактирования стиля через A2A."""
        server_url = running_server

        client = await ClientFactory.connect(server_url)

        try:
            # Отправляем задачу на редактирование стиля
            test_text = "This is bad text with many errors. It need to be improved."
            message = create_text_message_object(content=test_text)

            # Получаем ответ
            response_received = False
            async for event in client.send_message(message):
                if isinstance(event, tuple):
                    task, update = event
                    if task.status.state == TaskState.completed:
                        assert task.status.message is not None
                        response_text = task.status.message.parts[0].root.text
                        assert "отредактирован" in response_text.lower() or "edited" in response_text.lower()
                        assert len(response_text) > len(test_text)  # Проверяем что текст был обработан
                        response_received = True
                        break
                    elif task.status.state == TaskState.failed:
                        pytest.fail(f"Задача завершилась с ошибкой: {task.status.message}")

            assert response_received, "Не получили ответ от агента"

        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_a2a_agent_card_endpoint(self, running_server):
        """Тест что агент карта доступна по стандартному A2A endpoint."""
        server_url = running_server

        async with httpx.AsyncClient() as http_client:
            # Проверяем стандартный A2A endpoint для карты агента
            response = await http_client.get(f"{server_url}/.well-known/agent-card.json")
            assert response.status_code == 200

            card_data = response.json()
            assert card_data["name"] == "A2A Essay Pipeline"
            assert len(card_data["skills"]) == 2

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_a2a_concurrent_requests(self, running_server):
        """Тест одновременной обработки нескольких запросов."""
        server_url = running_server

        async def process_request(topic: str):
            client = await ClientFactory.connect(server_url)
            try:
                message = create_text_message_object(content=topic)
                async for event in client.send_message(message):
                    if isinstance(event, tuple):
                        task, update = event
                        if task.status.state == TaskState.completed:
                            return True
                        elif task.status.state == TaskState.failed:
                            return False
                return False
            finally:
                await client.close()

        # Запускаем несколько одновременных запросов
        tasks = [
            process_request("Write about machine learning"),
            process_request("Write about quantum computing"),
            process_request("Write about blockchain technology"),
        ]

        results = await asyncio.gather(*tasks)

        # Все запросы должны завершиться успешно
        assert all(results), "Не все одновременные запросы завершились успешно"

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_a2a_error_handling(self, running_server):
        """Тест обработки ошибок в A2A экосистеме."""
        server_url = running_server

        # Мокаем OpenAI API для генерации ошибки
        with patch('app.agents.essay_agent.AsyncOpenAI') as mock_openai:
            mock_client = mock_openai.return_value
            mock_client.chat.completions.create = asyncio.coroutine(
                lambda **kwargs: (_ for _ in ()).throw(Exception("OpenAI API Error"))
            )()

            client = await ClientFactory.connect(server_url)

            try:
                message = create_text_message_object(content="Write an essay about AI")

                error_handled = False
                async for event in client.send_message(message):
                    if isinstance(event, tuple):
                        task, update = event
                        if task.status.state == TaskState.failed:
                            assert task.status.message is not None
                            error_text = task.status.message.parts[0].root.text
                            assert "ошибка" in error_text.lower() or "error" in error_text.lower()
                            error_handled = True
                            break

                assert error_handled, "Ошибка не была правильно обработана"

            finally:
                await client.close()
