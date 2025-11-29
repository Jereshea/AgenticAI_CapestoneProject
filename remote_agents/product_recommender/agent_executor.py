from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.utils.errors import ServerError
from a2a.types import (
    InvalidParamsError,
    Part,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from agent import productRecommenderAgent
import json


class productRecommenderAgentExecutor(AgentExecutor):
    def __init__(self):
        self.agent = productRecommenderAgent()

    async def _process_request(
        self,
        query: str,
        session_id: str,
        task_updater: TaskUpdater,
    ) -> None:
        try:
            async for item in self.agent.stream(query, session_id):
                is_task_complete = item["is_task_complete"]

                if not is_task_complete:
                    await task_updater.update_status(
                        TaskState.working,
                        message=task_updater.new_agent_message(
                            [Part(root=TextPart(text=item["updates"]))]
                        ),
                    )
                    continue

                parts = [Part(root=TextPart(text=str(item["content"])))]
                await task_updater.add_artifact(parts)
                await task_updater.complete()
                break

        except Exception as e:
            await task_updater.update_status(
                TaskState.failed,
                message=task_updater.new_agent_message(
                    [Part(root=TextPart(text=f"Error: {str(e)}"))]
                ),
                final=True,
            )

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ):
        if not context.task_id or not context.context_id:
            raise ValueError("RequestContext must have task_id and context_id")
        if not context.message:
            raise ValueError("RequestContext must have a message")

        query = context.get_user_input()
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)

        if not context.current_task:
            await updater.submit()

        await updater.start_work()
        await self._process_request(query, context.context_id, updater)

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        raise ServerError(error=UnsupportedOperationError())
