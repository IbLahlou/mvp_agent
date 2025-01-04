# src/core/agent.py
from langchain.agents import Tool, AgentExecutor
from langchain.agents.openai_functions_agent.base import OpenAIFunctionsAgent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.messages import SystemMessage, MessagesPlaceholder
from typing import List

class Agent:
    """Simplified agent that handles conversation and basic tools"""
    
    def __init__(self, openai_api_key: str, temperature: float = 0.7):
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            model="gpt-4",
            temperature=temperature
        )
        self.tools = self._get_tools()
        self.executor = self._create_executor()
    
    def _get_tools(self) -> List[Tool]:
        """Define basic tools available to the agent"""
        return [
            Tool(
                name="calculator",
                func=lambda x: str(eval(x)),
                description="For mathematical calculations"
            )
        ]
    
    def _create_executor(self) -> AgentExecutor:
        """Create the agent executor with a simple prompt"""
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="You are a helpful AI assistant."),
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
    
    async def execute(self, query: str, chat_history: List = None) -> str:
        """Execute the agent with the given query"""
        try:
            return await self.executor.arun(
                input=query,
                chat_history=chat_history or []
            )
        except Exception as e:
            raise Exception(f"Agent execution error: {str(e)}")

# src/core/cache.py
from redis.asyncio import Redis
from typing import Optional
import json

class Cache:
    """Simple Redis cache implementation"""
    
    def __init__(self, host: str, port: int, password: Optional[str] = None):
        self.redis = Redis(
            host=host,
            port=port,
            password=password,
            decode_responses=True
        )
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        try:
            value = await self.redis.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            print(f"Cache get error: {str(e)}")
            return None
    
    async def set(self, key: str, value: str, ttl: int = 3600):
        """Set value in cache with TTL"""
        try:
            await self.redis.setex(key, ttl, json.dumps(value))
        except Exception as e:
            print(f"Cache set error: {str(e)}")
            
    async def add_to_list(self, list_key: str, value: dict):
        """Add value to a Redis list"""
        try:
            await self.redis.lpush(list_key, json.dumps(value))
        except Exception as e:
            print(f"Cache list add error: {str(e)}")
    
    async def get_list(self, list_key: str, start: int = 0, end: int = -1) -> List[dict]:
        """Get values from a Redis list"""
        try:
            items = await self.redis.lrange(list_key, start, end)
            return [json.loads(item) for item in items]
        except Exception as e:
            print(f"Cache list get error: {str(e)}")
            return []