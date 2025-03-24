"""
Groq LLM Integration for Indian Financial Analyzer
"""
import requests
import json
import logging
import config

logger = logging.getLogger(__name__)

class GroqClient:
    """Class for interacting with Groq LLM API"""
    
    def __init__(self, api_key=None):
        """Initialize the Groq client with API key"""
        self.api_key = api_key or config.GROQ_API_KEY
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        
        if not self.api_key:
            logger.warning("Groq API key not provided. LLM functionality will be limited.")
    
    def generate_response(self, prompt, model="llama3-8b-8192", max_tokens=1024, temperature=0.7):
        """
        Generate a response from Groq LLM
        
        Args:
            prompt (str): The prompt/query to send to the LLM
            model (str): The model to use (default: llama3-8b-8192)
            max_tokens (int): Maximum number of tokens in the response
            temperature (float): Temperature for response generation (0.0 to 1.0)
            
        Returns:
            dict: Response from the LLM
        """
        if not self.api_key:
            logger.error("Groq API key is required for LLM functionality")
            return {"error": "API key is required", "text": ""}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            
            # Extract the generated text from the response
            if "choices" in result and len(result["choices"]) > 0:
                answer = result["choices"][0]["message"]["content"]
                return {"text": answer, "model": model}
            else:
                return {"error": "No response generated", "text": ""}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error querying Groq API: {str(e)}")
            return {"error": str(e), "text": ""}
    
    def analyze_financial_data(self, data, query=None):
        """
        Analyze financial data with LLM
        
        Args:
            data (str): Financial data to analyze
            query (str): Specific question to ask about the data
            
        Returns:
            dict: Analysis results from the LLM
        """
        prompt = f"""You are a financial advisor specialized in Indian markets. 
        
Data:
{data}

"""
        if query:
            prompt += f"Question: {query}\n\nProvide a detailed analysis focused on this question."
        else:
            prompt += "Analyze this financial data and provide key insights, trends, and recommendations."
            
        return self.generate_response(prompt, temperature=0.2)
    
    def explain_concept(self, concept, level="beginner"):
        """
        Explain a financial concept at different expertise levels
        
        Args:
            concept (str): Financial concept to explain
            level (str): Expertise level (beginner, intermediate, expert)
            
        Returns:
            dict: Explanation from the LLM
        """
        # Adjust the prompt based on the expertise level
        detail_level = {
            "beginner": "in simple terms, avoiding jargon",
            "intermediate": "with some technical details",
            "expert": "with detailed technical analysis"
        }.get(level.lower(), "in simple terms, avoiding jargon")
        
        prompt = f"""You are a financial educator specializing in Indian markets.

Explain the concept of '{concept}' {detail_level}. 
Include relevant examples from the Indian financial context.
If applicable, mention how this concept applies differently in the Indian market compared to global markets."""
        
        return self.generate_response(prompt, temperature=0.3)
    
    def generate_investment_advice(self, profile, market_conditions=None):
        """
        Generate personalized investment advice based on a user profile
        
        Args:
            profile (dict): User investment profile
            market_conditions (str): Current market conditions
            
        Returns:
            dict: Investment advice from the LLM
        """
        # Convert profile dict to a string description
        profile_str = "\n".join([f"{key}: {value}" for key, value in profile.items()])
        
        prompt = f"""You are a financial advisor specializing in the Indian market.

Investor Profile:
{profile_str}

"""
        if market_conditions:
            prompt += f"""
Current Market Conditions:
{market_conditions}

"""
        
        prompt += """Based on this profile and current market conditions, provide personalized investment advice for the Indian market.
Include:
1. Recommended asset allocation
2. Specific investment suggestions (mutual funds, stocks, etc.)
3. Risk considerations
4. Timeline recommendations
5. Tax efficiency suggestions relevant to Indian tax laws

Keep all advice specific to the Indian financial market and regulatory environment."""
        
        return self.generate_response(prompt, temperature=0.4, max_tokens=1500)

# Create a Groq client instance
groq_client = GroqClient()