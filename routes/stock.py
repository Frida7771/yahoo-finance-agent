"""
Stock API - 直接查询股票数据（简单 API，不经过 Agent）
用于前端图表展示等场景
"""
from fastapi import APIRouter, Query, HTTPException
import yfinance as yf

from schemas import StockInfoResponse, StockChartData

router = APIRouter()


@router.get("/{ticker}", response_model=StockInfoResponse)
async def get_stock_info(ticker: str):
    """
    获取股票基本信息
    
    这是一个简单的直接查询 API，适合前端展示。
    如果需要自然语言对话，请使用 /api/chat
    """
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info
        
        if not info or not info.get("regularMarketPrice"):
            raise HTTPException(status_code=404, detail=f"Stock '{ticker}' not found")
        
        return StockInfoResponse(
            symbol=info.get("symbol", ticker.upper()),
            name=info.get("shortName"),
            price=info.get("regularMarketPrice"),
            market_cap=info.get("marketCap"),
            pe_ratio=info.get("trailingPE"),
            sector=info.get("sector"),
            industry=info.get("industry"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/chart", response_model=StockChartData)
async def get_chart_data(
    ticker: str,
    period: str = Query("1mo", pattern="^(1d|5d|1mo|3mo|6mo|1y|2y|5y|max)$")
):
    """获取图表数据（用于前端绑定图表）"""
    try:
        stock = yf.Ticker(ticker.upper())
        history = stock.history(period=period)
        
        if history.empty:
            raise HTTPException(status_code=404, detail=f"No data for '{ticker}'")
        
        return StockChartData(
            dates=history.index.strftime("%Y-%m-%d").tolist(),
            prices=history["Close"].tolist(),
            volumes=history["Volume"].astype(int).tolist(),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}/news")
async def get_stock_news(ticker: str):
    """获取股票新闻"""
    try:
        stock = yf.Ticker(ticker.upper())
        news = stock.news or []
        
        return [
            {
                "title": n.get("title"),
                "link": n.get("link"),
                "publisher": n.get("publisher"),
            }
            for n in news[:10]
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
