import os

from openai import AsyncOpenAI


class StyleEditorAgent:
    def __init__(self):
        # Инициализация OpenAI клиента
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def edit_style(self, text: str) -> dict:
        # Создание промпта для редактирования стиля текста
        prompt = (
            "Edit the following text for better style, clarity, and flow "
            "while preserving the original meaning:\n\n"
            f"{text}"
        )

        # Вызов OpenAI API для редактирования текста
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.5,
        )

        # Извлечение отредактированного текста
        edited_text = response.choices[0].message.content.strip()

        # Возврат результата с оригинальным и отредактированным текстом  # noqa: RUF003
        return {"original_text": text, "edited_text": edited_text}
