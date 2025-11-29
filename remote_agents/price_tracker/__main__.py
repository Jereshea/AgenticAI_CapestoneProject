from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from agent import priceTrackerAgent
from agent_executor import priceTrackerAgentExecutor
import click
import uvicorn


@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=10001)
def main(host, port):
    try:
        capabilities = AgentCapabilities(streaming=False)
        skill = AgentSkill(
            id="price_tracker_agent",
            name="price_tracker_agent",
            description=("Fetch the price details of products"),
            tags=["price fetcher", "price", "amazon"],
            examples=["Fetch the price of Samsung Galaxy F54 5G"],
        )

        agent_card = AgentCard(
            name="price_tracker_agent",
            description=("Fetch price for the product"),
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=priceTrackerAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=priceTrackerAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )

        request_handler = DefaultRequestHandler(
            agent_executor=priceTrackerAgentExecutor(),
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
