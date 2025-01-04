from langchain import agents
from langchain.agents import AgentExecutor
from langchain.agents.openai_functions_agent.base import OpenAIFunctionsAgent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain.schema.messages import SystemMessage
from langchain.tools import Tool
from src.config.settings import Settings

class BaseAgent:
    def __init__(self):
        """Initialize the BaseAgent with LLM, tools, and agent executor."""
        self.settings = Settings()
        try:
            self.llm = ChatOpenAI(
                api_key=self.settings.OPENAI_API_KEY,
                model="gpt-4",  # Try this model first
                temperature=self.settings.TEMPERATURE
            )
            print("LLM initialized successfully")
        except Exception as e:
            print(f"Error initializing LLM: {str(e)}")
            raise

        self.tools = self._get_tools()
        self.agent_executor = self._create_agent()

    def _get_tools(self):
        """Return a list of tools available to the agent."""
        return [
            Tool(
                name="calculator",
                func=lambda x: str(eval(x)),
                description="Useful for performing mathematical calculations"
            )
        ]

    def _create_agent(self):
        """Create and return an agent executor with the specified tools and prompt."""
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=(
                "You are a helpful assistant skilled at using tools to solve problems."
            )),
            HumanMessagePromptTemplate.from_template("{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        agent = OpenAIFunctionsAgent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )

        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True
        )

    async def execute(self, query: str):
        """Execute the agent with the given query."""
        try:
            result = await self.agent_executor.arun(
                input=query
            )
            print(f"Execution result: {result}")
            return result
        except ValueError as e:
            print(f"ValueError in execute: {str(e)}")
            raise
        except RuntimeError as e:
            print(f"RuntimeError in execute: {str(e)}")
            raise
        except Exception as e:
            print(f"Unexpected error in execute: {str(e)}")
            raise