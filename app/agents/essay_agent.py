from openai import AsyncOpenAI
from ..config import OPENAI_API_KEY


class EssayAgent:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)

    async def write_essay(self, topic: str) -> dict:
        prompt = f"Напиши структурированное эссе на тему: {topic}. Сделай его информативным и интересным."
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7,
        )

        essay_text = response.choices[0].message.content.strip()
        return {"topic": topic, "essay": essay_text}
