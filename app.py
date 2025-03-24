from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
import sys
import json
import markdown
import logging
import traceback
from datetime import datetime, timedelta
from pathlib import Path
import config
from database import db
from data_sources.news_extractor import news_extractor
from data_sources.stock_data import stock_data
from ai.groq_client import GroqClient
groq_client = GroqClient()
from ai.rag_system import rag_system
from ai.financial_agent import financial_agent

# Set up Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize database connection
try:
    db.connect()
    logger.info("Connected to MongoDB successfully")
except Exception as e:
    logger.warning(f"Could not connect to MongoDB: {str(e)}")

# Main routes
@app.route('/')
def index():
    """Render the main dashboard page."""
    try:
        # Get market overview data
        market_data = stock_data.get_market_overview()
        
        # Get recent news
        news_data = news_extractor.get_market_news(market="Indian", limit=5)
        
        return render_template('report_template.html', 
                              market_data=market_data,
                              news_data=news_data)
    except Exception as e:
        logger.error(f"Error rendering index: {str(e)}")
        return render_template('report_template.html', error=str(e))

# API endpoints for market data
@app.route('/api/market/overview')
def market_overview():
    """Get market overview data."""
    try:
        data = stock_data.get_market_overview()
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        logger.error(f"Error getting market overview: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/market/sectors')
def market_sectors():
    """Get sector performance data."""
    try:
        data = stock_data.get_sector_performance()
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        logger.error(f"Error getting sector performance: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# API endpoints for stock data
@app.route('/api/stock/<symbol>')
def get_stock(symbol):
    """Get data for a specific stock."""
    try:
        price_data = stock_data.get_stock_price(symbol)
        company_info = stock_data.get_company_info(symbol)
        
        # Store in database if available
        if db.connected and price_data and company_info:
            combined_data = {
                "symbol": symbol,
                "name": company_info.get("name", ""),
                "current_price": company_info.get("current_price", 0),
                "sector": company_info.get("sector", ""),
                "industry": company_info.get("industry", ""),
                "last_updated": datetime.now()
            }
            db.add_indian_stock(combined_data)
        
        return jsonify({
            "status": "success", 
            "price_data": price_data,
            "company_info": company_info
        })
    except Exception as e:
        logger.error(f"Error getting stock data for {symbol}: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/stock/search')
def search_stocks():
    """Search for stocks in the database."""
    try:
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 10))
        
        if not query:
            return jsonify({"status": "error", "message": "Search query is required"}), 400
        
        # Search in database
        filter_query = {"$or": [
            {"symbol": {"$regex": query, "$options": "i"}},
            {"name": {"$regex": query, "$options": "i"}}
        ]}
        
        results = db.get_indian_stocks(filter_query, limit) if db.connected else []
        
        return jsonify({"status": "success", "results": results})
    except Exception as e:
        logger.error(f"Error searching stocks: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# API endpoints for news
@app.route('/api/news')
def get_news():
    """Get financial news."""
    try:
        category = request.args.get('category', 'market')
        query = request.args.get('query', '')
        limit = int(request.args.get('limit', 10))
        
        if category == 'market':
            news_data = news_extractor.get_market_news(market="Indian", limit=limit)
        elif category == 'stock' and query:
            news_data = news_extractor.get_stock_news(symbol=query, limit=limit)
        elif category == 'sector' and query:
            news_data = news_extractor.get_sector_news(sector=query, limit=limit)
        elif category == 'economic':
            news_data = news_extractor.get_economic_indicators(limit=limit)
        else:
            news_data = news_extractor.search_financial_news(query=query or "Indian stock market", max_results=limit)
        
        # Store news articles in database if available
        if db.connected and news_data.get("articles"):
            for article in news_data["articles"]:
                db.add_news_article(article)
        
        return jsonify({"status": "success", "data": news_data})
    except Exception as e:
        logger.error(f"Error getting news: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# API endpoints for AI analysis
@app.route('/api/analyze/market')
def analyze_market():
    """Generate market analysis using the financial agent."""
    try:
        analysis = financial_agent.market_summary()
        
        # Store analysis in database if available
        if db.connected:
            analysis_data = {
                "analysis_type": "market_summary",
                "content": analysis,
                "timestamp": datetime.now(),
                "user_id": session.get("user_id")
            }
            db.save_analysis_result(analysis_data)
        
        return jsonify({"status": "success", "data": analysis})
    except Exception as e:
        logger.error(f"Error analyzing market: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/analyze/stock', methods=['POST'])
def analyze_stock():
    """Generate stock analysis using the financial agent."""
    try:
        data = request.get_json()
        if not data or 'symbol' not in data:
            return jsonify({"status": "error", "message": "Symbol is required"}), 400
        
        symbol = data['symbol']
        company_name = data.get('company_name')
        
        analysis = financial_agent.stock_analysis(symbol, company_name)
        
        # Store analysis in database if available
        if db.connected:
            analysis_data = {
                "analysis_type": "stock_analysis",
                "symbol": symbol,
                "content": analysis,
                "timestamp": datetime.now(),
                "user_id": session.get("user_id")
            }
            db.save_analysis_result(analysis_data)
        
        return jsonify({"status": "success", "data": analysis})
    except Exception as e:
        logger.error(f"Error analyzing stock: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/advice', methods=['POST'])
def get_investment_advice():
    """Generate personalized investment advice."""
    try:
        data = request.get_json()
        if not data or 'profile' not in data:
            return jsonify({"status": "error", "message": "Investment profile is required"}), 400
        
        profile = data['profile']
        advice = financial_agent.generate_investment_advice(profile)
        
        # Store analysis in database if available
        if db.connected:
            analysis_data = {
                "analysis_type": "investment_advice",
                "content": advice,
                "timestamp": datetime.now(),
                "user_id": session.get("user_id")
            }
            db.save_analysis_result(analysis_data)
        
        return jsonify({"status": "success", "data": advice})
    except Exception as e:
        logger.error(f"Error generating investment advice: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# API endpoints for financial books RAG
@app.route('/api/books')
def get_books():
    """Get available financial books."""
    try:
        books = rag_system.get_available_books()
        return jsonify({"status": "success", "data": books})
    except Exception as e:
        logger.error(f"Error getting books: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/books/<book_id>/summary')
def get_book_summary(book_id):
    """Get summary of a financial book."""
    try:
        summary = rag_system.get_book_summary(book_id)
        return jsonify({"status": "success", "data": summary})
    except Exception as e:
        logger.error(f"Error getting book summary: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/books/insights', methods=['POST'])
def get_book_insights():
    """Get insights from financial books based on a query."""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"status": "error", "message": "Query is required"}), 400
        
        query = data['query']
        book_id = data.get('book_id')  # Optional
        
        insights = rag_system.generate_book_insight(query, book_id)
        
        return jsonify({"status": "success", "data": insights})
    except Exception as e:
        logger.error(f"Error getting book insights: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/answer', methods=['POST'])
def answer_question():
    """Answer a financial question using the financial agent."""
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({"status": "error", "message": "Question is required"}), 400
        
        question = data['question']
        answer = financial_agent.answer_financial_question(question)
        
        return jsonify({"status": "success", "data": answer})
    except Exception as e:
        logger.error(f"Error answering question: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# API endpoints for portfolio management
@app.route('/api/portfolio', methods=['GET', 'POST'])
def manage_portfolio():
    """Get or update user portfolio."""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"status": "error", "message": "User not authenticated"}), 401
        
        if request.method == 'GET':
            portfolio = db.get_user_portfolio(user_id) if db.connected else None
            return jsonify({"status": "success", "data": portfolio})
        else:  # POST
            data = request.get_json()
            if not data:
                return jsonify({"status": "error", "message": "Portfolio data is required"}), 400
            
            data["user_id"] = user_id
            result = db.save_user_portfolio(data) if db.connected else None
            
            return jsonify({"status": "success", "message": "Portfolio updated", "id": result})
    except Exception as e:
        logger.error(f"Error managing portfolio: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/portfolio/analyze', methods=['POST'])
def analyze_portfolio():
    """Analyze user portfolio."""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"status": "error", "message": "User not authenticated"}), 401
        
        # Get portfolio from request or database
        data = request.get_json()
        if data and 'portfolio' in data:
            portfolio = data['portfolio']
        elif db.connected:
            portfolio_data = db.get_user_portfolio(user_id)
            portfolio = portfolio_data.get('holdings', []) if portfolio_data else []
        else:
            return jsonify({"status": "error", "message": "Portfolio data is required"}), 400
        
        # Generate portfolio analysis report
        report = financial_agent.generate_financial_report("portfolio_analysis", {"portfolio": portfolio})
        
        return jsonify({"status": "success", "data": report})
    except Exception as e:
        logger.error(f"Error analyzing portfolio: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"status": "error", "message": "Resource not found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"status": "error", "message": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
