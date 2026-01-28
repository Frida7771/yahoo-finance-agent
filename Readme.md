# Yahoo Finance LLM Agent

A FastAPI-based financial assistant powered by OpenAI, LangChain, and Yahoo Finance. Supports natural language queries for real-time stock data and SEC document Q&A.

## Demo

### 💬 Stock Agent - Natural Language Queries

![Stock Agent Demo](demo/stocks.jpg)

**Example Queries:**
```
> What's Apple's current stock price?
> Show me Microsoft's revenue and profit for the last 3 years
> What do analysts recommend for NVDA?
> Get Tesla's price history for last month
```

### 📄 RAG - SEC Document Q&A

![RAG Demo](demo/sec.jpg)

**Example Queries:**
```
> What was Microsoft's total revenue in 2025?
> What are the main risk factors mentioned in the 10-K?
> Summarize the company's business strategy
```

### 📊 API Response Example

```json
{
  "response": "Apple Inc. (AAPL) current stock information:\n\n- **Current Price:** $258.27\n- **Market Cap:** $3.82 trillion\n- **P/E Ratio:** 34.62\n- **52-Week High:** $288.62\n- **52-Week Low:** $169.21",
  "conversation_id": "91db28e1-d913-4aa6-b77b-fc7d6f75ceed"
}
```

---

## Features

### Finance Agent (`/api/chat`)
- **Natural Language Queries**: Ask questions like "What's Apple's current stock price?"
- **Real-time Data**: Fetches live data from Yahoo Finance
- **Stock Information**: Price, market cap, PE ratio, sector, etc.
- **Financial Statements**: Income statements, balance sheets, cash flow
- **Historical Data**: Price history with customizable periods
- **Analyst Recommendations**: Buy/sell ratings and price targets
- **Options Data**: Expiration dates and option chains
- **Stock News**: Latest news for any ticker

### RAG Document Q&A (`/api/rag`)
- **SEC Filing Analysis**: Ask questions about Microsoft's 10-K annual report
- **Vector Search**: FAISS-powered similarity search
- **Source Citations**: Returns relevant document snippets

### Direct Stock API (`/api/stock`)
- **Simple REST API**: Direct stock data queries for frontend integration
- **Chart Data**: Historical prices for visualization

## Tech Stack

- **Backend**: FastAPI + Uvicorn
- **LLM**: OpenAI GPT-4o / GPT-4o-mini
- **Agent**: LangChain with OpenAI Functions
- **Vector Store**: FAISS
- **Database**: SQLite (conversation history)
- **Data Source**: Yahoo Finance (yfinance)



## Installation

1. **Clone the repository**

```bash
git clone <your-repo-url>
cd yahoo-finance-llm-agent
```

2. **Create virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

Create a `.env` file:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key

# Optional
OPENAI_MODEL=gpt-4o-mini
DEBUG=false

# LangSmith (optional, for tracing)
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=your_langchain_api_key
LANGCHAIN_PROJECT=finance-agent
```

5. **Run the server**

```bash
# Development mode (with auto-reload)
make dev
# or
uvicorn main:app --reload

# Production mode
make run
```

6. **Access the API**

- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## API Usage

### Chat with Finance Agent

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is Apple stock price and latest news?"}'
```

### Ask SEC Documents

```bash
curl -X POST http://localhost:8000/api/rag/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What are Microsoft main risk factors?"}'
```

### Get Stock Info

```bash
curl http://localhost:8000/api/stock/AAPL
curl http://localhost:8000/api/stock/AAPL/chart?period=3mo
curl http://localhost:8000/api/stock/AAPL/news
```

## Available Tools

The Finance Agent can use these tools:

| Tool | Description |
|------|-------------|
| `get_stock_info` | Basic stock information |
| `get_historical_data` | Historical price data |
| `get_financials` | Financial statements |
| `get_stock_news` | Latest news |
| `get_recommendations` | Analyst recommendations |
| `get_holders_info` | Institutional/mutual fund holders |
| `get_stock_actions` | Dividends and splits |
| `get_shares_count` | Outstanding shares |
| `get_options_expiration_dates` | Options dates |
| `get_option_chain` | Options chain data |

## License

MIT
