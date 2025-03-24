"""
Indian Stock Market Data Provider using Yahoo Finance
"""
import os
import json
import logging
import requests
import random
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from utils.cache_manager import CacheManager

logger = logging.getLogger(__name__)

class StockData:
    """Provider for Indian stock market data using Yahoo Finance"""
    
    def __init__(self):
        """Initialize the stock data provider."""
        # For Indian stocks, we need to append .NS for NSE stocks
        self.default_exchange = ".NS"
        
        # Initialize cache manager for Yahoo Finance API calls
        self.cache = CacheManager(cache_dir="data/cache", enabled=True)
        
        # Headers to mimic a browser request
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br"
        }
        
        # Major Indian market indices with their Yahoo Finance symbols
        self.market_indices = {
            "NIFTY 50": "^NSEI",
            "BSE SENSEX": "^BSESN",
            "NIFTY BANK": "^NSEBANK",
            "NIFTY IT": "^CNXIT",
            "NIFTY PHARMA": "^CNXPHARMA",
            "NIFTY AUTO": "^CNXAUTO"
        }
        
    def get_market_overview(self) -> Dict[str, Any]:
        """
        Get an overview of the Indian market with major indices using Yahoo Finance.
        
        Returns:
            Dictionary with market data
        """
        try:
            # Check if we have a cached response
            cache_key = f"market_overview_{datetime.now().strftime('%Y-%m-%d_%H')}"
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return cached_data
            
            # Get data for major Indian indices
            indices_data = []
            total_volume = 0
            
            for name, symbol in self.market_indices.items():
                # Get the index data from Yahoo Finance
                index = yf.Ticker(symbol)
                
                # Get the current data
                current_data = index.history(period="2d")
                
                if len(current_data) < 2:
                    logger.warning(f"Insufficient historical data for {name} ({symbol})")
                    continue
                
                # Get the last full trading day data
                current = current_data.iloc[-1]
                prev = current_data.iloc[-2]
                
                # Calculate changes
                value = current['Close']
                prev_close = prev['Close']
                change = value - prev_close
                change_percent = (change / prev_close) * 100
                
                index_data = {
                    "name": name,
                    "value": round(value, 2),
                    "change": round(change, 2),
                    "change_percent": round(change_percent, 2),
                    "high": round(current['High'], 2),
                    "low": round(current['Low'], 2),
                    "volume": int(current['Volume']) if not pd.isna(current['Volume']) else 0,
                    "symbol": symbol
                }
                
                indices_data.append(index_data)
                total_volume += index_data["volume"]
            
            # For advances/declines, we would need additional data sources
            # Since these aren't readily available from Yahoo Finance, we'll estimate
            # based on the indices' performance
            positive_indices = sum(1 for idx in indices_data if idx["change"] > 0)
            negative_indices = sum(1 for idx in indices_data if idx["change"] < 0)
            
            # Approximate market breadth based on our limited data
            # In a production system, you'd use specific market breadth APIs
            result = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "indices": indices_data,
                "advances": int(1000 * (positive_indices / len(indices_data))) if indices_data else 0,
                "declines": int(1000 * (negative_indices / len(indices_data))) if indices_data else 0,
                "unchanged": int(1000 * ((len(indices_data) - positive_indices - negative_indices) / len(indices_data))) if indices_data else 0,
                "total_volume": total_volume
            }
            
            # Cache the results for one hour
            self.cache.set(cache_key, result, ttl=3600)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting market overview: {str(e)}")
            return {"error": str(e)}
            
    def get_sector_performance(self) -> Dict[str, Any]:
        """
        Get performance data for market sectors.
        
        Returns:
            Dictionary with sector performance data
        """
        try:
            # In a production system, we would make API calls to NSE/BSE APIs
            # For demo purposes, we'll generate sample data
            
            # List of Indian market sectors
            sectors = [
                "IT", "Banking", "Financial Services", "FMCG", "Pharma", 
                "Auto", "Metal", "Energy", "Reality", "Media"
            ]
            
            # Generate random performance for each sector
            sector_data = []
            for sector in sectors:
                change = random.uniform(-3, 3)
                value = random.uniform(10000, 20000)
                
                sector_data.append({
                    "name": sector,
                    "value": value,
                    "change": change,
                    "change_percent": change  # In a real implementation, would calculate properly
                })
            
            # Sort by change (descending) to show best/worst performing
            sector_data.sort(key=lambda x: x["change"], reverse=True)
            
            return {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "sectors": sector_data,
                "top_sector": sector_data[0]["name"],
                "bottom_sector": sector_data[-1]["name"]
            }
            
        except Exception as e:
            logger.error(f"Error getting sector performance: {str(e)}")
            return {"error": str(e)}
            
    def get_stock_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get current price data for a stock.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with stock price data
        """
        try:
            # Normalize symbol (remove NSE/BSE suffixes if present)
            symbol = symbol.split('.')[0].strip().upper()
            
            # In a production system, we would make API calls to NSE/BSE APIs
            # For demo purposes, we'll generate sample data
            
            # Generate random price data
            price = random.uniform(500, 2000)
            prev_close = price - random.uniform(-50, 50)
            change = price - prev_close
            change_percent = (change / prev_close) * 100
            
            volume = random.randint(100000, 1000000)
            avg_volume = volume * random.uniform(0.8, 1.2)
            
            # Performance for different time periods
            performance = {
                "1d": change_percent,
                "1w": random.uniform(-5, 5),
                "1m": random.uniform(-10, 10),
                "3m": random.uniform(-15, 15),
                "6m": random.uniform(-20, 20),
                "1y": random.uniform(-30, 30)
            }
            
            return {
                "symbol": symbol,
                "price": price,
                "prev_close": prev_close,
                "open": prev_close + random.uniform(-10, 10),
                "high": price + random.uniform(1, 10),
                "low": price - random.uniform(1, 10),
                "change": change,
                "change_percent": change_percent,
                "volume": volume,
                "avg_volume": avg_volume,
                "performance": performance,
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            
        except Exception as e:
            logger.error(f"Error getting stock price for {symbol}: {str(e)}")
            return {"error": str(e)}
            
    def get_company_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get information about a company.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with company information
        """
        try:
            # Normalize symbol (remove NSE/BSE suffixes if present)
            symbol = symbol.split('.')[0].strip().upper()
            
            # In a production system, we would make API calls to NSE/BSE APIs or other data providers
            # For demo purposes, we'll generate sample data
            
            # Use a simple mapping for a few sample stocks
            companies = {
                "TCS": {
                    "name": "Tata Consultancy Services Ltd.",
                    "sector": "IT",
                    "industry": "Software",
                    "description": "Tata Consultancy Services is an Indian multinational information technology services and consulting company.",
                    "founded": 1968,
                    "employees": 614000,
                    "headquarters": "Mumbai, India"
                },
                "RELIANCE": {
                    "name": "Reliance Industries Ltd.",
                    "sector": "Energy",
                    "industry": "Oil & Gas",
                    "description": "Reliance Industries Limited is an Indian multinational conglomerate company, with businesses across energy, petrochemicals, natural gas, retail, telecommunications, mass media, and textiles.",
                    "founded": 1973,
                    "employees": 195000,
                    "headquarters": "Mumbai, India"
                },
                "HDFCBANK": {
                    "name": "HDFC Bank Ltd.",
                    "sector": "Banking",
                    "industry": "Private Banking",
                    "description": "HDFC Bank Limited is an Indian banking and financial services company headquartered in Mumbai.",
                    "founded": 1994,
                    "employees": 134000,
                    "headquarters": "Mumbai, India"
                },
                "INFY": {
                    "name": "Infosys Ltd.",
                    "sector": "IT",
                    "industry": "Software",
                    "description": "Infosys is an Indian multinational information technology company that provides business consulting, information technology and outsourcing services.",
                    "founded": 1981,
                    "employees": 335000,
                    "headquarters": "Bengaluru, India"
                },
                "HCLTECH": {
                    "name": "HCL Technologies Ltd.",
                    "sector": "IT",
                    "industry": "Software",
                    "description": "HCL Technologies Limited is an Indian multinational information technology services and consulting company.",
                    "founded": 1991,
                    "employees": 211000,
                    "headquarters": "Noida, India"
                }
            }
            
            # Get company info, or generate random data if not in our sample
            company = companies.get(symbol, {
                "name": f"{symbol} Corporation Ltd.",
                "sector": random.choice(["IT", "Banking", "Financial Services", "FMCG", "Pharma", "Auto", "Metal", "Energy"]),
                "industry": random.choice(["Software", "Hardware", "Banking", "Insurance", "Auto Components", "Pharmaceuticals"]),
                "description": f"{symbol} is a leading Indian company in its sector.",
                "founded": random.randint(1970, 2010),
                "employees": random.randint(1000, 200000),
                "headquarters": random.choice(["Mumbai", "Bengaluru", "Delhi", "Hyderabad", "Chennai"]) + ", India"
            })
            
            # Add financial data
            price = random.uniform(500, 2000)
            company.update({
                "symbol": symbol,
                "current_price": price,
                "market_cap": price * random.randint(100000000, 10000000000),
                "pe_ratio": random.uniform(10, 40),
                "eps": random.uniform(10, 100),
                "book_value": random.uniform(100, 1000),
                "dividend_yield": random.uniform(0.01, 0.05),
                "52w_high": price * random.uniform(1.05, 1.2),
                "52w_low": price * random.uniform(0.8, 0.95),
                "avg_volume": random.randint(100000, 1000000)
            })
            
            return company
            
        except Exception as e:
            logger.error(f"Error getting company info for {symbol}: {str(e)}")
            return {"error": str(e)}
            
    def search_stocks(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for stocks by name or symbol.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            
        Returns:
            List of matching stocks
        """
        try:
            # In a production system, we would search a database or make API calls
            # For demo purposes, we'll use a sample list of top Indian stocks
            
            stocks = [
                {"symbol": "TCS", "name": "Tata Consultancy Services Ltd.", "sector": "IT"},
                {"symbol": "RELIANCE", "name": "Reliance Industries Ltd.", "sector": "Energy"},
                {"symbol": "HDFCBANK", "name": "HDFC Bank Ltd.", "sector": "Banking"},
                {"symbol": "INFY", "name": "Infosys Ltd.", "sector": "IT"},
                {"symbol": "HINDUNILVR", "name": "Hindustan Unilever Ltd.", "sector": "FMCG"},
                {"symbol": "ICICIBANK", "name": "ICICI Bank Ltd.", "sector": "Banking"},
                {"symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank Ltd.", "sector": "Banking"},
                {"symbol": "HDFC", "name": "Housing Development Finance Corporation Ltd.", "sector": "Financial Services"},
                {"symbol": "ITC", "name": "ITC Ltd.", "sector": "FMCG"},
                {"symbol": "LT", "name": "Larsen & Toubro Ltd.", "sector": "Construction"},
                {"symbol": "SBIN", "name": "State Bank of India", "sector": "Banking"},
                {"symbol": "BAJFINANCE", "name": "Bajaj Finance Ltd.", "sector": "Financial Services"},
                {"symbol": "BHARTIARTL", "name": "Bharti Airtel Ltd.", "sector": "Telecom"},
                {"symbol": "ASIANPAINT", "name": "Asian Paints Ltd.", "sector": "Consumer Durables"},
                {"symbol": "MARUTI", "name": "Maruti Suzuki India Ltd.", "sector": "Auto"},
                {"symbol": "HCLTECH", "name": "HCL Technologies Ltd.", "sector": "IT"},
                {"symbol": "AXISBANK", "name": "Axis Bank Ltd.", "sector": "Banking"},
                {"symbol": "WIPRO", "name": "Wipro Ltd.", "sector": "IT"},
                {"symbol": "SUNPHARMA", "name": "Sun Pharmaceutical Industries Ltd.", "sector": "Pharma"},
                {"symbol": "TATASTEEL", "name": "Tata Steel Ltd.", "sector": "Metal"}
            ]
            
            # Filter stocks based on query
            query = query.lower()
            results = [stock for stock in stocks if 
                      query in stock["symbol"].lower() or 
                      query in stock["name"].lower() or
                      query in stock["sector"].lower()]
            
            # Add some random price data
            for stock in results:
                stock["current_price"] = random.uniform(500, 2000)
                stock["change_percent"] = random.uniform(-3, 3)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching stocks: {str(e)}")
            return []
            
    def get_historical_data(self, symbol: str, period: str = "1y", interval: str = "1d") -> Dict[str, Any]:
        """
        Get historical price data for a stock.
        
        Args:
            symbol: Stock symbol
            period: Time period (1d, 1w, 1m, 3m, 6m, 1y, 5y)
            interval: Data interval (1m, 5m, 15m, 30m, 1h, 1d, 1w, 1mo)
            
        Returns:
            Dictionary with historical price data
        """
        try:
            # Generate random historical data
            end_date = datetime.now()
            
            # Determine start date based on period
            if period == "1d":
                start_date = end_date - timedelta(days=1)
                data_points = 390  # Stock market open minutes in a day
            elif period == "1w":
                start_date = end_date - timedelta(weeks=1)
                data_points = 5  # 5 trading days
            elif period == "1m":
                start_date = end_date - timedelta(days=30)
                data_points = 22  # ~22 trading days in a month
            elif period == "3m":
                start_date = end_date - timedelta(days=90)
                data_points = 66  # ~66 trading days in 3 months
            elif period == "6m":
                start_date = end_date - timedelta(days=180)
                data_points = 132  # ~132 trading days in 6 months
            elif period == "1y":
                start_date = end_date - timedelta(days=365)
                data_points = 252  # ~252 trading days in a year
            elif period == "5y":
                start_date = end_date - timedelta(days=365 * 5)
                data_points = 252 * 5  # ~1260 trading days in 5 years
            else:
                start_date = end_date - timedelta(days=30)
                data_points = 22
            
            # Generate starting price and trend
            price = random.uniform(500, 2000)
            trend = random.uniform(-0.0001, 0.0002)  # Daily percentage change trend
            volatility = random.uniform(0.005, 0.02)  # Daily volatility
            
            # Generate data points
            data = []
            current_price = price
            current_date = start_date
            
            for i in range(data_points):
                if current_date.weekday() < 5:  # Only generate for weekdays
                    daily_change = current_price * (trend + random.normalvariate(0, volatility))
                    current_price += daily_change
                    
                    # Generate OHLC data
                    open_price = current_price - daily_change
                    close_price = current_price
                    high_price = max(open_price, close_price) + abs(daily_change) * random.uniform(0.2, 0.5)
                    low_price = min(open_price, close_price) - abs(daily_change) * random.uniform(0.2, 0.5)
                    volume = random.randint(100000, 1000000)
                    
                    data.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "open": open_price,
                        "high": high_price,
                        "low": low_price,
                        "close": close_price,
                        "volume": volume
                    })
                
                # Move to next data point
                if interval == "1d":
                    current_date += timedelta(days=1)
                elif interval == "1w":
                    current_date += timedelta(weeks=1)
                elif interval == "1mo":
                    current_date += timedelta(days=30)
                else:
                    # For intraday intervals, just add data points within the day
                    minutes_to_add = {
                        "1m": 1,
                        "5m": 5,
                        "15m": 15,
                        "30m": 30,
                        "1h": 60
                    }.get(interval, 1)
                    
                    current_date += timedelta(minutes=minutes_to_add)
            
            return {
                "symbol": symbol,
                "period": period,
                "interval": interval,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "data": data
            }
            
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {str(e)}")
            return {"error": str(e)}


# Initialize global instance
stock_data = StockData()