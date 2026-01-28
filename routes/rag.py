"""
RAG API - SEC 文档问答
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models import Conversation, Message
from schemas import RAGRequest, RAGResponse, ConversationSchema, ConversationListItem
from rag import get_rag_service, remove_rag_service

router = APIRouter()


async def get_or_create_rag_conversation(
    db: AsyncSession, 
    conversation_id: str | None
) -> Conversation:
    """获取或创建 RAG 对话"""
    if conversation_id:
        result = await db.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(selectinload(Conversation.messages))
        )
        conv = result.scalar_one_or_none()
        if conv:
            return conv
    
    # 创建新对话
    conv = Conversation(id=str(uuid.uuid4()), conversation_type="rag", title="SEC Document Q&A")
    db.add(conv)
    await db.commit()
    
    # 重新查询以加载关系
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conv.id)
        .options(selectinload(Conversation.messages))
    )
    return result.scalar_one()


@router.post("/ask", response_model=RAGResponse)
async def ask_document(request: RAGRequest, db: AsyncSession = Depends(get_db)):
    """向 SEC 文档提问"""
    # 获取或创建对话
    conv = await get_or_create_rag_conversation(db, request.conversation_id)
    
    # 获取 RAG 服务并加载历史
    rag_service = await get_rag_service(conv.id)
    if conv.messages:
        rag_service.load_history([{"role": m.role, "content": m.content} for m in conv.messages])
    
    # 保存用户消息
    user_msg = Message(conversation_id=conv.id, role="user", content=request.question)
    db.add(user_msg)
    
    # 获取回答
    answer, sources = await rag_service.ask(request.question)
    
    # 保存助手消息
    assistant_msg = Message(conversation_id=conv.id, role="assistant", content=answer)
    db.add(assistant_msg)
    
    # 更新对话标题（如果是第一条消息）
    if len(conv.messages) == 0:
        conv.title = request.question[:50] + ("..." if len(request.question) > 50 else "")
    
    await db.commit()
    
    return RAGResponse(answer=answer, sources=sources, conversation_id=conv.id)


@router.post("/rebuild-index")
async def rebuild_index():
    """重建向量索引"""
    from rag import RAGService
    service = RAGService()
    await service.rebuild_index()
    return {"status": "Index rebuilt successfully"}


@router.get("/conversations", response_model=list[ConversationListItem])
async def list_rag_conversations(db: AsyncSession = Depends(get_db)):
    """获取所有 RAG 对话列表"""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.conversation_type == "rag")
        .order_by(Conversation.updated_at.desc())
        .limit(50)
    )
    return [ConversationListItem.model_validate(c) for c in result.scalars().all()]


@router.get("/conversations/{conversation_id}", response_model=ConversationSchema)
async def get_rag_conversation(conversation_id: str, db: AsyncSession = Depends(get_db)):
    """获取 RAG 对话详情"""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.messages))
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationSchema.model_validate(conv)


@router.delete("/conversations/{conversation_id}")
async def delete_rag_conversation(conversation_id: str, db: AsyncSession = Depends(get_db)):
    """删除 RAG 对话"""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if conv:
        await db.delete(conv)
        await db.commit()
        remove_rag_service(conversation_id)
    return {"status": "deleted"}

