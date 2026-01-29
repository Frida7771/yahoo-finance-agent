"""
FastAPI 主入口
"""
import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager

# ⚠️ 必须在最开始加载 .env，让 LangSmith 能读取环境变量
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config import get_settings
from database import init_db
from routes import chat, rag, stock, realtime

# 静态文件目录
STATIC_DIR = Path(__file__).parent / "static"

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # Startup
    logger.info("Starting Finance Agent API...")
    
    # 检查 LangSmith 配置 (支持两种前缀: LANGSMITH_ 和 LANGCHAIN_)
    tracing = (
        os.getenv("LANGSMITH_TRACING", "").lower() == "true" or
        os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true"
    )
    project = os.getenv("LANGSMITH_PROJECT") or os.getenv("LANGCHAIN_PROJECT", "default")
    api_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY", "")
    
    if tracing and api_key:
        logger.info(f"✅ LangSmith tracing ENABLED - Project: {project}")
    else:
        logger.warning("⚠️ LangSmith tracing DISABLED - Check env vars")
        logger.warning(f"   LANGSMITH_TRACING={os.getenv('LANGSMITH_TRACING')}")
        logger.warning(f"   LANGSMITH_API_KEY={'***' if api_key else 'NOT SET'}")
    
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Finance Agent API...")


settings = get_settings()

app = FastAPI(
    title="Finance Agent API",
    description="""
Yahoo Finance LLM Agent API

## Features

- **Chat API**: 与 Finance Agent 对话，获取实时股票数据和分析
- **RAG API**: 基于 SEC 文档的问答（如微软 10-K 年报）
- **Stock API**: 直接查询股票数据

## Authentication

Currently no authentication required. Add your OpenAI API key in `.env` file.
    """,
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat.router, prefix="/api/chat", tags=["Chat - Finance Agent"])
app.include_router(rag.router, prefix="/api/rag", tags=["RAG - SEC Documents"])
app.include_router(stock.router, prefix="/api/stock", tags=["Stock - Direct Query"])
app.include_router(realtime.router, prefix="/api/realtime", tags=["Real-time - WebSocket"])


@app.get("/", tags=["Health"])
async def root():
    """前端页面"""
    # 优先使用 Vite 构建的 React 前端
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Frontend not built. Run 'cd frontend && npm run build'"}


@app.get("/api", tags=["Health"])
async def api_info():
    """API 信息"""
    return {
        "message": "Finance Agent API",
        "version": "0.1.0",
        "docs": "/docs",
    }


# 挂载静态文件
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/health", tags=["Health"])
async def health():
    """健康检查"""
    return {"status": "ok"}


# 开发环境运行入口
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

