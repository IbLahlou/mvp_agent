from typing import Dict, TypedDict
from langgraph.graph import Graph
from langchain_openai import ChatOpenAI
from src.config.settings import Settings

class AgentState(TypedDict):
    input: str
    intermediate_steps: list
    output: str

def create_workflow():
    settings = Settings()
    
    # Define nodes
    def process_input(state: AgentState) -> AgentState:
        state["intermediate_steps"].append("Processing input")
        return state
    
    def generate_response(state: AgentState) -> AgentState:
        llm = ChatOpenAI(
            model=settings.MODEL_NAME,
            temperature=settings.TEMPERATURE
        )
        response = llm.predict(state["input"])
        state["output"] = response
        return state
    
    # Create workflow graph
    workflow = Graph()
    
    # Add nodes
    workflow.add_node("process_input", process_input)
    workflow.add_node("generate_response", generate_response)
    
    # Add edges
    workflow.add_edge("process_input", "generate_response")
    
    # Set entry point
    workflow.set_entry_point("process_input")
    
    return workflow.compile()