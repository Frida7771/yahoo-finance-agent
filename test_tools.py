"""
测试 Yahoo Finance 工具
运行: python test_tools.py
"""
from tools import (
    get_stock_info,
    get_historical_data,
    get_stock_actions,
    get_shares_count,
    get_financials,
    get_holders_info,
    get_recommendations,
    get_options_expiration_dates,
    get_option_chain,
    get_stock_news,
)


def test_tool(name: str, func, *args, **kwargs):
    """测试单个工具"""
    print(f"\n{'='*60}")
    print(f"🧪 Testing: {name}")
    print(f"{'='*60}")
    try:
        result = func.invoke(kwargs if kwargs else {"ticker": args[0]} if args else {})
        if isinstance(result, dict):
            # 只打印前几个 key
            keys = list(result.keys())[:10]
            print(f"✅ Success! Keys: {keys}")
            if "error" in result:
                print(f"⚠️  Error in result: {result['error']}")
        elif isinstance(result, list):
            print(f"✅ Success! Got {len(result)} items")
            if result:
                print(f"   First item: {str(result[0])[:100]}...")
        else:
            print(f"✅ Success! Result: {str(result)[:200]}")
    except Exception as e:
        print(f"❌ Failed: {e}")


def main():
    ticker = "AAPL"  # 使用 Apple 作为测试
    
    print(f"\n🚀 Testing Yahoo Finance Tools with ticker: {ticker}")
    
    # 1. 股票信息
    test_tool("get_stock_info", get_stock_info, ticker=ticker)
    
    # 2. 历史数据
    test_tool("get_historical_data", get_historical_data, ticker=ticker, period="5d")
    
    # 3. 股票行为 (分红/拆股)
    test_tool("get_stock_actions", get_stock_actions, ticker=ticker, action_type="dividends")
    
    # 4. 财务数据
    test_tool("get_financials", get_financials, ticker=ticker, financial_type="income_stmt")
    
    # 5. 股东信息
    test_tool("get_holders_info", get_holders_info, ticker=ticker, holder_type="major_holders")
    
    # 6. 分析师推荐
    test_tool("get_recommendations", get_recommendations, ticker=ticker, recommendation_type="recommendations_summary")
    
    # 7. 期权到期日
    test_tool("get_options_expiration_dates", get_options_expiration_dates, ticker=ticker)
    
    # 8. 股票新闻
    test_tool("get_stock_news", get_stock_news, ticker=ticker)
    
    print(f"\n{'='*60}")
    print("🎉 All tests completed!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()

