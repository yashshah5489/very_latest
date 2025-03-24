"""
MongoDB Database Handler for Indian Financial Analyzer
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

import pymongo
from pymongo.errors import ConnectionFailure, OperationFailure
import motor.motor_asyncio

import config

logger = logging.getLogger(__name__)

class Database:
    """MongoDB database handler for the Indian Financial Analyzer"""
    
    def __init__(self, uri=None, db_name=None):
        """Initialize the database connection"""
        self.uri = uri or config.MONGODB_URI
        self.db_name = db_name or config.MONGODB_DB_NAME
        self.client = None
        self.async_client = None
        self.db = None
        self.async_db = None
        self.connected = False
        
        # Collections
        self.indian_stocks = None
        self.financial_books = None
        self.news_articles = None
        self.analysis_results = None
        self.user_portfolios = None
        
        # Try to connect immediately
        try:
            self.connect()
        except Exception as e:
            logger.warning(f"Could not connect to MongoDB on initialization: {str(e)}")
    
    def connect(self):
        """Connect to MongoDB and set up collections"""
        try:
            # Synchronous client
            self.client = pymongo.MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            # Check connection by pinging
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            
            # Asynchronous client
            self.async_client = motor.motor_asyncio.AsyncIOMotorClient(self.uri)
            self.async_db = self.async_client[self.db_name]
            
            # Set up collections
            self.indian_stocks = self.db.indian_stocks
            self.financial_books = self.db.financial_books
            self.news_articles = self.db.news_articles
            self.analysis_results = self.db.analysis_results
            self.user_portfolios = self.db.user_portfolios
            
            # Create indices
            self._create_indexes()
            
            logger.info(f"Connected to MongoDB database: {self.db_name}")
            self.connected = True
            return True
            
        except (ConnectionFailure, OperationFailure) as e:
            logger.error(f"Could not connect to MongoDB: {str(e)}")
            self.connected = False
            return False
    
    def _create_indexes(self):
        """Create necessary indexes for collections"""
        try:
            # Indian stocks collection
            self.indian_stocks.create_index([("symbol", pymongo.ASCENDING)], unique=True)
            self.indian_stocks.create_index([("name", pymongo.TEXT)])
            
            # Financial books collection
            self.financial_books.create_index([("id", pymongo.ASCENDING)], unique=True)
            self.financial_books.create_index([("title", pymongo.TEXT), ("author", pymongo.TEXT)])
            self.financial_books.create_index([("tags", pymongo.ASCENDING)])
            
            # News articles collection
            self.news_articles.create_index([("url", pymongo.ASCENDING)], unique=True)
            self.news_articles.create_index([("title", pymongo.TEXT), ("content", pymongo.TEXT)])
            self.news_articles.create_index([("published_date", pymongo.DESCENDING)])
            self.news_articles.create_index([("tags", pymongo.ASCENDING)])
            
            # Analysis results collection
            self.analysis_results.create_index([("analysis_type", pymongo.ASCENDING)])
            self.analysis_results.create_index([("user_id", pymongo.ASCENDING)])
            self.analysis_results.create_index([("timestamp", pymongo.DESCENDING)])
            
            # User portfolios collection
            self.user_portfolios.create_index([("user_id", pymongo.ASCENDING)], unique=True)
            
            logger.info("Created database indexes")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {str(e)}")
    
    def get_collection(self, collection_name):
        """Get a synchronous collection by name"""
        if not self.connected:
            return None
            
        return self.db[collection_name]
    
    def get_async_collection(self, collection_name):
        """Get an asynchronous collection by name"""
        if not self.connected:
            return None
            
        return self.async_db[collection_name]
    
    def add_indian_stock(self, stock_data):
        """Add or update an Indian stock in the database"""
        if not self.connected:
            logger.warning("Cannot add stock, database not connected")
            return None
            
        try:
            # Update or insert stock data
            result = self.indian_stocks.update_one(
                {"symbol": stock_data["symbol"]},
                {"$set": stock_data},
                upsert=True
            )
            
            return result.upserted_id or stock_data["symbol"]
            
        except Exception as e:
            logger.error(f"Error adding Indian stock: {str(e)}")
            return None
    
    def get_indian_stock(self, symbol):
        """Get an Indian stock by symbol"""
        if not self.connected:
            logger.warning("Cannot get stock, database not connected")
            return None
            
        try:
            # Find stock by symbol
            stock = self.indian_stocks.find_one({"symbol": symbol})
            
            if not stock:
                return None
                
            # Convert ObjectId to string
            if "_id" in stock:
                stock["_id"] = str(stock["_id"])
                
            return stock
            
        except Exception as e:
            logger.error(f"Error getting Indian stock: {str(e)}")
            return None
    
    def get_indian_stocks(self, filter_query=None, limit=100):
        """Get multiple Indian stocks with optional filtering"""
        if not self.connected:
            logger.warning("Cannot get stocks, database not connected")
            return []
            
        try:
            # Find stocks with optional filter
            cursor = self.indian_stocks.find(filter_query or {}).limit(limit)
            
            # Convert to list and fix ObjectId
            stocks = []
            for stock in cursor:
                if "_id" in stock:
                    stock["_id"] = str(stock["_id"])
                stocks.append(stock)
                
            return stocks
            
        except Exception as e:
            logger.error(f"Error getting Indian stocks: {str(e)}")
            return []
    
    def add_financial_book(self, book_data):
        """Add a financial book to the database"""
        if not self.connected:
            logger.warning("Cannot add book, database not connected")
            return None
            
        try:
            # Ensure book has required fields
            required_fields = ["id", "title", "author"]
            for field in required_fields:
                if field not in book_data:
                    logger.error(f"Book data missing required field: {field}")
                    return None
            
            # Update or insert book data
            result = self.financial_books.update_one(
                {"id": book_data["id"]},
                {"$set": book_data},
                upsert=True
            )
            
            return result.upserted_id or book_data["id"]
            
        except Exception as e:
            logger.error(f"Error adding financial book: {str(e)}")
            return None
    
    def get_financial_book(self, book_id):
        """Get a financial book by ID"""
        if not self.connected:
            logger.warning("Cannot get book, database not connected")
            return None
            
        try:
            # Find book by ID
            book = self.financial_books.find_one({"id": book_id})
            
            if not book:
                return None
                
            # Convert ObjectId to string
            if "_id" in book:
                book["_id"] = str(book["_id"])
                
            return book
            
        except Exception as e:
            logger.error(f"Error getting financial book: {str(e)}")
            return None
    
    def get_all_financial_books(self):
        """Get all financial books"""
        if not self.connected:
            logger.warning("Cannot get books, database not connected")
            return []
            
        try:
            # Find all books
            cursor = self.financial_books.find()
            
            # Convert to list and fix ObjectId
            books = []
            for book in cursor:
                if "_id" in book:
                    book["_id"] = str(book["_id"])
                books.append(book)
                
            return books
            
        except Exception as e:
            logger.error(f"Error getting financial books: {str(e)}")
            return []
    
    def add_news_article(self, article_data):
        """Add a news article to the database"""
        if not self.connected:
            logger.warning("Cannot add news article, database not connected")
            return None
            
        try:
            # Ensure article has required fields
            required_fields = ["title", "url"]
            for field in required_fields:
                if field not in article_data:
                    logger.error(f"Article data missing required field: {field}")
                    return None
            
            # Add timestamp if not present
            if "timestamp" not in article_data:
                article_data["timestamp"] = datetime.now()
            
            # Update or insert article data
            result = self.news_articles.update_one(
                {"url": article_data["url"]},
                {"$set": article_data},
                upsert=True
            )
            
            return result.upserted_id or article_data["url"]
            
        except Exception as e:
            logger.error(f"Error adding news article: {str(e)}")
            return None
    
    def get_news_articles(self, query=None, limit=20, sort_by="published_date", sort_direction=-1):
        """Get news articles with filtering and sorting"""
        if not self.connected:
            logger.warning("Cannot get news articles, database not connected")
            return []
            
        try:
            # Find articles with optional filter, sorting and limit
            cursor = self.news_articles.find(query or {}).sort(sort_by, sort_direction).limit(limit)
            
            # Convert to list and fix ObjectId
            articles = []
            for article in cursor:
                if "_id" in article:
                    article["_id"] = str(article["_id"])
                    
                # Convert datetime to string
                if "timestamp" in article and isinstance(article["timestamp"], datetime):
                    article["timestamp"] = article["timestamp"].isoformat()
                if "published_date" in article and isinstance(article["published_date"], datetime):
                    article["published_date"] = article["published_date"].isoformat()
                    
                articles.append(article)
                
            return articles
            
        except Exception as e:
            logger.error(f"Error getting news articles: {str(e)}")
            return []
    
    def save_analysis_result(self, analysis_data):
        """Save an analysis result"""
        if not self.connected:
            logger.warning("Cannot save analysis result, database not connected")
            return None
            
        try:
            # Ensure result has required fields
            required_fields = ["analysis_type", "content"]
            for field in required_fields:
                if field not in analysis_data:
                    logger.error(f"Analysis data missing required field: {field}")
                    return None
            
            # Add timestamp if not present
            if "timestamp" not in analysis_data:
                analysis_data["timestamp"] = datetime.now()
            
            # Insert analysis data
            result = self.analysis_results.insert_one(analysis_data)
            
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error saving analysis result: {str(e)}")
            return None
    
    def get_analysis_history(self, user_id=None, limit=10):
        """Get analysis history for a user"""
        if not self.connected:
            logger.warning("Cannot get analysis history, database not connected")
            return []
            
        try:
            # Filter by user_id if provided
            query = {"user_id": user_id} if user_id else {}
            
            # Find analysis results, sorted by timestamp
            cursor = self.analysis_results.find(query).sort("timestamp", -1).limit(limit)
            
            # Convert to list and fix ObjectId
            results = []
            for result in cursor:
                if "_id" in result:
                    result["_id"] = str(result["_id"])
                    
                # Convert timestamp to string
                if "timestamp" in result and isinstance(result["timestamp"], datetime):
                    result["timestamp"] = result["timestamp"].isoformat()
                    
                results.append(result)
                
            return results
            
        except Exception as e:
            logger.error(f"Error getting analysis history: {str(e)}")
            return []
    
    def save_user_portfolio(self, portfolio_data):
        """Save or update a user portfolio"""
        if not self.connected:
            logger.warning("Cannot save user portfolio, database not connected")
            return None
            
        try:
            # Ensure portfolio has required fields
            required_fields = ["user_id"]
            for field in required_fields:
                if field not in portfolio_data:
                    logger.error(f"Portfolio data missing required field: {field}")
                    return None
            
            # Add timestamp if not present
            if "last_updated" not in portfolio_data:
                portfolio_data["last_updated"] = datetime.now()
            
            # Update or insert portfolio data
            result = self.user_portfolios.update_one(
                {"user_id": portfolio_data["user_id"]},
                {"$set": portfolio_data},
                upsert=True
            )
            
            return result.upserted_id or portfolio_data["user_id"]
            
        except Exception as e:
            logger.error(f"Error saving user portfolio: {str(e)}")
            return None
    
    def get_user_portfolio(self, user_id):
        """Get a user's portfolio"""
        if not self.connected:
            logger.warning("Cannot get user portfolio, database not connected")
            return None
            
        try:
            # Find portfolio by user_id
            portfolio = self.user_portfolios.find_one({"user_id": user_id})
            
            if not portfolio:
                return None
                
            # Convert ObjectId to string
            if "_id" in portfolio:
                portfolio["_id"] = str(portfolio["_id"])
                
            # Convert timestamp to string
            if "last_updated" in portfolio and isinstance(portfolio["last_updated"], datetime):
                portfolio["last_updated"] = portfolio["last_updated"].isoformat()
                
            return portfolio
            
        except Exception as e:
            logger.error(f"Error getting user portfolio: {str(e)}")
            return None
    
    def close(self):
        """Close the database connection"""
        if self.client:
            self.client.close()
        if self.async_client:
            self.async_client.close()
        self.connected = False
        logger.info("Database connection closed")


# Initialize global instance
db = Database()