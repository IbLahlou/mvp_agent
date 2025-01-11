# src/agents/base_agent.py
from langchain.agents import Tool, AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.messages import SystemMessage
from typing import List, Dict, Any
from src.config.settings import Settings
from langchain_community.vectorstores.faiss import FAISS
from langchain_openai import OpenAIEmbeddings
import os

class BaseAgent:
    def __init__(self):
        """Initialize the BaseAgent with LLM, tools, and RAG capabilities."""
        self.settings = Settings()
        self.llm = ChatOpenAI(
            api_key=self.settings.OPENAI_API_KEY,
            model="gpt-4",
            temperature=self.settings.TEMPERATURE
        )
        
        # Initialize embeddings and vector store
        self.embeddings = OpenAIEmbeddings(api_key=self.settings.OPENAI_API_KEY)
        self._initialize_vector_store()
        
        self.tools = self._get_tools()
        self.agent_executor = self._create_agent()
        # Add this line to your __init__ method after initializing other components
        self.context: Dict[str, Any] = {}

    def _initialize_vector_store(self):
        """Initialize or load vector store"""
        store_path = "data/vector_store"
        os.makedirs("data", exist_ok=True)
        
        if os.path.exists(store_path):
            try:
                self.vector_store = FAISS.load_local(
                    store_path, 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
            except Exception as e:
                print(f"Error loading vector store: {e}")
                self.vector_store = self._create_new_vector_store(store_path)
        else:
            self.vector_store = self._create_new_vector_store(store_path)

    def _create_new_vector_store(self, path: str) -> FAISS:
        """Create a new FAISS vector store"""
        vector_store = FAISS.from_texts(
            texts=["initialization"],
            embedding=self.embeddings
        )
        vector_store.save_local(path)
        return vector_store

    def _search_documents(self, query: str) -> str:
        """Search through documents using vector store"""
        try:
            results = self.vector_store.similarity_search(query, k=3)
            return "\n\n".join([f"Document {i+1}:\n{doc.page_content}" 
                              for i, doc in enumerate(results)])
        except Exception as e:
            return f"Error searching documents: {str(e)}"

    def _get_tools(self) -> List[Tool]:
        """Return a list of tools available to the agent."""
        return [
            Tool(
                name="search_documents",
                func=self._search_documents,
                description="Search through uploaded documents for relevant information"
            ),
            Tool(
                name="calculator",
                func=lambda x: str(eval(x)),
                description="Useful for performing mathematical calculations"
            )
        ]

    def _create_agent(self) -> AgentExecutor:
        """Create and return an agent executor."""
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=(
                "You are a helpful assistant skilled at using tools to solve problems. "
                "You can search through documents and perform calculations. "
                "When using information from documents, always cite the source."
            )),
            MessagesPlaceholder(variable_name="chat_history"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Using the new recommended way to create an OpenAI Functions agent
        agent = create_openai_functions_agent(
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

    async def execute(self, query: str, chat_history: List[Dict[str, Any]] = None) -> str:
        """
        Execute the agent with the given query, incorporating context.
        Args:
            query: The user's query
            chat_history: Optional chat history list
        Returns:
            str: The agent's response
        """
        try:
            # Include context in the execution
            input_context = {
                "input": query,
                "chat_history": chat_history or [],
                "context": self.get_context()
            }
            
            result = await self.agent_executor.arun(**input_context)
            return result
        except Exception as e:
            print(f"Error in agent execution: {str(e)}")
            raise

    def get_context(self) -> Dict[str, Any]:
        """
        Retrieve the current context for the agent.
        Returns:
            Dict containing the current context including any business context,
            framework settings, and conversation history.
        """
        return self.context

    def set_context(self, context: Dict[str, Any]) -> None:
        """
        Set or update the agent's context.
        Args:
            context: Dictionary containing context information
        """
        self.context.update(context)

    def clear_context(self) -> None:
        """Clear the agent's current context."""
        self.context = {}

    def get_business_context(self) -> List[str]:
        """
        Get business-specific context for prompt engineering.
        Returns:
            List of context strings relevant to the current business scenario.
        """
        return self.context.get('business_context', [])