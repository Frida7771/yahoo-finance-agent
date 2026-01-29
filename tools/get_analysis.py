# Description: A tool to fetch comprehensive stock analysis data
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import yfinance as yf


class StockAnalysisInput(BaseModel):
    ticker: str = Field(..., description="The ticker symbol of the stock to analyze")


@tool(args_schema=StockAnalysisInput)
def get_stock_analysis(ticker: str) -> dict:
    """
    Fetch comprehensive stock analysis data including valuation metrics, 
    profitability ratios, financial health indicators, and growth metrics.
    Use this tool when user asks for stock analysis, valuation, or financial ratios.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info or info.get("regularMarketPrice") is None:
            return {"error": f"Unable to fetch data for {ticker}"}
        
        def fmt_pct(val):
            """Format percentage"""
            return f"{val * 100:.2f}%" if val else None
        
        def fmt_num(val):
            """Format large numbers"""
            if val is None:
                return None
            if val >= 1e12:
                return f"${val/1e12:.2f}T"
            if val >= 1e9:
                return f"${val/1e9:.2f}B"
            if val >= 1e6:
                return f"${val/1e6:.2f}M"
            return f"${val:,.0f}"
        
        return {
            # 基本信息
            "company": {
                "name": info.get("longName"),
                "ticker": ticker.upper(),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "market_cap": fmt_num(info.get("marketCap")),
                "enterprise_value": fmt_num(info.get("enterpriseValue")),
            },
            
            # 估值指标
            "valuation": {
                "pe_ratio_ttm": round(info.get("trailingPE", 0), 2) if info.get("trailingPE") else None,
                "pe_ratio_forward": round(info.get("forwardPE", 0), 2) if info.get("forwardPE") else None,
                "pb_ratio": round(info.get("priceToBook", 0), 2) if info.get("priceToBook") else None,
                "ps_ratio": round(info.get("priceToSalesTrailing12Months", 0), 2) if info.get("priceToSalesTrailing12Months") else None,
                "ev_to_revenue": round(info.get("enterpriseToRevenue", 0), 2) if info.get("enterpriseToRevenue") else None,
                "ev_to_ebitda": round(info.get("enterpriseToEbitda", 0), 2) if info.get("enterpriseToEbitda") else None,
                "peg_ratio": round(info.get("pegRatio", 0), 2) if info.get("pegRatio") else None,
            },
            
            # 盈利能力
            "profitability": {
                "gross_margin": fmt_pct(info.get("grossMargins")),
                "operating_margin": fmt_pct(info.get("operatingMargins")),
                "profit_margin": fmt_pct(info.get("profitMargins")),
                "roe": fmt_pct(info.get("returnOnEquity")),
                "roa": fmt_pct(info.get("returnOnAssets")),
            },
            
            # 财务健康
            "financial_health": {
                "debt_to_equity": round(info.get("debtToEquity", 0), 2) if info.get("debtToEquity") else None,
                "current_ratio": round(info.get("currentRatio", 0), 2) if info.get("currentRatio") else None,
                "quick_ratio": round(info.get("quickRatio", 0), 2) if info.get("quickRatio") else None,
                "total_debt": fmt_num(info.get("totalDebt")),
                "total_cash": fmt_num(info.get("totalCash")),
                "free_cash_flow": fmt_num(info.get("freeCashflow")),
            },
            
            # 成长性
            "growth": {
                "revenue_growth_yoy": fmt_pct(info.get("revenueGrowth")),
                "earnings_growth_yoy": fmt_pct(info.get("earningsGrowth")),
                "earnings_quarterly_growth": fmt_pct(info.get("earningsQuarterlyGrowth")),
            },
            
            # 分红
            "dividend": {
                "dividend_yield": fmt_pct(info.get("dividendYield")),
                "dividend_rate": info.get("dividendRate"),
                "payout_ratio": fmt_pct(info.get("payoutRatio")),
                "ex_dividend_date": info.get("exDividendDate"),
            },
            
            # 分析师评级
            "analyst": {
                "target_price_mean": info.get("targetMeanPrice"),
                "target_price_high": info.get("targetHighPrice"),
                "target_price_low": info.get("targetLowPrice"),
                "recommendation": info.get("recommendationKey"),
                "number_of_analysts": info.get("numberOfAnalystOpinions"),
            },
        }
        
    except Exception as e:
        return {"error": f"Error analyzing stock: {str(e)}"}

