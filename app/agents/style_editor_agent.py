from openai import AsyncOpenAI
from ..config import OPENAI_API_KEY


class StyleEditorAgent:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)

    async def edit_style(self, text: str) -> dict:
        prompt = f"Отредактируй текст для лучшей ясности и стиля, сохраняя исходный смысл:\n\n{text}"
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.5,
        )

        edited_text = response.choices[0].message.content.strip()
        return {"original_text": text, "edited_text": edited_text}
