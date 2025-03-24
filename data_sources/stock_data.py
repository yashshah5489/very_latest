"""
Stock Data Module for Indian Financial Analyzer
"""
import requests
import json
import logging
from datetime import datetime, timedelta
import pandas as pd
import config

logger = logging.getLogger(__name__)

class IndianStockData:
    """Class for retrieving Indian stock market data"""
    
    def __init__(self):
        """Initialize the stock data retriever"""
        # Define common Indian market indices
        self.indices = {
            "NIFTY50": "^NSEI",
            "SENSEX": "^BSESN", 
            "NIFTYBANK": "^NSEBANK",
            "NIFTYMIDCAP": "NIFTY_MIDCAP_50.NS"
        }
    
    def get_stock_price(self, symbol, days=30):
        """
        Get historical stock prices for an Indian stock
        
        Args:
            symbol (str): Stock symbol (use .NS suffix for NSE, .BO for BSE)
            days (int): Number of days to retrieve
            
        Returns:
            dict: Historical price data
        """
        # Add .NS suffix if not present and not an index
        if not (symbol.endswith('.NS') or symbol.endswith('.BO') or symbol.startswith('^')):
            symbol = f"{symbol}.NS"  # Default to NSE
            
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Format dates for API
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # Use Yahoo Finance API (via rapidapi or direct)
        try:
            # This is a simplified version using direct HTTP requests
            # In production, use a proper API service with your API key
            
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                "period1": int(start_date.timestamp()),
                "period2": int(end_date.timestamp()),
                "interval": "1d"
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0"  # Simple user agent to avoid blocking
            }
            
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Process and format the data
            return self._process_price_data(data, symbol)
        
        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {str(e)}")
            return {"error": str(e), "data": []}
    
    def _process_price_data(self, raw_data, symbol):
        """Process and format raw price data from Yahoo Finance"""
        try:
            result = {"symbol": symbol, "data": []}
            
            # Extract chart data
            chart = raw_data.get("chart", {})
            result_set = chart.get("result", [])
            
            if not result_set:
                return result
                
            # Get the first result
            data_set = result_set[0]
            
            # Extract timestamps, open, high, low, close, volume
            timestamps = data_set.get("timestamp", [])
            quote = data_set.get("indicators", {}).get("quote", [{}])[0]
            
            opens = quote.get("open", [])
            highs = quote.get("high", [])
            lows = quote.get("low", [])
            closes = quote.get("close", [])
            volumes = quote.get("volume", [])
            
            # Format data points
            for i in range(len(timestamps)):
                if i < len(closes) and closes[i] is not None:
                    data_point = {
                        "date": datetime.fromtimestamp(timestamps[i]).strftime('%Y-%m-%d'),
                        "open": opens[i] if i < len(opens) and opens[i] is not None else None,
                        "high": highs[i] if i < len(highs) and highs[i] is not None else None,
                        "low": lows[i] if i < len(lows) and lows[i] is not None else None,
                        "close": closes[i],
                        "volume": volumes[i] if i < len(volumes) and volumes[i] is not None else 0
                    }
                    result["data"].append(data_point)
            
            # Add company name if available
            meta = data_set.get("meta", {})
            result["name"] = meta.get("symbol", symbol)
            
            # Calculate summary metrics
            if result["data"]:
                latest = result["data"][-1]
                earliest = result["data"][0]
                result["latest_price"] = latest["close"]
                result["change"] = latest["close"] - earliest["close"]
                result["change_percent"] = (result["change"] / earliest["close"]) * 100
            
            return result
        
        except Exception as e:
            logger.error(f"Error processing price data: {str(e)}")
            return {"symbol": symbol, "error": str(e), "data": []}
    
    def get_company_info(self, symbol):
        """
        Get basic company information for an Indian stock
        
        Args:
            symbol (str): Stock symbol (use .NS suffix for NSE, .BO for BSE)
            
        Returns:
            dict: Company information
        """
        # Add .NS suffix if not present and not an index
        if not (symbol.endswith('.NS') or symbol.endswith('.BO') or symbol.startswith('^')):
            symbol = f"{symbol}.NS"  # Default to NSE
            
        try:
            url = f"https://query1.finance.yahoo.com/v7/finance/options/{symbol}"
            headers = {"User-Agent": "Mozilla/5.0"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Extract company information
            result = {
                "symbol": symbol,
                "name": "",
                "exchange": "",
                "sector": "",
                "industry": "",
                "current_price": 0,
                "market_cap": 0,
                "pe_ratio": 0,
                "dividend_yield": 0
            }
            
            option_chain = data.get("optionChain", {})
            result_set = option_chain.get("result", [])
            
            if result_set:
                quote = result_set[0].get("quote", {})
                result["name"] = quote.get("longName", quote.get("shortName", symbol))
                result["exchange"] = quote.get("exchange", "")
                result["current_price"] = quote.get("regularMarketPrice", 0)
                result["market_cap"] = quote.get("marketCap", 0)
                result["pe_ratio"] = quote.get("trailingPE", 0)
                result["dividend_yield"] = quote.get("dividendYield", 0)
                
                # Get more details about the company
                url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}?modules=assetProfile"
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    profile_data = response.json()
                    asset_profile = profile_data.get("quoteSummary", {}).get("result", [{}])[0].get("assetProfile", {})
                    result["sector"] = asset_profile.get("sector", "")
                    result["industry"] = asset_profile.get("industry", "")
                    result["summary"] = asset_profile.get("longBusinessSummary", "")
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching company info for {symbol}: {str(e)}")
            return {"symbol": symbol, "error": str(e)}
    
    def get_market_overview(self):
        """
        Get an overview of Indian market indices
        
        Returns:
            dict: Market overview data with key indices
        """
        result = {
            "indices": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Get data for each index
        for index_name, index_symbol in self.indices.items():
            try:
                index_data = self.get_stock_price(index_symbol, days=2)
                if index_data and "data" in index_data and index_data["data"]:
                    latest = index_data["data"][-1]
                    previous = index_data["data"][0] if len(index_data["data"]) > 1 else latest
                    
                    index_info = {
                        "name": index_name,
                        "symbol": index_symbol,
                        "value": latest["close"],
                        "change": latest["close"] - previous["close"],
                        "change_percent": ((latest["close"] - previous["close"]) / previous["close"]) * 100
                    }
                    result["indices"].append(index_info)
                    
            except Exception as e:
                logger.error(f"Error getting data for {index_name}: {str(e)}")
        
        return result
    
    def get_sector_performance(self, sectors=None):
        """
        Get performance data for Indian market sectors
        
        Args:
            sectors (list): List of sectors to include, or None for all
            
        Returns:
            dict: Sector performance data
        """
        # Default sectors to track in Indian market
        default_sectors = [
            {"name": "Information Technology", "symbol": "NIFTYIT.NS"},
            {"name": "Banking", "symbol": "^NSEBANK"},
            {"name": "Financial Services", "symbol": "NIFTY_FIN_SERVICE.NS"},
            {"name": "FMCG", "symbol": "NIFTY_FMCG.NS"},
            {"name": "Pharma", "symbol": "NIFTY_PHARMA.NS"},
            {"name": "Auto", "symbol": "NIFTY_AUTO.NS"}
        ]
        
        sectors_to_track = sectors or default_sectors
        
        result = {
            "sectors": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Get data for each sector
        for sector in sectors_to_track:
            try:
                sector_data = self.get_stock_price(sector["symbol"], days=30)
                if sector_data and "data" in sector_data and sector_data["data"]:
                    latest = sector_data["data"][-1]
                    month_ago = sector_data["data"][0] if len(sector_data["data"]) > 1 else latest
                    
                    sector_info = {
                        "name": sector["name"],
                        "symbol": sector["symbol"],
                        "current_value": latest["close"],
                        "monthly_change": latest["close"] - month_ago["close"],
                        "monthly_change_percent": ((latest["close"] - month_ago["close"]) / month_ago["close"]) * 100
                    }
                    result["sectors"].append(sector_info)
                    
            except Exception as e:
                logger.error(f"Error getting data for sector {sector['name']}: {str(e)}")
        
        return result

# Create stock data instance
stock_data = IndianStockData()