# Description: A tool to fetch stock information for a given ticker symbol.
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import yfinance as yf


class StockInfoInput(BaseModel):
    ticker: str = Field(..., description="The ticker symbol of the stock to fetch information for")


@tool(args_schema=StockInfoInput)
def get_stock_info(ticker: str) -> dict:
    """Fetch key stock information for a given ticker symbol including price, market cap, PE ratio, etc."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info or info.get("regularMarketPrice") is None:
            return {"error": f"Unable to fetch data for {ticker}. Please check the ticker symbol."}
        
        # Return key fields for better readability
        return {
            "symbol": info.get("symbol"),
            "shortName": info.get("shortName"),
            "longName": info.get("longName"),
            "currentPrice": info.get("currentPrice") or info.get("regularMarketPrice"),
            "previousClose": info.get("previousClose"),
            "open": info.get("open"),
            "dayHigh": info.get("dayHigh"),
            "dayLow": info.get("dayLow"),
            "volume": info.get("volume"),
            "marketCap": info.get("marketCap"),
            "trailingPE": info.get("trailingPE"),
            "forwardPE": info.get("forwardPE"),
            "dividendYield": info.get("dividendYield"),
            "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
            "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
        }
    except Exception as e:
        return {"error": f"Error fetching stock info: {str(e)}"}