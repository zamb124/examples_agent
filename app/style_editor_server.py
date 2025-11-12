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

from .agents.style_editor_agent import StyleEditorAgent


class StyleEditorAgentExecutor(AgentExecutor):
    def __init__(self):
        self.style_agent = StyleEditorAgent()

    async def execute(self, context: RequestContext, event_queue: EventQueue):
        if not context.message or not context.message.parts:
            return

        text = context.message.parts[0].text if hasattr(context.message.parts[0], 'text') else str(context.message.parts[0])

        await event_queue.enqueue_event(TaskStatusUpdateEvent(
            task_id=context.task_id,
            context_id=context.context_id,
            status=TaskStatus(state=TaskState.working),
            final=False,
        ))

        style_result = await self.style_agent.edit_style(text)

        await event_queue.enqueue_event(Task(
            id=context.task_id,
            context_id=context.context_id,
            status=TaskStatus(
                state=TaskState.completed,
                message=new_agent_text_message(f"Текст отредактирован:\n\n{style_result['edited_text']}", context.context_id, context.task_id),
            ),
        ))

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        await event_queue.enqueue_event(Task(
            id=context.task_id,
            context_id=context.context_id,
            status=TaskStatus(state=TaskState.canceled),
        ))


style_editor_card = AgentCard(
    name="Style Editor Agent",
    description="Агент для улучшения стиля текста через OpenAI GPT-4",
    url="http://localhost:8002",
    version="1.0.0",
    capabilities=AgentCapabilities(streaming=True),
    skills=[AgentSkill(id="edit_style", name="Редактировать стиль", description="Улучшает стиль текста", tags=["editing"])],
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
)

agent_executor = StyleEditorAgentExecutor()
app = A2AFastAPIApplication(style_editor_card, DefaultRequestHandler(agent_executor, InMemoryTaskStore())).build()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)  # noqa: S104
