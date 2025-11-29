from crewai import LLM, Agent, Crew, Task
from crewai.process import Process
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# MCP Tool Connection (runs live_data.py)
amazon_server_params = StdioServerParameters(
    command="python3",
    args=["live_data.py"],
)


class priceTrackerAgent:
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self.model = LLM(
            model="ollama_chat/llama3.1-cpu-custom",
            base_url="http://localhost:11434",
            temperature=0.0,
        )

        self.amazon_tools = MCPServerAdapter(amazon_server_params)

        self.analyst_task = Agent(
            role="Product Identifier",
            goal="Fetch product names",
            backstory="You are a professional in indentifying the product names in a user query.",
            verbose=True,
            allow_delegation=False,
            tools=self.amazon_tools.tools,
            llm=self.model,
        )

        self.identify_task = Task(
            description=(
                """
                DON'T RESPOND with you opinion.
                Given the user query {user_prompt},
                - 'products': list of product names mentioned in the query.

                STRICTLY pass only the **products name** as input [Don't add symbols like *] to the tool amazon_scraper ONE by ONE.
                Then combine the results.

                RETURN the entire tools output (title and its prices).
                """
            ),
            verbose=True,
            expected_output="Return the tools output",
            agent=self.analyst_task,
        )

        self.analysis_crew = Crew(
            agents=[self.analyst_task],
            tasks=[self.identify_task],
            process=Process.sequential,
            max_itr=1,
            verbose=True,
        )

    def fetch_product_details(self, product):
        results = {}
        for product in products:
            amazon_tool = self.amazon_tools.tools["amazon_scraper"]
            amazon_result = amazon_tool.run({"input_str": product})
            results[product] = {"amazon": amazon_result}

        return results

    def invoke(self, query: str, session_id: str = None, session_data: dict = None):
        if session_id:
            logger.info(f"Processing query for session_id: {session_id}")

        if session_data is None:
            session_data = {}

        crew_response = self.analysis_crew.kickoff({"user_prompt": query})
        print(crew_response)

        return crew_response


if __name__ == "__main__":
    agent = priceTrackerAgent()
    try:
        input_query = agent.invoke(
            """
            Based on the information available, here are a few Samsung smartphones that you might consider, keeping in mind your preferences for a great camera and good battery life, and a budget under ₹25,000:

            * **Samsung Galaxy F54 5G:** This phone is often recommended for its excellent battery life, featuring a 6000 mAh battery and a 108MP primary rear camera.
            * **Samsung Galaxy M34 5G:** Known for its large 6000mAh battery, it's a good option if battery life is a top priority. It also features a 50MP main camera.
            * **Samsung Galaxy A55 5G:** This model is frequently mentioned and has a good overall score.
            * **Samsung Galaxy A35 5G:** This is another option to consider within your budget.
            * **Samsung Galaxy M56 5G:** Some sources mention this model as having a long-lasting battery.

            When choosing, consider:

            * **Camera:** Look for higher megapixel counts for potentially better image quality.
            * **Battery:** A 5000 mAh battery or higher should offer good battery life.
            * **Other Features:** Consider other features that are important to you, such as display quality, processor, and RAM.
            """
        )
        print("\n=== Output ===\n", input_query)

    except Exception as e:
        print(f"An error occurred during agent invocation: {e}")
