import os

from a2a_sdk import A2AClient, TaskRequest
from openai import AsyncOpenAI


class EssayAgent:
    def __init__(self):
        # Инициализация OpenAI клиента
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # Инициализация A2A клиента для вызова других агентов
        self.a2a_client = A2AClient()

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

        # Создание запроса к агенту редактора стиля через A2A
        edit_request = TaskRequest(
            agent_id="style-editor-agent",
            capability_id="edit_style",
            parameters={"text": essay_text},
        )

        # Отправка задачи редактору стиля и получение результата
        edit_result = await self.a2a_client.send_task(edit_request)

        # Возврат финального результата
        return {"topic": topic, "essay": edit_result["edited_text"]}
