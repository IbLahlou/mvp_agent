# src/agents/base_agent.py
from langchain import agents
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain.schema.messages import SystemMessage
from langchain.tools import Tool
from langchain.agents import AgentOutputParser
from langchain.schema import AgentAction, AgentFinish
from src.config.settings import Settings
from typing import Union, List
import re

class CustomOutputParser(AgentOutputParser):
    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        # If the agent says it completed the task, return AgentFinish
        if "Final Answer:" in text:
            return AgentFinish(
                return_values={"output": text.split("Final Answer:")[-1].strip()},
                log=text
            )
        
        # Otherwise, assume it's an action and try to parse it
        action_match = re.search(r'Action: (\w+)(.*?)Action Input: (.*)', text, re.DOTALL)
        if not action_match:
            return AgentFinish(
                return_values={"output": text.strip()},
                log=text
            )
            
        action = action_match.group(1)
        action_input = action_match.group(3)
        
        return AgentAction(tool=action.strip(), tool_input=action_input.strip(), log=text)

class BaseAgent:
    def __init__(self):
        """Initialize the BaseAgent with LLM, tools, and agent executor."""
        self.settings = Settings()
        try:
            self.llm = ChatOpenAI(
                api_key=self.settings.OPENAI_API_KEY,
                model="gpt-4",
                temperature=self.settings.TEMPERATURE
            )
            print("LLM initialized successfully")
        except Exception as e:
            print(f"Error initializing LLM: {str(e)}")
            raise

        self.tools = self._get_tools()
        self.agent_executor = self._create_agent()

    def _get_tools(self) -> List[Tool]:
        """Return a list of tools available to the agent."""
        return [
            Tool(
                name="calculator",
                func=lambda x: str(eval(x)),
                description="Useful for performing mathematical calculations"
            )
        ]

    def _create_agent(self) -> AgentExecutor:
        """Create and return an agent executor with the specified tools and prompt."""
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=(
                "You are a helpful assistant skilled at using tools to solve problems. "
                "Always structure your responses with 'Final Answer:' when providing the final response."
            )),
            HumanMessagePromptTemplate.from_template("{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )

        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            return_intermediate_steps=True,  # This will help with debugging
            handle_parsing_errors=True
        )

    async def execute(self, query: str) -> str:
        """Execute the agent with the given query."""
        try:
            # Execute the agent and get both the result and intermediate steps
            response = await self.agent_executor.ainvoke(
                {"input": query}
            )
            
            # Extract the final answer from the response
            if isinstance(response, dict) and "output" in response:
                result = response["output"]
            else:
                result = str(response)
            
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