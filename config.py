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
    langchain_project: str = "quantbrains"
    
    # Database (PostgreSQL)
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/finance_agent"
    
    # RAG
    documents_dir: Path = BASE_DIR / "documents"
    vector_store_dir: Path = BASE_DIR / "data" / "vector_store"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Alpaca (Real-time data)
    alpaca_api_key: str | None = None
    alpaca_secret_key: str | None = None
    alpaca_paper: bool = True  # Use paper trading (free)
    
    # Redis (Message Queue for real-time data)
    redis_url: str = "redis://localhost:6379"
    redis_stream_name: str = "stock_quotes"
    redis_consumer_group: str = "quote_consumers"
    
    # Google OAuth
    google_client_id: str | None = None
    google_client_secret: str | None = None
    
    # JWT
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days
    
    # API
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # 用量限制
    free_ai_limit: int = 1  # 免费用户 AI 分析次数限制
    free_ai_reset_hours: int = 24  # 重置周期 (小时)


@lru_cache
def get_settings() -> Settings:
    return Settings()

