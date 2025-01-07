# src/services/prompt_processor.py
from typing import Optional, Dict, Any
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

class PromptProcessor:
    """Service for processing text using prompt engineering techniques"""
    
    def __init__(self, openai_api_key: str, model_name: str = "gpt-4", temperature: float = 0.7):
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            model=model_name,
            temperature=temperature
        )
        
        # Define the base prompt template for processing search results
        self.search_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an experienced professional support specialist named Alex. When processing search results:
            1. Approach each query with both expertise and warmth
            2. Share information clearly but conversationally
            3. Balance technical accuracy with accessible explanations
            4. When clarification is needed, ask specific, well-framed questions
            
            Your tone should reflect both competence and approachability. Use professional yet warm language, and feel free to express genuine interest in helping solve the query. Think of how an experienced professional would explain things to a valued client."""),
            ("human", "Here are the search results:\n{search_results}\n\nPlease process this information and provide a response."),
        ])

        # Define fallback responses for when no results are found
        self.fallback_responses = [
            "Good day, Sarah speaking. How can I be of assistance?",
            "I'd like to help with that - could you clarify what you're looking for?"
        ]

    async def process_search_results(self, results: list, query: str) -> Dict[str, Any]:
        """
        Process search results using prompt engineering
        
        Args:
            results: List of search results from FAISS
            query: Original search query
            
        Returns:
            Dict containing processed response and metadata
        """
        try:
            # If no results, return a fallback response
            if not results:
                return {
                    "processed_response": self.fallback_responses[0],
                    "original_results": [],
                    "confidence": 0.0
                }

            # Format search results for the prompt
            formatted_results = "\n\n".join([
                f"Result {i+1}:\n{r['content']}\nConfidence: {r['score']}"
                for i, r in enumerate(results)
            ])

            # Get enhanced response using the prompt
            chain = self.search_prompt | self.llm
            response = await chain.ainvoke({
                "search_results": formatted_results
            })

            # Calculate overall confidence score
            avg_confidence = sum(r['score'] for r in results) / len(results)

            return {
                "processed_response": response.content,
                "original_results": results,
                "confidence": avg_confidence
            }

        except Exception as e:
            return {
                "processed_response": self.fallback_responses[1],
                "original_results": [],
                "confidence": 0.0,
                "error": str(e)
            }
