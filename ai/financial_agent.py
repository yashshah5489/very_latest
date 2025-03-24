"""
Financial Agent Module for Indian Financial Analyzer
"""
import logging
from datetime import datetime
import json
from ai.groq_client import groq_client
from ai.rag_system import rag_system
from data_sources.news_extractor import news_extractor
from data_sources.stock_data import stock_data
import config

logger = logging.getLogger(__name__)

class FinancialAgent:
    """
    Agent for financial analysis tasks using LLM capabilities
    """
    
    def __init__(self, user_id=None):
        """
        Initialize the financial agent
        
        Args:
            user_id (str): ID of the user this agent is serving
        """
        self.user_id = user_id
        self.context = {
            "market": config.DEFAULT_INDEX,
            "timestamp": datetime.now().isoformat()
        }
    
    def market_summary(self):
        """
        Generate a market summary for Indian markets
        
        Returns:
            dict: Market summary and insights
        """
        # Get market data
        market_data = stock_data.get_market_overview()
        sectors_data = stock_data.get_sector_performance()
        
        # Format data for the LLM
        market_context = "Current Indian Market Indices:\n"
        for index in market_data.get("indices", []):
            change_sign = "+" if index.get("change", 0) >= 0 else ""
            market_context += f"- {index.get('name', '')}: {index.get('value', 0):.2f} ({change_sign}{index.get('change_percent', 0):.2f}%)\n"
        
        market_context += "\nSector Performance (30 days):\n"
        for sector in sectors_data.get("sectors", []):
            change_sign = "+" if sector.get("monthly_change", 0) >= 0 else ""
            market_context += f"- {sector.get('name', '')}: {change_sign}{sector.get('monthly_change_percent', 0):.2f}%\n"
        
        # Get recent news headlines
        news_data = news_extractor.get_market_news(market="Indian", limit=5)
        
        news_context = "Recent Market News:\n"
        for article in news_data.get("articles", []):
            news_context += f"- {article.get('title', '')}\n"
        
        # Combine data for LLM context
        prompt = f"""You are a financial analyst specializing in the Indian market. Provide a comprehensive market summary based on the following data.

{market_context}

{news_context}

In your summary:
1. Analyze the current market trends and sector performances
2. Highlight potential factors influencing market movements
3. Indicate which sectors show strength or weakness
4. Provide a short-term outlook (1-2 weeks) based on technical indicators and news sentiment
5. Mention any upcoming events that might impact the Indian market

Keep your analysis focused on the Indian financial market context and relevant to Indian investors.
"""
        
        response = groq_client.generate_response(prompt, temperature=0.2)
        
        return {
            "summary": response.get("text", "Failed to generate market summary"),
            "market_data": market_data,
            "sector_data": sectors_data,
            "timestamp": datetime.now().isoformat()
        }
    
    def stock_analysis(self, symbol, company_name=None):
        """
        Generate analysis for a specific Indian stock
        
        Args:
            symbol (str): Stock symbol
            company_name (str): Company name (optional)
            
        Returns:
            dict: Stock analysis and insights
        """
        # Get stock data
        price_data = stock_data.get_stock_price(symbol, days=90)
        company_info = stock_data.get_company_info(symbol)
        
        # Get stock news
        news_data = news_extractor.get_stock_news(
            symbol=symbol, 
            company_name=company_name or company_info.get("name", ""),
            limit=5
        )
        
        # Format data for the LLM
        company_context = f"""Company: {company_info.get('name', symbol)} ({symbol})
Exchange: {company_info.get('exchange', 'NSE/BSE')}
Sector: {company_info.get('sector', '')}
Industry: {company_info.get('industry', '')}
Current Price: ₹{company_info.get('current_price', 0):.2f}
Market Cap: ₹{company_info.get('market_cap', 0)/10000000:.2f} Cr
P/E Ratio: {company_info.get('pe_ratio', 0):.2f}
Dividend Yield: {company_info.get('dividend_yield', 0)*100:.2f}%

Company Description:
{company_info.get('summary', 'No description available')}
"""
        
        # Format price data
        if price_data.get("data"):
            first_price = price_data["data"][0]["close"]
            last_price = price_data["data"][-1]["close"]
            percent_change = ((last_price - first_price) / first_price) * 100
            change_sign = "+" if percent_change >= 0 else ""
            
            price_context = f"""3-Month Performance: {change_sign}{percent_change:.2f}%
Price Range: ₹{min(p['low'] for p in price_data['data'] if p['low']):.2f} - ₹{max(p['high'] for p in price_data['data'] if p['high']):.2f}
Average Volume: {sum(p['volume'] for p in price_data['data'])/len(price_data['data']):.0f} shares
"""
        else:
            price_context = "Price data not available."
        
        # Format news context
        news_context = "Recent News:\n"
        for article in news_data.get("articles", []):
            news_context += f"- {article.get('title', '')}\n"
        
        # Combine data for LLM context
        prompt = f"""You are a financial analyst specializing in Indian stocks. Provide a comprehensive analysis of this stock based on the following data.

{company_context}

{price_context}

{news_context}

In your analysis:
1. Evaluate the stock's recent performance and volatility
2. Analyze strengths, weaknesses, opportunities, and threats
3. Compare key metrics to industry standards in India
4. Identify potential catalysts or risks specific to this company or sector
5. Provide a balanced investment perspective (short-term and long-term outlook)

Include specific references to Indian market conditions and regulations where relevant.
"""
        
        response = groq_client.generate_response(prompt, temperature=0.3)
        
        return {
            "symbol": symbol,
            "company_name": company_info.get("name", symbol),
            "analysis": response.get("text", "Failed to generate stock analysis"),
            "price_data": price_data,
            "company_info": company_info,
            "timestamp": datetime.now().isoformat()
        }
    
    def investment_advice(self, profile):
        """
        Generate personalized investment advice for Indian investors
        
        Args:
            profile (dict): User investment profile
            
        Returns:
            dict: Personalized investment advice
        """
        # Get market data for context
        market_data = stock_data.get_market_overview()
        sectors_data = stock_data.get_sector_performance()
        
        # Format market context
        market_context = "Current Indian Market Conditions:\n"
        for index in market_data.get("indices", []):
            change_sign = "+" if index.get("change", 0) >= 0 else ""
            market_context += f"- {index.get('name', '')}: {index.get('value', 0):.2f} ({change_sign}{index.get('change_percent', 0):.2f}%)\n"
        
        market_context += "\nSector Performance (30 days):\n"
        for sector in sectors_data.get("sectors", []):
            change_sign = "+" if sector.get("monthly_change", 0) >= 0 else ""
            market_context += f"- {sector.get('name', '')}: {change_sign}{sector.get('monthly_change_percent', 0):.2f}%\n"
        
        # Get financial wisdom from books
        book_insights = rag_system.generate_book_insight(
            f"investment advice for {profile.get('risk_tolerance', 'moderate')} investor with {profile.get('time_horizon', 'long-term')} horizon in India"
        )
        
        # Format profile for LLM
        profile_str = "\n".join([f"{key.replace('_', ' ').title()}: {value}" for key, value in profile.items()])
        
        # Build prompt for the LLM
        prompt = f"""You are a certified financial advisor specializing in Indian markets. Provide personalized investment advice based on the following information.

Investor Profile:
{profile_str}

{market_context}

Financial Book Insights:
{book_insights.get('insight', '')}

Based on this information, provide comprehensive investment advice including:
1. Recommended asset allocation suitable for this investor profile
2. Specific investment suggestions in the Indian market (specific mutual fund categories, ETFs, or sectors)
3. Risk management strategies tailored to the investor's profile
4. Tax-efficient investment approaches considering Indian tax laws
5. Specific references to Indian financial instruments (PPF, ELSS, NPS, etc.) where appropriate
6. A suggested investment plan with timeline and milestones

Ensure all advice is specific to Indian markets, considers Indian regulations, and is tailored to the investor's profile.
"""
        
        response = groq_client.generate_response(prompt, temperature=0.4, max_tokens=1500)
        
        return {
            "profile": profile,
            "advice": response.get("text", "Failed to generate investment advice"),
            "book_insights": book_insights.get("sources", []),
            "timestamp": datetime.now().isoformat()
        }
    
    def answer_financial_question(self, question):
        """
        Answer a financial question with insights from books and market knowledge
        
        Args:
            question (str): Financial question
            
        Returns:
            dict: Answer with sources
        """
        # Get book insights for the question
        book_insights = rag_system.generate_book_insight(question)
        
        # Get current market context
        market_data = stock_data.get_market_overview()
        market_context = "Current Indian Market Indices:\n"
        for index in market_data.get("indices", []):
            change_sign = "+" if index.get("change", 0) >= 0 else ""
            market_context += f"- {index.get('name', '')}: {index.get('value', 0):.2f} ({change_sign}{index.get('change_percent', 0):.2f}%)\n"
        
        # Build prompt for the LLM
        prompt = f"""You are a financial advisor specializing in Indian markets. Answer the following question with insights from financial books and current market knowledge.

Question: {question}

Financial Book Insights:
{book_insights.get('insight', '')}

{market_context}

Provide a comprehensive answer that:
1. Directly addresses the question
2. Incorporates financial wisdom from the books
3. Applies the concepts to the current Indian financial context
4. Is clear and accessible to investors at all levels
5. Provides actionable information where appropriate

Make specific references to Indian financial instruments, regulations, or market conditions where relevant.
"""
        
        response = groq_client.generate_response(prompt, temperature=0.3)
        
        return {
            "question": question,
            "answer": response.get("text", "Failed to generate answer"),
            "book_sources": book_insights.get("sources", []),
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_financial_report(self, report_type, parameters=None):
        """
        Generate a financial report based on the specified type and parameters
        
        Args:
            report_type (str): Type of report to generate
            parameters (dict): Parameters for the report
            
        Returns:
            dict: Generated report content
        """
        parameters = parameters or {}
        report_content = ""
        
        if report_type == "market_outlook":
            # Generate market outlook report
            market_data = stock_data.get_market_overview()
            sectors_data = stock_data.get_sector_performance()
            news_data = news_extractor.get_market_news(market="Indian", limit=8)
            
            # Build context for LLM
            market_context = self._format_market_data(market_data, sectors_data)
            news_context = self._format_news_data(news_data)
            
            # Build prompt for the LLM
            prompt = f"""You are a senior financial analyst specializing in Indian markets. Generate a comprehensive market outlook report using the following data.

{market_context}

{news_context}

Create a well-structured market outlook report with the following sections:
1. Executive Summary - A concise overview of current market conditions
2. Macroeconomic Factors - Analysis of key economic indicators affecting the Indian market
3. Equity Market Analysis - Detailed analysis of major indices and sector performance
4. Sector Outlook - Prospects for key sectors in the Indian economy
5. Investment Recommendations - Suggested investment strategies based on the outlook
6. Risk Factors - Potential risks that could impact the Indian market

Format the report with clear section headings and well-organized content. Include specific data points from the provided information to support your analysis.
"""
            
            response = groq_client.generate_response(prompt, temperature=0.3, max_tokens=2000)
            report_content = response.get("text", "Failed to generate market outlook report")
            
        elif report_type == "portfolio_analysis":
            # Generate portfolio analysis report
            portfolio = parameters.get("portfolio", [])
            
            if not portfolio:
                return {"error": "Portfolio data is required for portfolio analysis report"}
            
            # Get data for each holding
            holdings_data = []
            total_value = 0
            
            for holding in portfolio:
                symbol = holding.get("symbol")
                quantity = holding.get("quantity", 0)
                
                if not symbol or not quantity:
                    continue
                    
                price_data = stock_data.get_stock_price(symbol, days=30)
                company_info = stock_data.get_company_info(symbol)
                
                if price_data.get("data"):
                    current_price = price_data["data"][-1]["close"]
                    value = current_price * quantity
                    total_value += value
                    
                    holdings_data.append({
                        "symbol": symbol,
                        "name": company_info.get("name", symbol),
                        "quantity": quantity,
                        "current_price": current_price,
                        "value": value,
                        "sector": company_info.get("sector", "Unknown")
                    })
            
            # Calculate allocations
            for holding in holdings_data:
                holding["allocation"] = (holding["value"] / total_value) * 100 if total_value > 0 else 0
            
            # Format portfolio data for LLM
            portfolio_context = f"Portfolio Value: ₹{total_value:.2f}\n\nHoldings:\n"
            
            for holding in holdings_data:
                portfolio_context += f"- {holding['name']} ({holding['symbol']}): {holding['quantity']} shares, ₹{holding['value']:.2f} ({holding['allocation']:.2f}%), Sector: {holding['sector']}\n"
            
            # Group by sector for sector allocation
            sectors = {}
            for holding in holdings_data:
                sector = holding["sector"]
                if sector not in sectors:
                    sectors[sector] = 0
                sectors[sector] += holding["value"]
            
            portfolio_context += "\nSector Allocation:\n"
            for sector, value in sectors.items():
                allocation = (value / total_value) * 100 if total_value > 0 else 0
                portfolio_context += f"- {sector}: ₹{value:.2f} ({allocation:.2f}%)\n"
            
            # Get market data for context
            market_data = stock_data.get_market_overview()
            market_context = "Current Market Conditions:\n"
            for index in market_data.get("indices", []):
                change_sign = "+" if index.get("change", 0) >= 0 else ""
                market_context += f"- {index.get('name', '')}: {index.get('value', 0):.2f} ({change_sign}{index.get('change_percent', 0):.2f}%)\n"
            
            # Build prompt for the LLM
            prompt = f"""You are a portfolio manager specializing in Indian markets. Analyze this investment portfolio and provide recommendations.

{portfolio_context}

{market_context}

Generate a comprehensive portfolio analysis report with the following sections:
1. Portfolio Summary - Overview of current holdings and allocation
2. Performance Analysis - Assessment of portfolio performance
3. Risk Assessment - Analysis of portfolio risk factors
4. Diversification Analysis - Evaluation of portfolio diversification
5. Sector Exposure - Analysis of sector allocation and risks
6. Recommendations - Specific suggestions for portfolio optimization
   - Holdings to maintain
   - Holdings to increase
   - Holdings to reduce
   - New positions to consider
7. Tax Considerations - Indian tax implications for recommended changes

Format the report with clear section headings and well-organized content. Include specific data points from the provided information to support your analysis.
Ensure all recommendations are suitable for the Indian market and consider Indian tax regulations.
"""
            
            response = groq_client.generate_response(prompt, temperature=0.3, max_tokens=2000)
            report_content = response.get("text", "Failed to generate portfolio analysis report")
        
        return {
            "report_type": report_type,
            "content": report_content,
            "parameters": parameters,
            "timestamp": datetime.now().isoformat()
        }
    
    def _format_market_data(self, market_data, sectors_data):
        """Format market data for LLM consumption"""
        context = "Current Indian Market Indices:\n"
        for index in market_data.get("indices", []):
            change_sign = "+" if index.get("change", 0) >= 0 else ""
            context += f"- {index.get('name', '')}: {index.get('value', 0):.2f} ({change_sign}{index.get('change_percent', 0):.2f}%)\n"
        
        context += "\nSector Performance (30 days):\n"
        for sector in sectors_data.get("sectors", []):
            change_sign = "+" if sector.get("monthly_change", 0) >= 0 else ""
            context += f"- {sector.get('name', '')}: {change_sign}{sector.get('monthly_change_percent', 0):.2f}%\n"
            
        return context
    
    def _format_news_data(self, news_data):
        """Format news data for LLM consumption"""
        context = "Recent Market News:\n"
        for article in news_data.get("articles", []):
            context += f"- {article.get('title', '')}\n"
            if article.get('content'):
                context += f"  Summary: {article.get('content', '')[:200]}...\n"
                
        return context

# Create financial agent instance
financial_agent = FinancialAgent()