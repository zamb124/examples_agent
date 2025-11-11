from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AFastAPIApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    Task,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from a2a.utils.message import new_agent_text_message

from .agents.essay_agent import EssayAgent
from .agents.style_editor_agent import StyleEditorAgent


class EssayPipelineAgentExecutor(AgentExecutor):
    """Исполнитель для полного пайплайна написания и редактирования эссе"""

    def __init__(self):
        self.essay_agent = EssayAgent()
        self.style_agent = StyleEditorAgent()

    async def execute(self, context: RequestContext, event_queue: EventQueue):
        if not context.message or not context.message.parts:
            return

        # Получаем текст из сообщения
        text = context.message.parts[0].root.text

        # Определяем тип задачи по контексту или навыку
        skill_id = getattr(context, "skill_id", None)

        # Статус работы
        await event_queue.put(TaskStatusUpdateEvent(
            task_id=context.task_id,
            context_id=context.context_id,
            status=TaskStatus(state=TaskState.working),
            final=False,
        ))

        try:
            if skill_id == "write_essay":
                # Пишем эссе, затем редактируем стиль
                essay_result = await self.essay_agent.write_essay(text)
                style_result = await self.style_agent.edit_style(essay_result["essay"])

                final_text = style_result["edited_text"]
                response_message = f"Эссе на тему '{text}' написано и отредактировано:\n\n{final_text}"

            elif skill_id == "edit_style":
                # Только редактируем стиль
                style_result = await self.style_agent.edit_style(text)
                final_text = style_result["edited_text"]
                response_message = f"Текст отредактирован:\n\n{final_text}"

            else:
                # По умолчанию считаем, что это тема для эссе
                essay_result = await self.essay_agent.write_essay(text)
                style_result = await self.style_agent.edit_style(essay_result["essay"])

                final_text = style_result["edited_text"]
                response_message = f"Эссе на тему '{text}' написано и отредактировано:\n\n{final_text}"

            # Завершаем задачу
            await event_queue.put(Task(
                id=context.task_id,
                context_id=context.context_id,
                status=TaskStatus(
                    state=TaskState.completed,
                    message=new_agent_text_message(
                        response_message,
                        context.context_id,
                        context.task_id,
                    ),
                ),
            ))
        except Exception as e:  # noqa: BLE001
            # Обрабатываем ошибку
            await event_queue.put(Task(
                id=context.task_id,
                context_id=context.context_id,
                status=TaskStatus(
                    state=TaskState.failed,
                    message=new_agent_text_message(
                        f"Ошибка: {e!s}",
                        context.context_id,
                        context.task_id,
                    ),
                ),
            ))

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        await event_queue.put(Task(
            id=context.task_id,
            context_id=context.context_id,
            status=TaskStatus(state=TaskState.canceled),
        ))


# Определение карты агента
agent_card = AgentCard(
    name="A2A Essay Pipeline",
    description="Pipeline for writing and editing essays using OpenAI",
    url="http://localhost:8000",
    version="1.0.0",
    capabilities=AgentCapabilities(streaming=True),
    skills=[
        AgentSkill(
            id="write_essay",
            name="Write Essay",
            description="Generates an essay on a given topic",
            tags=["writing", "essay", "openai"],
        ),
        AgentSkill(
            id="edit_style",
            name="Edit Style",
            description="Improves the style of given text",
            tags=["editing", "style", "openai"],
        ),
    ],
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
)

# Инициализация компонентов сервера
agent_executor = EssayPipelineAgentExecutor()  # Основной агент для пайплайна
task_store = InMemoryTaskStore()
handler = DefaultRequestHandler(agent_executor, task_store)

# Создание FastAPI приложения
app_builder = A2AFastAPIApplication(agent_card, handler)
app = app_builder.build()

# Запуск сервера при прямом вызове
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)  # noqa: S104
