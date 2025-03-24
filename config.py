"""
Configuration settings for the Indian Financial Analyzer
"""
import os
import logging
from pathlib import Path

# Application settings
APP_NAME = "Indian Financial Analyzer"
APP_VERSION = "1.0.0"
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

# Directory paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
BOOKS_DIR = DATA_DIR / "books"
CACHE_DIR = DATA_DIR / "cache"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
BOOKS_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)

# API keys from environment variables
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

# MongoDB settings
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME", "indian_financial_analyzer")

# LLM settings
LLM_MODEL = os.environ.get("LLM_MODEL", "llama3-70b-8192")
LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.5"))
LLM_MAX_TOKENS = int(os.environ.get("LLM_MAX_TOKENS", "4096"))

# RAG settings
EMBEDDING_CHUNK_SIZE = int(os.environ.get("EMBEDDING_CHUNK_SIZE", "1024"))
EMBEDDING_CHUNK_OVERLAP = int(os.environ.get("EMBEDDING_CHUNK_OVERLAP", "128"))

# API resource management
# Rate limiting settings for API calls to avoid exceeding free tier limits
TAVILY_RATE_LIMIT_PER_DAY = int(os.environ.get("TAVILY_RATE_LIMIT_PER_DAY", "50"))  # Conservative daily limit for Tavily API
GROQ_RATE_LIMIT_PER_DAY = int(os.environ.get("GROQ_RATE_LIMIT_PER_DAY", "100"))  # Conservative daily limit for Groq API
ENABLE_RESPONSE_CACHING = os.environ.get("ENABLE_RESPONSE_CACHING", "True").lower() == "true"
CACHE_EXPIRY_SECONDS = int(os.environ.get("CACHE_EXPIRY_SECONDS", "3600"))  # Default 1 hour cache for API responses

# Financial book settings
FINANCIAL_BOOKS = [
    {"id": "rich_dad_poor_dad", "title": "Rich Dad Poor Dad", "author": "Robert Kiyosaki"},
    {"id": "psychology_of_money", "title": "The Psychology of Money", "author": "Morgan Housel"},
    {"id": "intelligent_investor", "title": "The Intelligent Investor", "author": "Benjamin Graham"},
    {"id": "let_stocks_do_the_work", "title": "Let Stocks Do the Work", "author": "Ellis Traub"},
    {"id": "indian_financial_system", "title": "Indian Financial System", "author": "Bharati Pathak"}
]

# Logging configuration
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = os.environ.get("LOG_FILE", "indian_financial_analyzer.log")

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# Flask application settings
SECRET_KEY = os.environ.get("SECRET_KEY", os.urandom(24).hex())
SESSION_TYPE = "filesystem"
PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
TEMPLATES_AUTO_RELOAD = DEBUG