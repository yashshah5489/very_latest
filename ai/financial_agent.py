"""
Financial Agent for Indian Financial Analyzer
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from ai.groq_client import GroqClient
from ai.rag_system import rag_system
from data_sources.stock_data import stock_data
from data_sources.news_extractor import news_extractor

logger = logging.getLogger(__name__)

class FinancialAgent:
    """
    AI-powered financial agent specialized for Indian markets
    """
    
    def __init__(self, groq_client=None):
        """
        Initialize the financial agent.
        
        Args:
            groq_client: Optional pre-configured Groq client
        """
        self.groq_client = groq_client or GroqClient()
        
    def market_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of current market conditions.
        
        Returns:
            Dictionary with market summary information
        """
        try:
            # Get market data
            market_data = stock_data.get_market_overview()
            sector_data = stock_data.get_sector_performance()
            
            # Get recent market news
            news_data = news_extractor.get_market_news(market="Indian", limit=5)
            
            # Format context for LLM
            context = "Current Indian Market Data:\n"
            
            if market_data.get("indices"):
                context += "Market Indices:\n"
                for index in market_data["indices"]:
                    change_sign = "+" if index.get("change", 0) >= 0 else ""
                    context += f"- {index.get('name')}: {index.get('value', 0):.2f} ({change_sign}{index.get('change_percent', 0):.2f}%)\n"
            
            if sector_data.get("sectors"):
                context += "\nSector Performance:\n"
                for sector in sector_data["sectors"]:
                    change_sign = "+" if sector.get("change", 0) >= 0 else ""
                    context += f"- {sector.get('name')}: {change_sign}{sector.get('change_percent', 0):.2f}%\n"
            
            if news_data.get("articles"):
                context += "\nRecent Market News Headlines:\n"
                for i, article in enumerate(news_data["articles"], 1):
                    if i > 5:  # Limit to 5 news items
                        break
                    context += f"- {article.get('title')} ({article.get('source')})\n"
            
            # Generate analysis
            prompt = (
                "You are a financial advisor specializing in Indian markets. "
                "Provide a concise, insightful summary of current market conditions "
                "based on the following data. Focus on main trends, notable movements, "
                "and possible factors affecting the market. Tailor your response for "
                "Indian investors, referencing relevant economic context.\n\n"
                f"{context}\n\n"
                "Format your response with the following sections:\n"
                "1. Market Overview (overall sentiment and major index movements)\n"
                "2. Sector Insights (which sectors are performing well/poorly and why)\n"
                "3. Short-term Outlook (what investors might expect in the coming days/weeks)\n"
            )
            
            response = self.groq_client.analyze_finance(prompt)
            
            # Parse the response to extract key insights
            # For simplicity, we'll just use the full response
            summary = response
            
            return {
                "timestamp": datetime.now().isoformat(),
                "summary": summary,
                "market_data": market_data,
                "sector_data": sector_data
            }
            
        except Exception as e:
            logger.error(f"Error generating market summary: {str(e)}")
            return {
                "timestamp": datetime.now().isoformat(),
                "summary": "Unable to generate market summary due to an error. Please try again later.",
                "error": str(e)
            }
    
    def stock_analysis(self, symbol: str, company_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate an analysis for a specific stock.
        
        Args:
            symbol: Stock symbol
            company_name: Optional company name
            
        Returns:
            Dictionary with stock analysis
        """
        try:
            # Get stock data
            price_data = stock_data.get_stock_price(symbol)
            company_info = stock_data.get_company_info(symbol)
            
            # Get recent news about the stock
            news_data = news_extractor.get_stock_news(symbol=symbol, limit=3)
            
            # Format context for LLM
            context = f"Analysis for {company_name or symbol} ({symbol}):\n\n"
            
            if company_info:
                context += "Company Information:\n"
                context += f"- Name: {company_info.get('name', 'N/A')}\n"
                context += f"- Sector: {company_info.get('sector', 'N/A')}\n"
                context += f"- Industry: {company_info.get('industry', 'N/A')}\n"
                context += f"- Current Price: ₹{company_info.get('current_price', 0):.2f}\n"
                
                if company_info.get('market_cap'):
                    context += f"- Market Cap: ₹{company_info.get('market_cap') / 10000000:.2f} Cr\n"
                
                if company_info.get('pe_ratio'):
                    context += f"- P/E Ratio: {company_info.get('pe_ratio'):.2f}\n"
                
                if company_info.get('eps'):
                    context += f"- EPS: ₹{company_info.get('eps'):.2f}\n"
                
                if company_info.get('dividend_yield'):
                    context += f"- Dividend Yield: {company_info.get('dividend_yield') * 100:.2f}%\n"
                
                if company_info.get('52w_high'):
                    context += f"- 52 Week High: ₹{company_info.get('52w_high'):.2f}\n"
                
                if company_info.get('52w_low'):
                    context += f"- 52 Week Low: ₹{company_info.get('52w_low'):.2f}\n"
            
            if price_data:
                context += "\nRecent Price Performance:\n"
                
                if 'change' in price_data and 'change_percent' in price_data:
                    change_sign = "+" if price_data.get('change', 0) >= 0 else ""
                    context += f"- Today's Change: {change_sign}{price_data.get('change', 0):.2f} ({change_sign}{price_data.get('change_percent', 0):.2f}%)\n"
                
                if 'volume' in price_data:
                    context += f"- Volume: {price_data.get('volume', 0):,}\n"
                
                if 'avg_volume' in price_data:
                    context += f"- Average Volume: {price_data.get('avg_volume', 0):,}\n"
                
                if 'performance' in price_data:
                    perf = price_data['performance']
                    if '1m' in perf:
                        context += f"- 1 Month: {perf['1m']:.2f}%\n"
                    if '3m' in perf:
                        context += f"- 3 Month: {perf['3m']:.2f}%\n"
                    if '6m' in perf:
                        context += f"- 6 Month: {perf['6m']:.2f}%\n"
                    if '1y' in perf:
                        context += f"- 1 Year: {perf['1y']:.2f}%\n"
            
            if news_data.get("articles"):
                context += "\nRecent News:\n"
                for article in news_data["articles"]:
                    context += f"- {article.get('title')} ({article.get('published_date')})\n"
                    if article.get('content'):
                        # Include a snippet of the content
                        snippet = article['content'][:200] + "..." if len(article['content']) > 200 else article['content']
                        context += f"  Summary: {snippet}\n"
            
            # Generate analysis
            prompt = (
                "You are a financial analyst specializing in Indian stock markets. "
                "Provide a detailed analysis of the following stock based on the provided data. "
                "Focus on current valuation, recent performance, news impact, and outlook. "
                "Tailor your analysis for Indian investors, considering relevant market context.\n\n"
                f"{context}\n\n"
                "Format your analysis with the following sections:\n"
                "1. Company Overview (brief description of business and market position)\n"
                "2. Financial Assessment (valuation metrics, financial health)\n"
                "3. Recent Performance (price action, news impact)\n"
                "4. Outlook & Recommendation (potential future performance, risk factors, investment thesis)\n"
            )
            
            analysis = self.groq_client.analyze_finance(prompt)
            
            return {
                "symbol": symbol,
                "company_name": company_info.get('name', company_name or symbol),
                "analysis": analysis,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating stock analysis for {symbol}: {str(e)}")
            return {
                "symbol": symbol,
                "company_name": company_name or symbol,
                "analysis": f"Unable to generate analysis for {symbol} due to an error. Please try again later.",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_investment_advice(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate personalized investment advice based on a user profile.
        
        Args:
            profile: Dictionary containing user investment profile information
            
        Returns:
            Dictionary with personalized investment advice
        """
        try:
            # Extract profile information
            risk_tolerance = profile.get('risk_tolerance', 'moderate')
            investment_horizon = profile.get('investment_horizon', 'medium')
            goals = profile.get('goals', [])
            current_investments = profile.get('current_investments', [])
            
            # Get current market data
            market_data = stock_data.get_market_overview()
            
            # Format context for LLM
            context = "User Investment Profile:\n"
            context += f"- Risk Tolerance: {risk_tolerance}\n"
            context += f"- Investment Horizon: {investment_horizon}\n"
            
            if goals:
                context += "- Investment Goals:\n"
                for goal in goals:
                    context += f"  * {goal.get('description')}: ₹{goal.get('target_amount', 0):,} in {goal.get('timeframe', 'N/A')}\n"
            
            if current_investments:
                context += "- Current Investments:\n"
                for investment in current_investments:
                    context += f"  * {investment.get('type')}: {investment.get('allocation', 0)}% (₹{investment.get('amount', 0):,})\n"
            
            if market_data.get("indices"):
                context += "\nCurrent Market Indices:\n"
                for index in market_data["indices"]:
                    change_sign = "+" if index.get("change", 0) >= 0 else ""
                    context += f"- {index.get('name')}: {index.get('value', 0):.2f} ({change_sign}{index.get('change_percent', 0):.2f}%)\n"
            
            # Generate advice
            prompt = (
                "You are a financial advisor specializing in Indian markets. "
                "Provide personalized investment advice based on the following user profile "
                "and current market conditions. Tailor your recommendations specifically "
                "for Indian investors, considering available investment options in India, "
                "tax implications, and current market environment.\n\n"
                f"{context}\n\n"
                "Format your advice with the following sections:\n"
                "1. Portfolio Assessment (evaluation of current allocation if available)\n"
                "2. Recommended Asset Allocation (specific percentages across asset classes)\n"
                "3. Investment Suggestions (specific types of funds/instruments suitable for the investor)\n"
                "4. Action Plan (concrete next steps the investor should take)\n"
            )
            
            advice = self.groq_client.analyze_finance(prompt)
            
            return {
                "advice": advice,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating investment advice: {str(e)}")
            return {
                "advice": "Unable to generate personalized investment advice due to an error. Please try again later.",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def answer_financial_question(self, question: str) -> Dict[str, Any]:
        """
        Answer a financial question using AI and financial book knowledge.
        
        Args:
            question: The financial question to answer
            
        Returns:
            Dictionary with answer information
        """
        try:
            # First, get insights from financial books
            book_insights = rag_system.answer_financial_question(question)
            
            # Then, augment with current market context
            market_data = stock_data.get_market_overview()
            
            market_context = "Current Indian Market Context:\n"
            if market_data.get("indices"):
                for index in market_data["indices"]:
                    change_sign = "+" if index.get("change", 0) >= 0 else ""
                    market_context += f"- {index.get('name')}: {index.get('value', 0):.2f} ({change_sign}{index.get('change_percent', 0):.2f}%)\n"
            
            # Generate a comprehensive answer
            prompt = (
                "You are a financial advisor specializing in Indian markets. "
                f"The user asks: \"{question}\"\n\n"
                "Provide a comprehensive answer combining financial wisdom from books "
                "and current market context. Focus on relevance to Indian investors.\n\n"
                f"Insights from financial books:\n{book_insights.get('answer')}\n\n"
                f"{market_context}\n\n"
                "Provide a clear, actionable answer that integrates the book knowledge "
                "with current market context. Be specific to Indian markets where relevant."
            )
            
            answer = self.groq_client.analyze_finance(prompt)
            
            return {
                "question": question,
                "answer": answer,
                "book_sources": book_insights.get("sources", []),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error answering financial question: {str(e)}")
            return {
                "question": question,
                "answer": f"Unable to answer this question due to an error. Please try again later.",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_financial_report(self, report_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a financial report of a specific type.
        
        Args:
            report_type: Type of report to generate
            data: Data to use for generating the report
            
        Returns:
            Dictionary with generated report
        """
        try:
            report_content = ""
            
            if report_type == "portfolio_analysis":
                portfolio = data.get("portfolio", [])
                
                context = "Portfolio Holdings:\n"
                for holding in portfolio:
                    context += f"- {holding.get('symbol')}: {holding.get('shares')} shares at ₹{holding.get('purchase_price', 0):.2f}\n"
                
                prompt = (
                    "You are a portfolio analyst specializing in Indian markets. "
                    "Analyze the following investment portfolio and provide insights "
                    "on diversification, risk exposure, potential areas of improvement, "
                    "and overall assessment. Tailor your analysis for Indian investors.\n\n"
                    f"{context}\n\n"
                    "Format your analysis with the following sections:\n"
                    "1. Portfolio Overview (composition, total value, key characteristics)\n"
                    "2. Risk Assessment (concentration risks, sector exposure)\n"
                    "3. Performance Analysis (estimated returns, benchmark comparison)\n"
                    "4. Recommendations (suggestions for optimization)\n"
                )
                
                report_content = self.groq_client.analyze_finance(prompt)
            
            elif report_type == "market_outlook":
                timeframe = data.get("timeframe", "short_term")
                sectors = data.get("sectors", [])
                
                # Get market data
                market_data = stock_data.get_market_overview()
                sector_data = stock_data.get_sector_performance()
                
                # Format context
                context = "Current Indian Market Data:\n"
                if market_data.get("indices"):
                    for index in market_data["indices"]:
                        change_sign = "+" if index.get("change", 0) >= 0 else ""
                        context += f"- {index.get('name')}: {index.get('value', 0):.2f} ({change_sign}{index.get('change_percent', 0):.2f}%)\n"
                
                if sectors and sector_data.get("sectors"):
                    context += "\nSelected Sectors Performance:\n"
                    for sector_name in sectors:
                        sector = next((s for s in sector_data["sectors"] if s.get("name") == sector_name), None)
                        if sector:
                            change_sign = "+" if sector.get("change", 0) >= 0 else ""
                            context += f"- {sector.get('name')}: {change_sign}{sector.get('change_percent', 0):.2f}%\n"
                
                timeframe_desc = {
                    "short_term": "1-3 months",
                    "medium_term": "6-12 months",
                    "long_term": "1-3 years"
                }.get(timeframe, "short to medium term")
                
                prompt = (
                    "You are a market strategist specializing in Indian markets. "
                    f"Provide a {timeframe_desc} outlook for the Indian market"
                    f"{' with focus on the selected sectors' if sectors else ''}. "
                    "Consider current market conditions, economic factors, and potential "
                    "catalysts. Tailor your outlook specifically for Indian investors.\n\n"
                    f"{context}\n\n"
                    "Format your outlook with the following sections:\n"
                    "1. Market Overview (current positioning and sentiment)\n"
                    "2. Key Drivers (factors likely to influence market direction)\n"
                    f"3. {timeframe.replace('_', ' ').title()} Outlook (probable scenarios and targets)\n"
                    "4. Investment Strategy (recommendations for the period)\n"
                )
                
                report_content = self.groq_client.analyze_finance(prompt)
            
            else:
                return {
                    "error": f"Unsupported report type: {report_type}",
                    "timestamp": datetime.now().isoformat()
                }
            
            return {
                "report_type": report_type,
                "content": report_content,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating {report_type} report: {str(e)}")
            return {
                "report_type": report_type,
                "content": f"Unable to generate {report_type} report due to an error. Please try again later.",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Initialize global instance
financial_agent = FinancialAgent()