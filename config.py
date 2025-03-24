"""
Configuration settings for the Indian Financial Analyzer
"""
import os

# Application settings
APP_NAME = "Indian Financial Analyzer"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "AI-powered financial analysis for Indian markets"

# Logging settings
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = "indian_financial_analyzer.log"

# API Keys
# These are loaded from environment variables
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Database settings
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME", "indian_financial_analyzer")

# File paths
DATA_DIR = "data"
BOOKS_DIR = os.path.join(DATA_DIR, "books")
CACHE_DIR = os.path.join(DATA_DIR, "cache")

# Ensure directories exist
os.makedirs(BOOKS_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# Market settings
DEFAULT_MARKET = "Indian"