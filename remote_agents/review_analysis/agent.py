from google.adk.agents.llm_agent import LlmAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import google_search
from typing import Any, AsyncIterable
from google.genai import types
import asyncio
import json


class reviewAnalysisAgent:
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self._agent = self._build_agent()
        self._user_id = "remote_agent"
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
        )

    def get_processing_message(self) -> str:
        return "Analyzing data..."

    def _build_agent(self) -> LlmAgent:
        return LlmAgent(
            model="gemini-2.0-flash",
            name="review_analysis",
            description="Agent to get reviews of the products using Google Search.",
            instruction="""
            Identify the products in the query and fetch the product reviews for each product.
            Use tools to address it.

            DON'T provide SUGGESTION. Just fetch the reviews.
            """,
            tools=[google_search],
        )

    async def stream(
        self, query: str, session_id: str
    ) -> AsyncIterable[dict[str, Any]]:

        session = await self._runner.session_service.get_session(
            app_name=self._agent.name,
            user_id=self._user_id,
            session_id=session_id,
        )
        content = types.Content(role="user", parts=[types.Part.from_text(text=query)])

        if session is None:
            session = await self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )

        async for event in self._runner.run_async(
            user_id=self._user_id, session_id=session.id, new_message=content
        ):
            if event.is_final_response():
                response = ""
                if event.content and event.content.parts:
                    response = "\n".join(
                        [p.text for p in event.content.parts if p.text]
                    )
                    if not response:
                        for p in event.content.parts:
                            if p.function_response:
                                response = json.dumps(p.function_response.model_dump())
                                break

                yield {"is_task_complete": True, "content": response}
            else:
                yield {
                    "is_task_complete": False,
                    "updates": self.get_processing_message(),
                }

    def run(
        self,
        query: str = None,
        session: dict = None,
        session_id: str = "default_session",
    ) -> str:
        if session and "reviews_data" in session:
            query = session["reviews_data"]

        result = ""

        async def _run():
            nonlocal result
            async for chunk in self.stream(query, session_id):
                if chunk["is_task_complete"]:
                    result = chunk["content"]

        asyncio.run(_run())
        return result


if __name__ == "__main__":
    agent = productRecommenderAgent()
    final_output = agent.run("Share the reviews of Samsung Galaxy F54 5G.")
    print("\n=== Output ===\n", final_output)
