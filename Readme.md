# 📈 Finance Agent

An AI-powered financial analyst assistant built with FastAPI, LangGraph, and React. Features natural language queries, real-time stock data, SEC 10-K document analysis, and live market monitoring.

## Demo

![Homepage](demo/page.jpg)

---

## Features

### 🏠 Homepage
Landing page introducing the Finance Agent with quick navigation to both interfaces.

### 🤖 AI Analysis
- **Natural Language Queries**: Ask questions like "Analyze Apple's valuation and risks"
- **Real-time Data**: Live data from Yahoo Finance (price, financials, valuation metrics)
- **SEC 10-K Analysis**: Risk factors, legal proceedings, executive compensation, cybersecurity
- **Query Builder**: Pre-built templates for common analysis requests
- **LangSmith Integration**: Full observability and tracing

### 📊 Real-Time Dashboard
- **Live Quotes**: WebSocket-powered real-time stock prices via Alpaca
- **Multiple Watchlists**: Organize stocks by category (Tech, Finance, Custom)
- **TradingView Charts**: Mini chart widgets for each stock
- **Price Alerts**: Browser notifications when price targets are hit
- **Grid/List Views**: Toggle between display modes

### 🔍 RAG Pipeline
- **Dynamic Document Ingestion**: Auto-download SEC filings via EDGAR API
- **FAISS Vector Search**: Semantic search with OpenAI embeddings
- **Auto-refresh**: Detects newer filings and updates cache automatically

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React + TypeScript + Vite + Tailwind CSS + shadcn/ui |
| **Backend** | FastAPI + Python |
| **Agent** | LangGraph (LangChain 1.x) + OpenAI |
| **Vector Store** | FAISS + OpenAI Embeddings |
| **Real-time** | Alpaca WebSocket |
| **Data Sources** | Yahoo Finance API, SEC EDGAR API |

---

## Quick Start

### 1. Setup

```bash
git clone https://github.com/Frida7771/yahoo-finance-agent
cd yahoo-finance-llm-agent

# Backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

### 2. Configure

Create `.env` file:

```bash
OPENAI_API_KEY=your_openai_api_key

# Optional: LangSmith tracing
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key

# Optional: Real-time quotes
ALPACA_API_KEY=your_alpaca_api_key
ALPACA_SECRET_KEY=your_alpaca_secret_key
```

### 3. Run

```bash
# Terminal 1: Backend
python main.py

# Terminal 2: Frontend (dev mode)
cd frontend && npm run dev
```

### 4. Access

| URL | Description |
|-----|-------------|
| http://localhost:5173 | Frontend (dev) |
| http://localhost:8000 | Backend API |
| http://localhost:8000/docs | API Documentation |


## License

MIT
