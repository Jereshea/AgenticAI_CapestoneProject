from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import Agent, SequentialAgent, ParallelAgent

model = LiteLlm(
    model="ollama_chat/llama3.1-cpu-custom",
    base_url="http://localhost:11434",
)

# Remote Agents
price_tracker_agent_card_url = "http://localhost:10001/.well-known/agent-card.json"
price_tracker_agent = RemoteA2aAgent(
    name="price_tracker_agent",
    description="Fetch the price details of products",
    agent_card=price_tracker_agent_card_url,
)

review_analysis_agentt_card_url = "http://localhost:10002/.well-known/agent-card.json"
review_analysis_agent = RemoteA2aAgent(
    name="review_analysis_agent",
    description="Fetches customer reviews for the products",
    agent_card=review_analysis_agentt_card_url,
)

product_recommender_agent_card_url = (
    "http://localhost:10003/.well-known/agent-card.json"
)
product_recommender_agent = RemoteA2aAgent(
    name="product_recommender_agent",
    description="Suggest products based on the user specifications",
    agent_card=product_recommender_agent_card_url,
)

priceTracker_reviewAnalysis_agents = ParallelAgent(
    name="priceTracker_reviewAnalysis_agents",
    sub_agents=[price_tracker_agent, review_analysis_agent],
    description="Runs agents in parallel",
)

e_commerce_personal_shopper = Agent(
    name="E_Commerce_Personal_Shopper",
    model=model,
    description="Provides personalized suggestion",
    instruction="""
    Based on the inputs, provide which is better.
    Also share the link to purchase ONLY from the input obtained.
    """,
    output_key="personal_shopper",
)

personal_shopper = SequentialAgent(
    name="Personal_Shopper",
    description="Sequentially calls subagents",
    sub_agents=[
        product_recommender_agent,
        priceTracker_reviewAnalysis_agents,
        e_commerce_personal_shopper,
    ],
)
