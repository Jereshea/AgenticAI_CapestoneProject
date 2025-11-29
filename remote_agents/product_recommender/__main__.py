from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from agent import productRecommenderAgent
from agent_executor import productRecommenderAgentExecutor
import click
import uvicorn


@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=10003)
def main(host, port):
    try:
        capabilities = AgentCapabilities(streaming=False)
        skill = AgentSkill(
            id="product_recommender_agent",
            name="product_recommender_agent",
            description=("Suggest products based on the user specifications"),
            tags=["suggest", "feature", "idea"],
            examples=[
                "I want a smartphone under ₹25,000 with a great camera and good battery. I prefer Samsung."
            ],
        )

        agent_card = AgentCard(
            name="product_recommender_agent",
            description=("Suggest products based on the user specifications"),
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=productRecommenderAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=productRecommenderAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )

        request_handler = DefaultRequestHandler(
            agent_executor=productRecommenderAgentExecutor(),
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
