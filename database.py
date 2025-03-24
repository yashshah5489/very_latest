"""
PostgreSQL Database Handler for Indian Financial Analyzer
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import json

import sqlalchemy
from sqlalchemy import create_engine, Column, String, Integer, Float, JSON, Table, MetaData, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import text

import config

logger = logging.getLogger(__name__)

# Create SQLAlchemy Base
Base = declarative_base()

# Define models
class IndianStock(Base):
    """Model for Indian stocks"""
    __tablename__ = 'indian_stocks'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    sector = Column(String(50), index=True)
    industry = Column(String(50), index=True)
    current_price = Column(Float)
    change_percent = Column(Float)
    market_cap = Column(Float)
    pe_ratio = Column(Float)
    eps = Column(Float)
    dividend_yield = Column(Float)
    high_52w = Column(Float)
    low_52w = Column(Float)
    volume = Column(Integer)
    avg_volume = Column(Integer)
    data = Column(JSONB)  # For additional flexible data
    last_updated = Column(DateTime, default=datetime.now)
    
class FinancialBook(Base):
    """Model for financial books"""
    __tablename__ = 'financial_books'
    
    id = Column(String(50), primary_key=True)
    title = Column(String(200), nullable=False, index=True)
    author = Column(String(100), nullable=False, index=True)
    year = Column(Integer)
    description = Column(Text)
    tags = Column(JSONB)  # Array of tags
    book_metadata = Column(JSONB)  # Additional metadata
    
class NewsArticle(Base):
    """Model for news articles"""
    __tablename__ = 'news_articles'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False, index=True)
    url = Column(String(500), unique=True, nullable=False)
    source = Column(String(100), index=True)
    author = Column(String(100))
    published_date = Column(DateTime, index=True)
    content = Column(Text)
    summary = Column(Text)
    sentiment = Column(Float)
    entities = Column(JSONB)  # Named entities mentioned in the article
    tags = Column(JSONB)  # Array of tags
    timestamp = Column(DateTime, default=datetime.now)
    
class AnalysisResult(Base):
    """Model for analysis results"""
    __tablename__ = 'analysis_results'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), index=True)
    analysis_type = Column(String(50), index=True)
    subject = Column(String(100), index=True)  # What was analyzed (stock symbol, etc.)
    content = Column(JSONB)  # Analysis content in JSON format
    summary = Column(Text)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    
class UserPortfolio(Base):
    """Model for user portfolios"""
    __tablename__ = 'user_portfolios'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(100))
    holdings = Column(JSONB)  # Portfolio holdings
    performance = Column(JSONB)  # Performance metrics
    settings = Column(JSONB)  # User settings
    last_updated = Column(DateTime, default=datetime.now)

class Database:
    """PostgreSQL database handler for the Indian Financial Analyzer"""
    
    def __init__(self, database_url=None):
        """Initialize the database connection"""
        self.database_url = database_url or os.environ.get("DATABASE_URL")
        self.engine = None
        self.session_factory = None
        self.Session = None
        self.connected = False
        
        # Try to connect immediately
        try:
            self.connect()
        except Exception as e:
            logger.warning(f"Could not connect to PostgreSQL on initialization: {str(e)}")
    
    def connect(self):
        """Connect to PostgreSQL and set up tables"""
        try:
            # Create engine
            self.engine = create_engine(self.database_url)
            
            # Create all tables if they don't exist
            Base.metadata.create_all(self.engine)
            
            # Create session factory
            self.session_factory = sessionmaker(bind=self.engine)
            self.Session = scoped_session(self.session_factory)
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text('SELECT 1'))
            
            logger.info(f"Connected to PostgreSQL database")
            self.connected = True
            return True
            
        except Exception as e:
            logger.error(f"Could not connect to PostgreSQL: {str(e)}")
            self.connected = False
            return False
    
    def add_indian_stock(self, stock_data):
        """Add or update an Indian stock in the database"""
        if not self.connected:
            logger.warning("Cannot add stock, database not connected")
            return None
            
        try:
            session = self.Session()
            
            # Check if stock exists
            stock = session.query(IndianStock).filter_by(symbol=stock_data["symbol"]).first()
            
            if stock:
                # Update existing stock
                for key, value in stock_data.items():
                    if key == 'data':
                        # Merge data dictionaries
                        if stock.data is None:
                            stock.data = value
                        else:
                            stock_data_dict = stock.data.copy()
                            stock_data_dict.update(value)
                            stock.data = stock_data_dict
                    elif hasattr(stock, key):
                        setattr(stock, key, value)
                stock.last_updated = datetime.now()
            else:
                # Create new stock
                # Extract known fields
                known_fields = {k: v for k, v in stock_data.items() if k in [
                    'symbol', 'name', 'sector', 'industry', 'current_price', 
                    'change_percent', 'market_cap', 'pe_ratio', 'eps', 
                    'dividend_yield', 'volume', 'avg_volume'
                ]}
                
                # Put all other fields in data JSON
                data_fields = {k: v for k, v in stock_data.items() if k not in known_fields}
                known_fields['data'] = data_fields
                known_fields['last_updated'] = datetime.now()
                
                if 'high_52w' in stock_data:
                    known_fields['high_52w'] = stock_data['high_52w']
                if 'low_52w' in stock_data:
                    known_fields['low_52w'] = stock_data['low_52w']
                
                stock = IndianStock(**known_fields)
                session.add(stock)
                
            session.commit()
            stock_id = stock.id
            session.close()
            
            return stock_id
            
        except Exception as e:
            logger.error(f"Error adding Indian stock: {str(e)}")
            if session:
                session.rollback()
                session.close()
            return None
    
    def get_indian_stock(self, symbol):
        """Get an Indian stock by symbol"""
        if not self.connected:
            logger.warning("Cannot get stock, database not connected")
            return None
            
        try:
            session = self.Session()
            stock = session.query(IndianStock).filter_by(symbol=symbol).first()
            
            if not stock:
                session.close()
                return None
                
            # Convert to dictionary
            stock_dict = {
                'id': stock.id,
                'symbol': stock.symbol,
                'name': stock.name,
                'sector': stock.sector,
                'industry': stock.industry,
                'current_price': stock.current_price,
                'change_percent': stock.change_percent,
                'market_cap': stock.market_cap,
                'pe_ratio': stock.pe_ratio,
                'eps': stock.eps,
                'dividend_yield': stock.dividend_yield,
                'high_52w': stock.high_52w,
                'low_52w': stock.low_52w,
                'volume': stock.volume,
                'avg_volume': stock.avg_volume,
                'last_updated': stock.last_updated.isoformat() if stock.last_updated else None
            }
            
            # Add data fields
            if stock.data:
                stock_dict.update(stock.data)
                
            session.close()
            return stock_dict
            
        except Exception as e:
            logger.error(f"Error getting Indian stock: {str(e)}")
            if 'session' in locals() and session:
                session.close()
            return None
    
    def get_indian_stocks(self, filter_query=None, limit=100):
        """Get multiple Indian stocks with optional filtering"""
        if not self.connected:
            logger.warning("Cannot get stocks, database not connected")
            return []
            
        try:
            session = self.Session()
            query = session.query(IndianStock)
            
            # Apply filters if provided
            if filter_query:
                if 'sector' in filter_query:
                    query = query.filter(IndianStock.sector == filter_query['sector'])
                if 'industry' in filter_query:
                    query = query.filter(IndianStock.industry == filter_query['industry'])
                if 'name_contains' in filter_query:
                    query = query.filter(IndianStock.name.ilike(f"%{filter_query['name_contains']}%"))
                if 'symbol_contains' in filter_query:
                    query = query.filter(IndianStock.symbol.ilike(f"%{filter_query['symbol_contains']}%"))
            
            # Apply limit
            stocks = query.limit(limit).all()
            
            # Convert to list of dictionaries
            result = []
            for stock in stocks:
                stock_dict = {
                    'id': stock.id,
                    'symbol': stock.symbol,
                    'name': stock.name,
                    'sector': stock.sector,
                    'industry': stock.industry,
                    'current_price': stock.current_price,
                    'change_percent': stock.change_percent
                }
                
                # Add data fields
                if stock.data:
                    stock_dict.update(stock.data)
                    
                result.append(stock_dict)
                
            session.close()
            return result
            
        except Exception as e:
            logger.error(f"Error getting Indian stocks: {str(e)}")
            if 'session' in locals() and session:
                session.close()
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
            
            session = self.Session()
            
            # Check if book exists
            book = session.query(FinancialBook).filter_by(id=book_data["id"]).first()
            
            if book:
                # Update existing book
                for key, value in book_data.items():
                    if key == 'metadata':
                        # Merge metadata dictionaries
                        if book.metadata is None:
                            book.metadata = value
                        else:
                            metadata_dict = book.metadata.copy()
                            metadata_dict.update(value)
                            book.metadata = metadata_dict
                    elif hasattr(book, key):
                        setattr(book, key, value)
            else:
                # Create new book
                # Extract known fields
                known_fields = {k: v for k, v in book_data.items() if k in [
                    'id', 'title', 'author', 'year', 'description', 'tags'
                ]}
                
                # Put all other fields in metadata
                metadata_fields = {k: v for k, v in book_data.items() if k not in known_fields}
                if metadata_fields:
                    known_fields['metadata'] = metadata_fields
                
                book = FinancialBook(**known_fields)
                session.add(book)
                
            session.commit()
            book_id = book.id
            session.close()
            
            return book_id
            
        except Exception as e:
            logger.error(f"Error adding financial book: {str(e)}")
            if 'session' in locals() and session:
                session.rollback()
                session.close()
            return None
    
    def get_financial_book(self, book_id):
        """Get a financial book by ID"""
        if not self.connected:
            logger.warning("Cannot get book, database not connected")
            return None
            
        try:
            session = self.Session()
            book = session.query(FinancialBook).filter_by(id=book_id).first()
            
            if not book:
                session.close()
                return None
                
            # Convert to dictionary
            book_dict = {
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'year': book.year,
                'description': book.description,
                'tags': book.tags
            }
            
            # Add metadata fields
            if book.metadata:
                book_dict.update(book.metadata)
                
            session.close()
            return book_dict
            
        except Exception as e:
            logger.error(f"Error getting financial book: {str(e)}")
            if 'session' in locals() and session:
                session.close()
            return None
    
    def get_all_financial_books(self):
        """Get all financial books"""
        if not self.connected:
            logger.warning("Cannot get books, database not connected")
            return []
            
        try:
            session = self.Session()
            books = session.query(FinancialBook).all()
            
            # Convert to list of dictionaries
            result = []
            for book in books:
                book_dict = {
                    'id': book.id,
                    'title': book.title,
                    'author': book.author,
                    'year': book.year,
                    'description': book.description,
                    'tags': book.tags
                }
                
                # Add metadata fields
                if book.metadata:
                    book_dict.update(book.metadata)
                    
                result.append(book_dict)
                
            session.close()
            return result
            
        except Exception as e:
            logger.error(f"Error getting financial books: {str(e)}")
            if 'session' in locals() and session:
                session.close()
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
            
            session = self.Session()
            
            # Check if article exists
            article = session.query(NewsArticle).filter_by(url=article_data["url"]).first()
            
            if article:
                # Update existing article
                for key, value in article_data.items():
                    if hasattr(article, key):
                        setattr(article, key, value)
                article.timestamp = datetime.now()
            else:
                # Create new article
                # Extract known fields
                known_fields = {k: v for k, v in article_data.items() if k in [
                    'title', 'url', 'source', 'author', 'published_date', 
                    'content', 'summary', 'sentiment', 'entities', 'tags'
                ]}
                
                # Set timestamp
                known_fields['timestamp'] = datetime.now()
                
                article = NewsArticle(**known_fields)
                session.add(article)
                
            session.commit()
            article_id = article.id
            session.close()
            
            return article_id
            
        except Exception as e:
            logger.error(f"Error adding news article: {str(e)}")
            if 'session' in locals() and session:
                session.rollback()
                session.close()
            return None
    
    def get_news_articles(self, query=None, limit=20, sort_by="published_date", sort_direction=-1):
        """Get news articles with filtering and sorting"""
        if not self.connected:
            logger.warning("Cannot get news articles, database not connected")
            return []
            
        try:
            session = self.Session()
            db_query = session.query(NewsArticle)
            
            # Apply filters if provided
            if query:
                if 'source' in query:
                    db_query = db_query.filter(NewsArticle.source == query['source'])
                if 'title_contains' in query:
                    db_query = db_query.filter(NewsArticle.title.ilike(f"%{query['title_contains']}%"))
                if 'content_contains' in query:
                    db_query = db_query.filter(NewsArticle.content.ilike(f"%{query['content_contains']}%"))
                if 'after_date' in query:
                    db_query = db_query.filter(NewsArticle.published_date >= query['after_date'])
                if 'before_date' in query:
                    db_query = db_query.filter(NewsArticle.published_date <= query['before_date'])
            
            # Apply sorting
            if sort_direction < 0:
                db_query = db_query.order_by(getattr(NewsArticle, sort_by).desc())
            else:
                db_query = db_query.order_by(getattr(NewsArticle, sort_by))
            
            # Apply limit
            articles = db_query.limit(limit).all()
            
            # Convert to list of dictionaries
            result = []
            for article in articles:
                article_dict = {
                    'id': article.id,
                    'title': article.title,
                    'url': article.url,
                    'source': article.source,
                    'author': article.author,
                    'published_date': article.published_date.isoformat() if article.published_date else None,
                    'content': article.content,
                    'summary': article.summary,
                    'sentiment': article.sentiment,
                    'entities': article.entities,
                    'tags': article.tags,
                    'timestamp': article.timestamp.isoformat() if article.timestamp else None
                }
                
                result.append(article_dict)
                
            session.close()
            return result
            
        except Exception as e:
            logger.error(f"Error getting news articles: {str(e)}")
            if 'session' in locals() and session:
                session.close()
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
            
            session = self.Session()
            
            # Add timestamp if not present
            if "timestamp" not in analysis_data:
                analysis_data["timestamp"] = datetime.now()
            
            # Extract known fields
            known_fields = {k: v for k, v in analysis_data.items() if k in [
                'user_id', 'analysis_type', 'subject', 'content', 'summary', 'timestamp'
            ]}
            
            # Create new analysis result
            analysis_result = AnalysisResult(**known_fields)
            session.add(analysis_result)
            
            session.commit()
            result_id = analysis_result.id
            session.close()
            
            return result_id
            
        except Exception as e:
            logger.error(f"Error saving analysis result: {str(e)}")
            if 'session' in locals() and session:
                session.rollback()
                session.close()
            return None
    
    def get_analysis_history(self, user_id=None, limit=10):
        """Get analysis history for a user"""
        if not self.connected:
            logger.warning("Cannot get analysis history, database not connected")
            return []
            
        try:
            session = self.Session()
            db_query = session.query(AnalysisResult)
            
            # Filter by user_id if provided
            if user_id:
                db_query = db_query.filter(AnalysisResult.user_id == user_id)
            
            # Apply sorting and limit
            results = db_query.order_by(AnalysisResult.timestamp.desc()).limit(limit).all()
            
            # Convert to list of dictionaries
            result = []
            for ar in results:
                ar_dict = {
                    'id': ar.id,
                    'user_id': ar.user_id,
                    'analysis_type': ar.analysis_type,
                    'subject': ar.subject,
                    'content': ar.content,
                    'summary': ar.summary,
                    'timestamp': ar.timestamp.isoformat() if ar.timestamp else None
                }
                
                result.append(ar_dict)
                
            session.close()
            return result
            
        except Exception as e:
            logger.error(f"Error getting analysis history: {str(e)}")
            if 'session' in locals() and session:
                session.close()
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
            
            session = self.Session()
            
            # Check if portfolio exists
            portfolio = session.query(UserPortfolio).filter_by(user_id=portfolio_data["user_id"]).first()
            
            if portfolio:
                # Update existing portfolio
                for key, value in portfolio_data.items():
                    if key in ['holdings', 'performance', 'settings']:
                        # Merge dictionaries
                        current_value = getattr(portfolio, key) or {}
                        if isinstance(current_value, dict) and isinstance(value, dict):
                            current_value.update(value)
                            setattr(portfolio, key, current_value)
                        else:
                            setattr(portfolio, key, value)
                    elif hasattr(portfolio, key):
                        setattr(portfolio, key, value)
                portfolio.last_updated = datetime.now()
            else:
                # Create new portfolio
                # Extract known fields
                known_fields = {k: v for k, v in portfolio_data.items() if k in [
                    'user_id', 'name', 'holdings', 'performance', 'settings'
                ]}
                
                # Set last_updated
                known_fields['last_updated'] = datetime.now()
                
                portfolio = UserPortfolio(**known_fields)
                session.add(portfolio)
                
            session.commit()
            portfolio_id = portfolio.id
            session.close()
            
            return portfolio_id
            
        except Exception as e:
            logger.error(f"Error saving user portfolio: {str(e)}")
            if 'session' in locals() and session:
                session.rollback()
                session.close()
            return None
    
    def get_user_portfolio(self, user_id):
        """Get a user's portfolio"""
        if not self.connected:
            logger.warning("Cannot get user portfolio, database not connected")
            return None
            
        try:
            session = self.Session()
            portfolio = session.query(UserPortfolio).filter_by(user_id=user_id).first()
            
            if not portfolio:
                session.close()
                return None
                
            # Convert to dictionary
            portfolio_dict = {
                'id': portfolio.id,
                'user_id': portfolio.user_id,
                'name': portfolio.name,
                'holdings': portfolio.holdings,
                'performance': portfolio.performance,
                'settings': portfolio.settings,
                'last_updated': portfolio.last_updated.isoformat() if portfolio.last_updated else None
            }
                
            session.close()
            return portfolio_dict
            
        except Exception as e:
            logger.error(f"Error getting user portfolio: {str(e)}")
            if 'session' in locals() and session:
                session.close()
            return None
    
    def close(self):
        """Close the database connection"""
        if hasattr(self, 'engine') and self.engine:
            self.engine.dispose()
        if hasattr(self, 'Session'):
            self.Session.remove()
        self.connected = False
        logger.info("Database connection closed")


# Initialize global instance
db = Database()