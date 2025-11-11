
from openai import AsyncOpenAI

from ..config import OPENAI_API_KEY


class EssayAgent:
    def __init__(self):
        # Инициализация OpenAI клиента
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)

    async def write_essay(self, topic: str) -> dict:
        # Создание промпта для генерации эссе
        prompt = (
            f"Write a well-structured essay on the topic: {topic}. "
            "Make it informative and engaging."
        )

        # Вызов OpenAI API для генерации текста эссе
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7,
        )

        # Извлечение сгенерированного текста
        essay_text = response.choices[0].message.content.strip()

        # Возврат результата с сырым текстом эссе
        return {"topic": topic, "essay": essay_text}
