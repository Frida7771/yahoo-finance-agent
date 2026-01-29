"""
配置管理
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path


# 项目根目录
BASE_DIR = Path(__file__).parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    
    # LangSmith (可选)
    langchain_tracing_v2: bool = False
    langchain_api_key: str | None = None
    langchain_project: str = "finance-agent"
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./data/finance_agent.db"
    
    # RAG
    documents_dir: Path = BASE_DIR / "documents"
    vector_store_dir: Path = BASE_DIR / "data" / "vector_store"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Alpaca (Real-time data)
    alpaca_api_key: str | None = None
    alpaca_secret_key: str | None = None
    alpaca_paper: bool = True  # Use paper trading (free)
    
    # API
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()

