# src/agents/base_agent.py
from langchain import agents
from langchain.agents import Tool, AgentExecutor
from langchain.agents.openai_functions_agent.base import OpenAIFunctionsAgent
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings  # Updated import
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder
from langchain.schema.messages import SystemMessage
from langchain_community.vectorstores.faiss import FAISS
import os

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
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=self.settings.OPENAI_API_KEY
            )
            self.vector_store = self._initialize_vector_store()
            print("LLM and Vector Store initialized successfully")
        except Exception as e:
            print(f"Error initializing components: {str(e)}")
            raise

        self.tools = self._get_tools()
        self.agent_executor = self._create_agent()

    def _initialize_vector_store(self):
        """Initialize or load FAISS vector store"""
        vector_store_path = "data/vector_store"
        os.makedirs("data", exist_ok=True)
        
        if os.path.exists(vector_store_path):
            try:
                return FAISS.load_local(
                    vector_store_path, 
                    self.embeddings,
                    allow_dangerous_deserialization=True  # Only for trusted local files
                )
            except Exception:
                # If loading fails, create new store
                return self._create_new_vector_store(vector_store_path)
        else:
            return self._create_new_vector_store(vector_store_path)

    def _create_new_vector_store(self, path):
        """Create a new FAISS vector store"""
        vector_store = FAISS.from_texts(
            texts=["Initial document"],
            embedding=self.embeddings,
            metadatas=[{"source": "initialization"}]
        )
        vector_store.save_local(path)
        return vector_store

    def _get_tools(self):
        """Return a list of tools available to the agent."""
        return [
            Tool(
                name="search_documents",
                func=self._search_documents,
                description="Search through stored documents for relevant information"
            ),
            Tool(
                name="calculator",
                func=lambda x: str(eval(x)),
                description="Useful for performing mathematical calculations"
            )
        ]

    def _search_documents(self, query: str):
        """Search through documents using vector store"""
        docs = self.vector_store.similarity_search(query)
        return "\n".join([doc.page_content for doc in docs])

    def _create_agent(self):
        """Create and return an agent executor with the specified tools and prompt."""
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=(
                "You are a helpful assistant skilled at using tools to solve problems. "
                "You can search through documents and perform calculations."
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
        except Exception as e:
            print(f"Error in execute: {str(e)}")
            raise