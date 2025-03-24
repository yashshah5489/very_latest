"""
News Extractor using Tavily API with caching to conserve API usage limits
"""
import os
import json
import logging
import requests
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

# Import cache manager for API usage optimization
try:
    from utils.cache_manager import cache_manager
except ImportError:
    # Fallback if the cache manager is not available
    cache_manager = None
    logger = logging.getLogger(__name__)
    logger.warning("Cache manager not available, API usage will not be optimized")
else:
    logger = logging.getLogger(__name__)

class NewsExtractor:
    """News extraction service using Tavily API with caching to minimize API usage"""
    
    def __init__(self, api_key=None):
        """
        Initialize news extractor with Tavily API key.
        
        Args:
            api_key: Optional Tavily API key
        """
        self.api_key = api_key or os.environ.get("TAVILY_API_KEY")
        if not self.api_key:
            logger.warning("No Tavily API key provided. Set the TAVILY_API_KEY environment variable.")
        
        self.api_base = "https://api.tavily.com/v1"
        self.search_endpoint = f"{self.api_base}/search"
        
        # Check if caching is available
        self.caching_enabled = cache_manager is not None
        
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to the Tavily API with caching to minimize API usage.
        
        Args:
            endpoint: API endpoint
            params: Request parameters
            
        Returns:
            API response as a dictionary
        """
        if not self.api_key:
            return {"error": "API key not configured. Please set TAVILY_API_KEY environment variable."}
        
        # Generate a cache key from the endpoint and params
        cache_key = f"tavily_{endpoint}_{hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()}"
        
        # Check if we have a cached response
        if self.caching_enabled:
            cached_response = cache_manager.get(cache_key)
            if cached_response:
                logger.info(f"Using cached response for Tavily API request to {endpoint}")
                return cached_response
            
            # Check if we have exceeded the rate limit
            if not cache_manager.track_api_call("tavily"):
                logger.warning("Tavily API daily rate limit exceeded")
                return {"error": "Daily rate limit for Tavily API exceeded. Try again tomorrow."}
        
        # Make the API request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            url = self.search_endpoint if endpoint == "search" else f"{self.api_base}/{endpoint}"
            logger.info(f"Making Tavily API request to {url}")
            
            response = requests.post(
                url,
                headers=headers,
                json=params
            )
            response.raise_for_status()
            result = response.json()
            
            # Cache the successful response
            if self.caching_enabled and "error" not in result:
                cache_manager.set(cache_key, result)
                
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Tavily API: {str(e)}")
            return {"error": str(e)}
        
    def _parse_search_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse search results from the Tavily API.
        
        Args:
            results: Raw search results from the API
            
        Returns:
            Parsed news data
        """
        if "error" in results:
            return results
            
        if "results" not in results:
            return {"error": "No results found in API response"}
        
        articles = []
        for result in results.get("results", []):
            # Extract data from each result
            article = {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", ""),
                "source": result.get("source", "Unknown"),
                "published_date": result.get("published_date", "")
            }
            articles.append(article)
        
        return {
            "articles": articles,
            "search_id": results.get("search_id", ""),
            "count": len(articles)
        }
        
    def search_financial_news(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Search for financial news based on a query.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary containing news articles
        """
        # Append "India" to the query for India-specific results
        if "india" not in query.lower() and "indian" not in query.lower():
            query = f"{query} India"
            
        params = {
            "query": query,
            "search_depth": "advanced",
            "include_answer": False,
            "include_domains": [
                "moneycontrol.com", "economictimes.indiatimes.com", 
                "livemint.com", "thehindubusinessline.com", 
                "financialexpress.com", "business-standard.com",
                "investing.com", "cnbctv18.com", "ndtv.com/business",
                "bloomberg.com", "reuters.com", "ft.com"
            ],
            "max_results": max_results
        }
        
        results = self._make_request("search", params)
        return self._parse_search_results(results)
        
    def get_market_news(self, market: str = "Indian", limit: int = 10) -> Dict[str, Any]:
        """
        Get general market news.
        
        Args:
            market: Market to get news for (default: "Indian")
            limit: Maximum number of news items to return
            
        Returns:
            Dictionary containing news articles
        """
        query = f"{market} stock market news latest updates"
        return self.search_financial_news(query, limit)
        
    def get_stock_news(self, symbol: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get news for a specific stock.
        
        Args:
            symbol: Stock symbol
            limit: Maximum number of news items to return
            
        Returns:
            Dictionary containing news articles
        """
        query = f"{symbol} stock news latest updates India"
        return self.search_financial_news(query, limit)
        
    def get_sector_news(self, sector: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get news for a specific market sector.
        
        Args:
            sector: Market sector (e.g. "Technology", "Banking")
            limit: Maximum number of news items to return
            
        Returns:
            Dictionary containing news articles
        """
        query = f"Indian {sector} sector stock market news latest updates"
        return self.search_financial_news(query, limit)
        
    def get_economic_indicators(self, limit: int = 10) -> Dict[str, Any]:
        """
        Get news about economic indicators.
        
        Args:
            limit: Maximum number of news items to return
            
        Returns:
            Dictionary containing news articles
        """
        query = "Indian economic indicators RBI inflation GDP growth latest updates"
        return self.search_financial_news(query, limit)
        
    def get_company_news(self, company_name: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get news for a specific company by name.
        
        Args:
            company_name: Company name
            limit: Maximum number of news items to return
            
        Returns:
            Dictionary containing news articles
        """
        query = f"{company_name} company news India latest updates"
        return self.search_financial_news(query, limit)
        
    def get_financial_insights(self, topic: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get financial insights on a specific topic.
        
        Args:
            topic: Financial topic
            limit: Maximum number of results to return
            
        Returns:
            Dictionary containing news articles with insights
        """
        query = f"Indian financial insights analysis {topic}"
        
        params = {
            "query": query,
            "search_depth": "advanced",
            "include_answer": True,  # Include Tavily's generated answer for insights
            "include_domains": [
                "moneycontrol.com", "economictimes.indiatimes.com", 
                "livemint.com", "thehindubusinessline.com", 
                "financialexpress.com", "business-standard.com",
                "investing.com", "cnbctv18.com", "ndtv.com/business",
                "bloomberg.com", "reuters.com", "ft.com"
            ],
            "max_results": limit
        }
        
        results = self._make_request("search", params)
        
        # Parse results and add the generated answer as insights if available
        parsed_results = self._parse_search_results(results)
        
        if "answer" in results:
            parsed_results["insights"] = results["answer"]
            
        return parsed_results


# Initialize global instance
news_extractor = NewsExtractor()