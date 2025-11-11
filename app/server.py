from a2a_sdk import A2AServer, AgentCard, Task, TaskStatus
from fastapi import FastAPI

from .agents.essay_agent import EssayAgent
from .agents.style_editor_agent import StyleEditorAgent

app = FastAPI(title="A2A Essay Pipeline", version="0.1.0")

# Инициализация A2A сервера
a2a_server = A2AServer(app)

# Создание экземпляров агентов
essay_agent = EssayAgent()
style_editor_agent = StyleEditorAgent()

# Определение карт агентов
agent_cards = [
    AgentCard(
        name="Essay Writer",
        description="Writes essays on given topics using OpenAI",
        version="1.0.0",
        capabilities=[
            {
                "id": "write_essay",
                "name": "Write Essay",
                "description": "Generates an essay on a given topic",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "The topic for the essay",
                        },
                    },
                    "required": ["topic"],
                },
            },
        ],
    ),
    AgentCard(
        name="Style Editor",
        description="Edits text for better style using OpenAI",
        version="1.0.0",
        capabilities=[
            {
                "id": "edit_style",
                "name": "Edit Style",
                "description": "Improves the style of given text",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to edit",
                        },
                    },
                    "required": ["text"],
                },
            },
        ],
    ),
]

# Регистрация карт агентов в A2A сервере
for card in agent_cards:
    a2a_server.register_agent_card(card)

# Обработчик задач для написания эссе
@a2a_server.task_handler("write_essay")
async def handle_write_essay(task: Task):
    await task.update_status(TaskStatus.WORKING)
    try:
        result = await essay_agent.write_essay(task.parameters["topic"])
        await task.complete(result)
    except Exception as e:  # noqa: BLE001
        await task.fail(str(e))

# Обработчик задач для редактирования стиля
@a2a_server.task_handler("edit_style")
async def handle_edit_style(task: Task):
    await task.update_status(TaskStatus.WORKING)
    try:
        result = await style_editor_agent.edit_style(task.parameters["text"])
        await task.complete(result)
    except Exception as e:  # noqa: BLE001
        await task.fail(str(e))

# Запуск сервера при прямом вызове
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)  # noqa: S104
