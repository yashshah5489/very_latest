"""
News Extraction Module for Indian Financial Analyzer using Tavily API
"""
import requests
import json
import logging
from datetime import datetime
import config

logger = logging.getLogger(__name__)

class TavilyNewsExtractor:
    """Class for extracting financial news using Tavily API with focus on Indian markets"""
    
    def __init__(self, api_key=None):
        """Initialize the news extractor with the Tavily API key"""
        self.api_key = api_key or config.TAVILY_API_KEY
        self.api_url = "https://api.tavily.com/search"
        
        if not self.api_key:
            logger.warning("Tavily API key not provided. News extraction functionality will be limited.")
    
    def search_financial_news(self, query, max_results=5, include_domains=None, exclude_domains=None, search_depth="advanced"):
        """
        Search for financial news using Tavily API
        
        Args:
            query (str): Search query string (e.g., "HDFC Bank quarterly results")
            max_results (int): Maximum number of results to return
            include_domains (list): List of domains to include in the search
            exclude_domains (list): List of domains to exclude from the search
            search_depth (str): Search depth (basic, advanced, or comprehensive)
            
        Returns:
            dict: Search results with news articles
        """
        if not self.api_key:
            logger.error("Tavily API key is required for news extraction")
            return {"error": "API key is required", "articles": []}
        
        # Default to Indian financial news sources if not specified
        if not include_domains:
            include_domains = [
                "economictimes.indiatimes.com",
                "moneycontrol.com",
                "livemint.com",
                "business-standard.com",
                "financialexpress.com",
                "thehindubusinessline.com"
            ]
        
        params = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": search_depth,
            "max_results": max_results
        }
        
        if include_domains:
            params["include_domains"] = include_domains
        
        if exclude_domains:
            params["exclude_domains"] = exclude_domains
        
        try:
            response = requests.get(self.api_url, params=params)
            response.raise_for_status()
            return self._process_results(response.json())
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching news from Tavily API: {str(e)}")
            return {"error": str(e), "articles": []}
    
    def _process_results(self, results):
        """Process and format the API results"""
        if not results or "results" not in results:
            return {"articles": []}
        
        articles = []
        for result in results.get("results", []):
            article = {
                "title": result.get("title", ""),
                "content": result.get("content", ""),
                "url": result.get("url", ""),
                "published_date": result.get("published_date", datetime.now().isoformat()),
                "source": result.get("source", ""),
                "relevance_score": result.get("relevance_score", 0),
                "retrieved_at": datetime.now().isoformat()
            }
            articles.append(article)
        
        return {
            "articles": articles,
            "count": len(articles)
        }
    
    def get_market_news(self, market="Indian", limit=10):
        """Get latest news for a specific market (defaults to Indian market)"""
        query = f"{market} stock market latest news"
        return self.search_financial_news(query, max_results=limit)
    
    def get_stock_news(self, symbol, company_name=None, limit=5):
        """Get news for a specific stock"""
        company = company_name or symbol
        query = f"{company} stock {symbol} latest news India"
        return self.search_financial_news(query, max_results=limit)
    
    def get_sector_news(self, sector, limit=5):
        """Get news for a specific sector in the Indian market"""
        query = f"India {sector} sector latest financial news"
        return self.search_financial_news(query, max_results=limit)
    
    def get_economic_indicators(self, limit=5):
        """Get news about Indian economic indicators"""
        query = "India latest economic indicators GDP inflation interest rates"
        return self.search_financial_news(query, max_results=limit)


# Create an instance of the news extractor
news_extractor = TavilyNewsExtractor()