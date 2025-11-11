"""
Unit тесты для агентов A2A Essay Pipeline.
"""
from unittest.mock import AsyncMock, MagicMock

import pytest


class TestEssayAgent:
    """Тесты для EssayAgent."""

    @pytest.mark.asyncio
    async def test_write_essay_success(self, essay_agent, mock_openai_client, mock_a2a_client):
        """Тест успешного написания эссе."""
        # Настройка мока OpenAI
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated essay content"
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        # Выполнение теста
        result = await essay_agent.write_essay("Test Topic")

        # Проверки
        assert result["topic"] == "Test Topic"
        assert result["essay"] == "Generated essay content"
        mock_openai_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_write_essay_openai_error(self, essay_agent, mock_openai_client):
        """Тест обработки ошибки OpenAI."""
        # Настройка мока для генерации исключения
        mock_openai_client.chat.completions.create = AsyncMock(side_effect=Exception("OpenAI Error"))

        # Выполнение и проверка
        with pytest.raises(Exception, match="OpenAI Error"):
            await essay_agent.write_essay("Test Topic")


class TestStyleEditorAgent:
    """Тесты для StyleEditorAgent."""

    @pytest.mark.asyncio
    async def test_edit_style_success(self, style_editor_agent, mock_openai_client):
        """Тест успешного редактирования стиля."""
        # Настройка мока OpenAI
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Edited text content"
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        # Выполнение теста
        result = await style_editor_agent.edit_style("Original text")

        # Проверки
        assert result["original_text"] == "Original text"
        assert result["edited_text"] == "Edited text content"
        mock_openai_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_style_openai_error(self, style_editor_agent, mock_openai_client):
        """Тест обработки ошибки OpenAI в StyleEditorAgent."""
        # Настройка мока для генерации исключения
        mock_openai_client.chat.completions.create = AsyncMock(side_effect=Exception("OpenAI Error"))

        # Выполнение и проверка
        with pytest.raises(Exception, match="OpenAI Error"):
            await style_editor_agent.edit_style("Original text")

    @pytest.mark.asyncio
    async def test_edit_style_empty_text(self, style_editor_agent, mock_openai_client):
        """Тест редактирования пустого текста."""
        # Настройка мока OpenAI
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Edited empty text"
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        # Выполнение теста
        result = await style_editor_agent.edit_style("")

        # Проверки
        assert result["original_text"] == ""
        assert result["edited_text"] == "Edited empty text"
