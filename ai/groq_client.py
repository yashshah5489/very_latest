"""
Groq LLM Client for Indian Financial Analyzer using LangChain
with caching to conserve API usage limits
"""
import os
import json
import logging
import hashlib
from typing import Dict, Any, List, Optional, Union

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain.schema.output_parser import StrOutputParser

# Import cache manager for API usage optimization
try:
    from utils.cache_manager import cache_manager
except ImportError:
    # Fallback if the cache manager is not available
    cache_manager = None
    logger = logging.getLogger(__name__)
    logger.warning("Cache manager not available, Groq API usage will not be optimized")
else:
    logger = logging.getLogger(__name__)

class GroqClient:
    """Client for Groq LLM API using LangChain"""
    
    def __init__(self, api_key=None):
        """Initialize Groq client with API key."""
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            logger.warning("No Groq API key provided. Set the GROQ_API_KEY environment variable.")
        
        self.default_model = "llama3-70b-8192"  # Using LLaMA 3 70B model
        
        # Initialize the LangChain LLM
        try:
            self.llm = ChatGroq(
                groq_api_key=self.api_key,
                model_name=self.default_model
            )
            logger.info(f"Initialized Groq LLM with model: {self.default_model}")
        except Exception as e:
            logger.error(f"Error initializing Groq LLM: {str(e)}")
            self.llm = None
    
    def chat_completion(self, 
                        messages: List[Dict[str, str]], 
                        model: Optional[str] = None,
                        temperature: float = 0.7,
                        max_tokens: int = 1024,
                        stream: bool = False) -> Dict[str, Any]:
        """
        Get a chat completion from Groq API using LangChain with caching to minimize API usage.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            model: Model to use (defaults to self.default_model)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            Response formatted like the OpenAI API response
        """
        if not self.api_key:
            return {"error": "API key not configured. Please set GROQ_API_KEY environment variable."}
        
        if not self.llm:
            return {"error": "LLM not initialized properly. Check logs for details."}
        
        # Check if caching is available and enabled
        caching_enabled = cache_manager is not None
        
        # Create a cache key from the request parameters
        # We don't include stream in the cache key as it only affects delivery, not content
        cache_key = None
        if caching_enabled and not stream:
            # Convert messages to a stable string representation for caching
            messages_str = json.dumps(messages, sort_keys=True)
            model_name = model or self.default_model
            cache_key = f"groq_{model_name}_{temperature}_{max_tokens}_{hashlib.md5(messages_str.encode()).hexdigest()}"
            
            # Check if we have a cached response
            cached_response = cache_manager.get(cache_key)
            if cached_response:
                logger.info(f"Using cached response for Groq LLM request")
                return cached_response
            
            # Check if we have exceeded the rate limit
            if not cache_manager.track_api_call("groq"):
                logger.warning("Groq API daily rate limit exceeded")
                return {"error": "Daily rate limit for Groq API exceeded. Try again tomorrow."}
            
        try:
            # If a different model is specified, create a new LLM instance
            llm = self.llm
            if model and model != self.default_model:
                llm = ChatGroq(
                    groq_api_key=self.api_key,
                    model_name=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            else:
                # Update parameters
                llm.temperature = temperature
                llm.max_tokens = max_tokens
            
            logger.info(f"Making Groq LLM request with model: {model or self.default_model}")
            
            # Convert OpenAI-style messages to LangChain format
            response_text = llm.invoke(messages)
            
            # Format the response like OpenAI's API for backward compatibility
            response = {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": response_text.content
                        },
                        "index": 0,
                        "finish_reason": "stop"
                    }
                ],
                "model": model or self.default_model,
                "object": "chat.completion"
            }
            
            # Cache the successful response if caching is enabled and not streaming
            if caching_enabled and cache_key and not stream:
                cache_manager.set(cache_key, response)
                
            return response
            
        except Exception as e:
            logger.error(f"Error calling Groq API via LangChain: {str(e)}")
            return {"error": str(e)}
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text based on a prompt.
        
        Args:
            prompt: The prompt to generate text from
            **kwargs: Additional parameters to pass to chat_completion
            
        Returns:
            Generated text content
        """
        messages = [{"role": "user", "content": prompt}]
        response = self.chat_completion(messages, **kwargs)
        
        if "error" in response:
            return f"Error: {response['error']}"
        
        if "choices" in response and len(response["choices"]) > 0:
            return response["choices"][0]["message"]["content"]
        
        return "No response generated"
    
    def analyze_finance(self, 
                       query: str, 
                       context: Optional[str] = None, 
                       format: Optional[str] = None) -> str:
        """
        Generate financial analysis on a specific query.
        
        Args:
            query: The financial query or analysis request
            context: Additional context or data for the analysis
            format: Optional format for the response (json, markdown, etc.)
            
        Returns:
            Generated financial analysis
        """
        # Build the prompt based on the requested format
        if format == "json":
            format_instruction = "Provide the response in valid JSON format."
        elif format == "markdown":
            format_instruction = "Format the response using Markdown."
        else:
            format_instruction = ""
        
        system_prompt = (
            "You are a specialized financial advisor for Indian markets. "
            "You provide detailed, accurate, and professional financial analysis. "
            "Focus on Indian market specifics like SEBI regulations, NSE/BSE insights, "
            "and local economic factors. When uncertain, acknowledge limitations. "
            f"{format_instruction}"
        )
        
        prompt = query
        if context:
            prompt = f"Context information:\n{context}\n\nQuery: {query}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat_completion(messages, temperature=0.3)
        
        if "error" in response:
            return f"Error: {response['error']}"
        
        if "choices" in response and len(response["choices"]) > 0:
            return response["choices"][0]["message"]["content"]
        
        return "No analysis generated"
    
    def extract_financial_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract financial entities from text.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            Dictionary with entity types as keys and lists of entities as values
        """
        prompt = (
            "Extract the following financial entities from the text below. "
            "Return the result as a JSON object with entity types as keys and arrays of unique entities as values.\n"
            "Entity types to extract:\n"
            "- company_names: Names of companies\n"
            "- stock_symbols: Stock ticker symbols\n"
            "- indices: Market indices\n"
            "- currencies: Currency names or symbols\n"
            "- financial_metrics: Financial metrics mentioned\n"
            "- dates: Any dates mentioned\n"
            "- people: Names of people\n\n"
            f"Text to analyze:\n{text}\n\n"
            "JSON response:"
        )
        
        messages = [
            {"role": "system", "content": "You are a financial entity extraction assistant. Extract entities accurately from the provided text."},
            {"role": "user", "content": prompt}
        ]
        
        response = self.chat_completion(messages, temperature=0.1)
        
        if "error" in response:
            logger.error(f"Error extracting entities: {response['error']}")
            return {}
        
        if "choices" in response and len(response["choices"]) > 0:
            content = response["choices"][0]["message"]["content"]
            try:
                # Look for JSON content within the response
                if "```json" in content:
                    # Extract JSON from code block
                    json_str = content.split("```json")[1].split("```")[0].strip()
                    return json.loads(json_str)
                else:
                    # Try to parse the entire response as JSON
                    return json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from response: {str(e)}")
                return {}
        
        return {}
    
    def summarize_financial_text(self, text: str, max_length: int = 200) -> str:
        """
        Summarize financial text.
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary in words
            
        Returns:
            Summarized text
        """
        prompt = (
            f"Summarize the following financial text in {max_length} words or less. "
            "Focus on key financial insights, maintain factual accuracy, and preserve important figures and percentages:\n\n"
            f"{text}"
        )
        
        return self.generate_text(prompt, temperature=0.3)
    
    def answer_financial_question(self, question: str, context: Optional[str] = None) -> str:
        """
        Answer a financial question.
        
        Args:
            question: The financial question to answer
            context: Optional context to help with answering the question
            
        Returns:
            Answer to the question
        """
        system_prompt = (
            "You are a financial advisor specialized in Indian markets. "
            "Provide accurate, helpful answers to financial questions. "
            "Focus on Indian financial specifics and regulations when relevant. "
            "When you don't know the answer, acknowledge limitations rather than inventing information."
        )
        
        user_prompt = question
        if context:
            user_prompt = f"Context information:\n{context}\n\nQuestion: {question}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.chat_completion(messages, temperature=0.3)
        
        if "error" in response:
            return f"Error: {response['error']}"
        
        if "choices" in response and len(response["choices"]) > 0:
            return response["choices"][0]["message"]["content"]
        
        return "Unable to answer the question at this time."