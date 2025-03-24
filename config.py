"""
Configuration settings for the Indian Financial Analyzer
"""
import os

# MongoDB Configuration
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.environ.get("MONGODB_DB", "indian_financial_analyzer")

# Collections
COLLECTION_STOCKS = "indian_stocks"
COLLECTION_MARKET_DATA = "market_data"
COLLECTION_USER_PORTFOLIOS = "user_portfolios"
COLLECTION_FINANCIAL_BOOKS = "financial_books"
COLLECTION_NEWS = "financial_news"
COLLECTION_ANALYSIS = "analysis_results"

# API Keys and External Services
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# Indian Financial Market Settings
DEFAULT_INDEX = "NIFTY50"  # Default Indian market index
SUPPORTED_INDICES = ["NIFTY50", "SENSEX", "NIFTYBANK", "NIFTYMIDCAP"]

# Common Indian stock tickers for demonstration
DEMO_STOCK_TICKERS = [
    "RELIANCE.NS",  # Reliance Industries
    "TCS.NS",       # Tata Consultancy Services
    "HDFCBANK.NS",  # HDFC Bank
    "INFY.NS",      # Infosys
    "HINDUNILVR.NS" # Hindustan Unilever
]

# Financial Books for RAG
FINANCIAL_BOOKS = [
    {
        "id": "rich_dad_poor_dad",
        "title": "Rich Dad Poor Dad",
        "author": "Robert Kiyosaki",
        "path": "data/books/rich_dad_poor_dad.txt"
    },
    {
        "id": "psychology_of_money",
        "title": "The Psychology of Money",
        "author": "Morgan Housel",
        "path": "data/books/psychology_of_money.txt"
    },
    {
        "id": "richest_man_in_babylon",
        "title": "The Richest Man in Babylon",
        "author": "George S. Clason",
        "path": "data/books/richest_man_in_babylon.txt"
    }
]

# Application settings
APP_NAME = "Indian Financial Analyzer"
DEBUG = True
SECRET_KEY = os.environ.get("SECRET_KEY", "development-secret-key")