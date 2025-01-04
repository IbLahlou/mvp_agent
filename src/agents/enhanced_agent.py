# src/agents/enhanced_agent.py
from langchain import agents
from langchain.agents import Tool, AgentExecutor
from langchain.agents.openai_functions_agent.base import OpenAIFunctionsAgent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.messages import SystemMessage
from typing import List, Any

from src.services.document_service import DocumentService
from src.config.settings import Settings

class EnhancedAgent:
    def __init__(self, document_service: DocumentService):
        self.settings = Settings()
        self.document_service = document_service
        
        self.llm = ChatOpenAI(
            api_key=self.settings.OPENAI_API_KEY,
            model="gpt-4",
            temperature=self.settings.TEMPERATURE
        )
        
        self.tools = self._get_tools()
        self.agent_executor = self._create_agent()
    
    def _get_tools(self) -> List[Tool]:
        """Get list of tools available to the agent."""
        return [
            Tool(
                name="search_documents",
                func=self.document_service.search_documents,
                description="Search through uploaded documents for relevant information. Input should be a search query."
            ),
            Tool(
                name="calculator",
                func=lambda x: str(eval(x)),
                description="Useful for performing mathematical calculations"
            )
        ]
    
    def _create_agent(self) -> AgentExecutor:
        """Create the agent executor."""
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=(
                "You are a helpful assistant with access to document search capabilities. "
                "When answering questions, you can search through uploaded documents for relevant information. "
                "Always cite the source document when using information from the search results."
            )),
            MessagesPlaceholder(variable_name="chat_history"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = OpenAIFunctionsAgent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=3
        )
    
    async def execute(self, query: str, chat_history: List[Any] = None) -> str:
        """Execute the agent with the given query."""
        try:
            result = await self.agent_executor.arun(
                input=query,
                chat_history=chat_history or []
            )
            return result
        except Exception as e:
            print(f"Error in agent execution: {str(e)}")
            raise