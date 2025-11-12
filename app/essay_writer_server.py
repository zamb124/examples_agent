import httpx
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


class EssayWriterAgentExecutor(AgentExecutor):
    def __init__(self, style_editor_url: str | None = None):
        self.essay_agent = EssayAgent()
        self.style_editor_url = style_editor_url

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

        essay_result = await self.essay_agent.write_essay(text)
        essay_text = essay_result["essay"]

        if self.style_editor_url:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.style_editor_url}/",
                    json={
                        "jsonrpc": "2.0",
                        "id": f"essay-{context.task_id}",
                        "method": "message/send",
                        "params": {
                            "message": {
                                "role": "user",
                                "messageId": f"msg-{context.task_id}",
                                "parts": [{"text": essay_text, "mime_type": "text/plain"}]
                            }
                        }
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "result" in result and result["result"]["status"]["state"] == "completed":
                        edited_text = result["result"]["status"]["message"]["parts"][0]["text"]
                        final_message = f"Эссе на тему '{text}' написано и отредактировано:\n\n{edited_text}"
                    else:
                        final_message = f"Эссе на тему '{text}':\n\n{essay_text}"
                else:
                    final_message = f"Эссе на тему '{text}':\n\n{essay_text}"
        else:
            final_message = f"Эссе на тему '{text}':\n\n{essay_text}"

        await event_queue.enqueue_event(Task(
            id=context.task_id,
            context_id=context.context_id,
            status=TaskStatus(
                state=TaskState.completed,
                message=new_agent_text_message(final_message, context.context_id, context.task_id),
            ),
        ))

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        await event_queue.enqueue_event(Task(
            id=context.task_id,
            context_id=context.context_id,
            status=TaskStatus(state=TaskState.canceled),
        ))


essay_writer_card = AgentCard(
    name="Essay Writer Agent",
    description="Агент для написания эссе через OpenAI GPT-4",
    url="http://localhost:8001",
    version="1.0.0",
    capabilities=AgentCapabilities(streaming=True),
    skills=[AgentSkill(id="write_essay", name="Написать эссе", description="Генерирует эссе на тему", tags=["writing"])],
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
)

agent_executor = EssayWriterAgentExecutor(style_editor_url="http://style-editor:8002")
app = A2AFastAPIApplication(essay_writer_card, DefaultRequestHandler(agent_executor, InMemoryTaskStore())).build()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)  # noqa: S104
