from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from agent import reviewAnalysisAgent
from agent_executor import reviewAnalysisAgentExecutor
import click
import uvicorn


@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=10002)
def main(host, port):
    try:
        capabilities = AgentCapabilities(streaming=False)
        skill = AgentSkill(
            id="review_analysis_agent",
            name="review_analysis_agent",
            description=("Fetches customer reviews for the products"),
            tags=["review", "customer feedback", "ratings"],
            examples=["Share the reviews of Samsung Galaxy F54 5G."],
        )

        agent_card = AgentCard(
            name="review_analysis_agent",
            description=("Fetches customer reviews for the products"),
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=reviewAnalysisAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=reviewAnalysisAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )

        request_handler = DefaultRequestHandler(
            agent_executor=reviewAnalysisAgentExecutor(),
            task_store=InMemoryTaskStore(),
        )
        server = A2AStarletteApplication(
            agent_card=agent_card, http_handler=request_handler
        )
        uvicorn.run(server.build(), host=host, port=port)

    except Exception as e:
        exit(1)


if __name__ == "__main__":
    main()
