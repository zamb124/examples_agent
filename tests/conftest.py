"""
Конфигурация pytest для тестирования A2A Essay Pipeline.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.essay_agent import EssayAgent
from app.agents.style_editor_agent import StyleEditorAgent


@pytest.fixture
def mock_openai_client():
    """Мок для OpenAI клиента."""
    client = AsyncMock()
    # Настройка мока для ответа chat completions
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test response"
    client.chat.completions.create = AsyncMock(return_value=mock_response)
    return client


@pytest.fixture
def mock_a2a_client():
    """Мок для A2A клиента."""
    client = AsyncMock()
    client.send_task = AsyncMock(return_value={"edited_text": "Edited test text"})
    return client


@pytest.fixture
def mock_config():
    """Мок для конфигурации."""
    with patch("app.config.OPENAI_API_KEY", "test-api-key"):
        yield


@pytest.fixture
async def essay_agent(mock_openai_client):
    """Фикстура для EssayAgent с моками."""
    with patch("app.config.OPENAI_API_KEY", "test-api-key"):
        agent = EssayAgent()
        agent.client = mock_openai_client
        return agent


@pytest.fixture
async def style_editor_agent(mock_openai_client):
    """Фикстура для StyleEditorAgent с моками."""
    with patch("app.config.OPENAI_API_KEY", "test-api-key"):
        agent = StyleEditorAgent()
        agent.client = mock_openai_client
        return agent
