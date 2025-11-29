from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import Event, EventQueue
from a2a.utils.errors import ServerError
from a2a.utils import (
    completed_task,
    new_artifact,
)
from a2a.types import (
    InvalidParamsError,
    Part,
    Task,
    TextPart,
    UnsupportedOperationError,
)
from typing import Any
from agent import priceTrackerAgent
from typing_extensions import override


class priceTrackerAgentExecutor(AgentExecutor):
    def __init__(self):
        self.agent = priceTrackerAgent()
        self.session_store = {}

    @override
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:

        error = self._validate_request(context)
        if error:
            raise ServerError(error=InvalidParamsError())

        query = context.get_user_input()
        session_id = "default_session"

        if session_id not in self.session_store:
            self.session_store[session_id] = {}

        session_data = self.session_store[session_id]

        try:
            result = self.agent.invoke(
                query=query, session_id=session_id, session_data=session_data
            )

        except Exception as e:
            print(f"Error invoking for session {session_id}: {e}")
            raise ServerError(error=InvalidParamsError(details=str(e))) from e

        parts = [Part(root=TextPart(text=result.raw))]

        await event_queue.enqueue_event(
            completed_task(
                context.task_id,
                context.context_id,
                [new_artifact(parts, f"output_{context.task_id}")],
                [context.message],
            )
        )

    @override
    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        raise ServerError(error=UnsupportedOperationError())

    def _validate_request(self, context: RequestContext) -> bool:
        return False

    def get_session_data(self, session_id: str) -> None:
        if session_id in self.session_store:
            del sefl.session_store[session_id]
