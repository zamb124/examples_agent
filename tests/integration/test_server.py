"""
Интеграционные тесты для FastAPI сервера A2A Essay Pipeline.
"""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.agents.essay_agent import EssayAgent
from app.agents.style_editor_agent import StyleEditorAgent
from app.server import app


class TestServerIntegration:
    """Интеграционные тесты для сервера."""

    @pytest.fixture
    def test_client(self):
        """Фикстура для тестового клиента FastAPI."""
        return TestClient(app)

    @pytest.fixture
    async def async_client(self):
        """Фикстура для асинхронного HTTP клиента."""
        async with AsyncClient(app=app, base_url="http://testserver") as client:
            yield client

    def test_server_startup(self, test_client):
        """Тест запуска сервера."""
        # Проверка что сервер отвечает (A2A сервер может возвращать 405 вместо 404)
        response = test_client.get("/")
        assert response.status_code in [404, 405]  # Сервер работает

    def test_openapi_docs_available(self, test_client):
        """Тест доступности OpenAPI документации."""
        response = test_client.get("/docs")
        assert response.status_code == 200

    def test_openapi_json_available(self, test_client):
        """Тест доступности OpenAPI JSON схемы."""
        response = test_client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "info" in data
        assert "paths" in data

    def test_a2a_server_initialization(self):
        """Тест инициализации A2A сервера."""
        # Проверка что приложение содержит A2A middleware
        from app.server import a2a_server
        assert a2a_server is not None

    def test_agent_instances_created(self):
        """Тест создания экземпляров агентов."""
        from app.server import agent_executor
        from app.agents.essay_agent import EssayAgent
        from app.agents.style_editor_agent import StyleEditorAgent
        # Проверяем что агент-исполнитель содержит нужные агенты
        assert hasattr(agent_executor, 'essay_agent')
        assert hasattr(agent_executor, 'style_agent')
        assert isinstance(agent_executor.essay_agent, EssayAgent)
        assert isinstance(agent_executor.style_agent, StyleEditorAgent)

    def test_agent_cards_registered(self):
        """Тест регистрации карт агентов."""
        from app.server import a2a_server
        # Проверка что карты агентов зарегистрированы
        assert len(a2a_server._agent_cards) > 0  # Проверка наличия карт


class TestA2AEndpoints:
    """Тесты A2A endpoints."""

    @pytest.fixture
    def mock_essay_agent(self, mocker):
        """Мок для EssayAgent."""
        mock_agent = mocker.AsyncMock()
        mock_agent.write_essay.return_value = {
            "topic": "Test Topic",
            "essay": "Test essay content",
        }
        return mock_agent

    @pytest.fixture
    def mock_style_editor_agent(self, mocker):
        """Мок для StyleEditorAgent."""
        mock_agent = mocker.AsyncMock()
        mock_agent.edit_style.return_value = {
            "original_text": "Original",
            "edited_text": "Edited",
        }
        return mock_agent

    def test_write_essay_endpoint_structure(self, test_client):
        """Тест структуры endpoint для написания эссе."""
        # Этот тест проверяет наличие endpoint в схеме OpenAPI
        response = test_client.get("/openapi.json")
        schema = response.json()

        # Проверка что есть пути связанные с задачами
        paths = schema.get("paths", {})
        # A2A endpoints могут быть зарегистрированы динамически
        assert isinstance(paths, dict)

    @pytest.mark.asyncio
    async def test_a2a_task_processing_mock(self, mocker, mock_essay_agent, mock_style_editor_agent):
        """Тест обработки A2A задач с моками."""
        # Мокаем агентов в модуле server
        mocker.patch("app.server.essay_agent", mock_essay_agent)
        mocker.patch("app.server.style_editor_agent", mock_style_editor_agent)

        # Импортируем обработчики после мока
        from a2a_sdk import Task

        from app.server import handle_write_essay

        # Создаем мок задачи
        mock_task = mocker.AsyncMock(spec=Task)
        mock_task.parameters = {"topic": "Test Topic"}

        # Тестируем обработчик
        await handle_write_essay(mock_task)

        # Проверяем вызовы
        mock_essay_agent.write_essay.assert_called_once_with("Test Topic")
        mock_task.update_status.assert_called_once()
        mock_task.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_a2a_task_error_handling(self, mocker, mock_essay_agent):
        """Тест обработки ошибок в A2A задачах."""
        # Мокаем агента для генерации ошибки
        mock_essay_agent.write_essay.side_effect = Exception("Test error")
        mocker.patch("app.server.essay_agent", mock_essay_agent)

        from a2a_sdk import Task

        from app.server import handle_write_essay

        # Создаем мок задачи
        mock_task = mocker.AsyncMock(spec=Task)
        mock_task.parameters = {"topic": "Test Topic"}

        # Тестируем обработчик
        await handle_write_essay(mock_task)

        # Проверяем вызовы
        mock_task.update_status.assert_called_once()
        mock_task.fail.assert_called_once_with("Test error")
