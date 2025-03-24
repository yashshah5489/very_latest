"""
MongoDB Database Handler for Indian Financial Analyzer
"""
import pymongo
import motor.motor_asyncio
from pymongo.errors import ConnectionFailure
import logging
import config

logger = logging.getLogger(__name__)

class Database:
    """MongoDB database handler for the Indian Financial Analyzer"""
    
    def __init__(self, uri=None, db_name=None):
        """Initialize the database connection"""
        self.uri = uri or config.MONGODB_URI
        self.db_name = db_name or config.MONGODB_DB
        
        # Initialize sync client for regular operations
        self.client = None
        self.db = None
        
        # Initialize async client for non-blocking operations
        self.async_client = None
        self.async_db = None
        
        # Connect to the database
        self.connect()
    
    def connect(self):
        """Connect to MongoDB and set up collections"""
        try:
            # Setup synchronous connection
            self.client = pymongo.MongoClient(self.uri)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            
            # Setup asynchronous connection
            self.async_client = motor.motor_asyncio.AsyncIOMotorClient(self.uri)
            self.async_db = self.async_client[self.db_name]
            
            logger.info(f"Connected to MongoDB: {self.db_name}")
            return True
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            return False
    
    def get_collection(self, collection_name):
        """Get a synchronous collection by name"""
        return self.db[collection_name]
    
    def get_async_collection(self, collection_name):
        """Get an asynchronous collection by name"""
        return self.async_db[collection_name]
    
    # Stock Data Operations
    
    def add_indian_stock(self, stock_data):
        """Add or update an Indian stock in the database"""
        collection = self.get_collection(config.COLLECTION_STOCKS)
        query = {"symbol": stock_data["symbol"]}
        
        # Use upsert to insert if not exists, update if exists
        result = collection.update_one(query, {"$set": stock_data}, upsert=True)
        return result
    
    def get_indian_stock(self, symbol):
        """Get an Indian stock by symbol"""
        collection = self.get_collection(config.COLLECTION_STOCKS)
        return collection.find_one({"symbol": symbol})
    
    def get_indian_stocks(self, filter_query=None, limit=100):
        """Get multiple Indian stocks with optional filtering"""
        collection = self.get_collection(config.COLLECTION_STOCKS)
        query = filter_query or {}
        return list(collection.find(query).limit(limit))
    
    # Financial Books for RAG
    
    def add_financial_book(self, book_data):
        """Add a financial book to the database"""
        collection = self.get_collection(config.COLLECTION_FINANCIAL_BOOKS)
        query = {"id": book_data["id"]}
        result = collection.update_one(query, {"$set": book_data}, upsert=True)
        return result
    
    def get_financial_book(self, book_id):
        """Get a financial book by ID"""
        collection = self.get_collection(config.COLLECTION_FINANCIAL_BOOKS)
        return collection.find_one({"id": book_id})
    
    def get_all_financial_books(self):
        """Get all financial books"""
        collection = self.get_collection(config.COLLECTION_FINANCIAL_BOOKS)
        return list(collection.find())
    
    # News Articles
    
    def add_news_article(self, article_data):
        """Add a news article to the database"""
        collection = self.get_collection(config.COLLECTION_NEWS)
        # Check if article already exists by URL
        if "url" in article_data:
            query = {"url": article_data["url"]}
            # If exists, update it
            if collection.find_one(query):
                result = collection.update_one(query, {"$set": article_data})
                return result
        
        # Otherwise insert as new
        result = collection.insert_one(article_data)
        return result
    
    def get_news_articles(self, query=None, limit=20, sort_by="published_date", sort_direction=-1):
        """Get news articles with filtering and sorting"""
        collection = self.get_collection(config.COLLECTION_NEWS)
        filter_query = query or {}
        return list(collection.find(filter_query).sort(sort_by, sort_direction).limit(limit))
    
    # Analysis Results
    
    def save_analysis_result(self, analysis_data):
        """Save an analysis result"""
        collection = self.get_collection(config.COLLECTION_ANALYSIS)
        result = collection.insert_one(analysis_data)
        return result
    
    def get_analysis_history(self, user_id=None, limit=10):
        """Get analysis history for a user"""
        collection = self.get_collection(config.COLLECTION_ANALYSIS)
        query = {"user_id": user_id} if user_id else {}
        return list(collection.find(query).sort("timestamp", -1).limit(limit))
    
    # User Portfolios
    
    def save_user_portfolio(self, portfolio_data):
        """Save or update a user portfolio"""
        collection = self.get_collection(config.COLLECTION_USER_PORTFOLIOS)
        query = {"user_id": portfolio_data["user_id"]}
        result = collection.update_one(query, {"$set": portfolio_data}, upsert=True)
        return result
    
    def get_user_portfolio(self, user_id):
        """Get a user's portfolio"""
        collection = self.get_collection(config.COLLECTION_USER_PORTFOLIOS)
        return collection.find_one({"user_id": user_id})
    
    def close(self):
        """Close the database connection"""
        if self.client:
            self.client.close()
        if self.async_client:
            self.async_client.close()

# Create a database instance
db = Database()