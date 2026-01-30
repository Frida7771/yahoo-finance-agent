"""
SQLAlchemy 数据库模型
"""
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    picture: Mapped[str | None] = mapped_column(String(500), nullable=True)
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    # 用量限制
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)  # 付费用户
    ai_usage_count: Mapped[int] = mapped_column(default=0)  # AI 分析使用次数
    ai_usage_reset_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # 重置时间
    
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    watchlists: Mapped[list["Watchlist"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )


class Conversation(Base):
    """对话记录"""
    __tablename__ = "conversations"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), default="New Chat")
    conversation_type: Mapped[str] = mapped_column(String(20), default="agent")  # agent, rag
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    user: Mapped["User | None"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", 
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )


class Message(Base):
    """消息记录"""
    __tablename__ = "messages"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(20))  # user, assistant
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class Watchlist(Base):
    """用户自选股列表"""
    __tablename__ = "watchlists"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    symbols: Mapped[str] = mapped_column(Text, default="")  # 逗号分隔的股票代码
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    user: Mapped["User"] = relationship(back_populates="watchlists")
