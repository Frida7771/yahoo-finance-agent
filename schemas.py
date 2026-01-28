"""
Pydantic Schemas (请求/响应模型)
"""
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


# ========== Enums ==========
class ConversationType(str, Enum):
    agent = "agent"  # Yahoo Finance Agent
    rag = "rag"      # SEC 文档问答


# ========== Chat ==========
class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    model: str | None = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str


# ========== RAG ==========
class RAGRequest(BaseModel):
    question: str
    conversation_id: str | None = None


class RAGResponse(BaseModel):
    answer: str
    sources: list[str] = []
    conversation_id: str


# ========== Message ==========
class MessageSchema(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== Conversation ==========
class ConversationSchema(BaseModel):
    id: str
    title: str
    conversation_type: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageSchema] = []
    
    class Config:
        from_attributes = True


class ConversationListItem(BaseModel):
    id: str
    title: str
    conversation_type: str
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ========== Stock ==========
class StockInfoResponse(BaseModel):
    symbol: str
    name: str | None = None
    price: float | None = None
    market_cap: int | None = None
    pe_ratio: float | None = None
    sector: str | None = None
    industry: str | None = None


class StockChartData(BaseModel):
    dates: list[str]
    prices: list[float]
    volumes: list[int]
