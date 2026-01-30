# 📈 QuantBrains

An AI-powered financial analyst assistant built with FastAPI, LangGraph, and React. Features natural language queries, real-time stock data, SEC 10-K document analysis, and personalized watchlists.

## Demo

| Homepage | Real-Time Dashboard |
|----------|---------------------|
| ![Homepage](demo/page.jpg) | ![Dashboard](demo/dashboard.jpg) |


---

## Features

### 🔐 Authentication
- **Google OAuth**: Secure login with Google account

### 🤖 AI Analysis
- **Natural Language Queries**: Ask questions like "Analyze Apple's valuation and risks"
- **Real-time Data**: Live data from Yahoo Finance (price, financials, valuation metrics)
- **SEC 10-K Analysis**: Risk factors, legal proceedings, executive compensation, cybersecurity
- **LangSmith Integration**: Full observability and tracing

### 📊 Real-Time Dashboard
- **Live Quotes**: WebSocket-powered real-time stock prices via Alpaca
- **User Watchlists**: Create custom watchlists saved to your account
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
| **Database** | PostgreSQL + SQLAlchemy (async) |
| **Agent** | LangGraph (LangChain 1.x) + OpenAI |
| **Vector Store** | FAISS + OpenAI Embeddings |
| **Real-time** | Alpaca WebSocket + Redis Streams |
| **Auth** | Google OAuth 2.0 + JWT |
| **Data Sources** | Yahoo Finance API, SEC EDGAR API |

---

## Quick Start

### 1. Prerequisites

```bash
# PostgreSQL
docker run -d --name postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=finance_agent \
  -p 5432:5432 postgres:15

# Redis (optional, for real-time)
docker run -d --name redis -p 6379:6379 redis:7
```

### 2. Setup

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

### 3. Configure

Create `.env` file:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/finance_agent

# Google OAuth (required for login)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# JWT (change in production!)
JWT_SECRET_KEY=your-secret-key-change-in-production

# Optional: LangSmith tracing
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key

# Optional: Real-time quotes
ALPACA_API_KEY=your_alpaca_api_key
ALPACA_SECRET_KEY=your_alpaca_secret_key

# Optional: Redis
REDIS_URL=redis://localhost:6379
```

Frontend `.env` (`frontend/.env`):
```bash
VITE_GOOGLE_CLIENT_ID=your_google_client_id
```

### 4. Run

```bash
# Terminal 1: Backend
python main.py

# Terminal 2: Frontend (dev mode)
cd frontend && npm run dev
```

### 5. Access

| URL | Description |
|-----|-------------|
| http://localhost:5173 | Frontend (dev) |
| http://localhost:8000 | Backend API |
| http://localhost:8000/docs | API Documentation |


## License

MIT
