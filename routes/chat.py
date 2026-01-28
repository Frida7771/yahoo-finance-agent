"""
Chat API - Yahoo Finance Agent
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import json

from database import get_db
from models import Conversation, Message
from schemas import ChatRequest, ChatResponse, ConversationSchema, ConversationListItem
from agent import get_agent, remove_agent

router = APIRouter()


async def get_or_create_conversation(
    db: AsyncSession, 
    conversation_id: str | None,
    conversation_type: str = "agent"
) -> Conversation:
    """获取或创建对话"""
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
    conv = Conversation(id=str(uuid.uuid4()), conversation_type=conversation_type)
    db.add(conv)
    await db.commit()
    
    # 重新查询以加载关系
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conv.id)
        .options(selectinload(Conversation.messages))
    )
    return result.scalar_one()


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """与 Finance Agent 对话"""
    # 获取或创建对话
    conv = await get_or_create_conversation(db, request.conversation_id, "agent")
    
    # 获取 Agent 并加载历史
    agent = get_agent(conv.id, request.model)
    if conv.messages:
        agent.load_history([{"role": m.role, "content": m.content} for m in conv.messages])
    
    # 保存用户消息
    user_msg = Message(conversation_id=conv.id, role="user", content=request.message)
    db.add(user_msg)
    
    # 获取回复
    response = await agent.achat(request.message)
    
    # 保存助手消息
    assistant_msg = Message(conversation_id=conv.id, role="assistant", content=response)
    db.add(assistant_msg)
    
    # 更新对话标题（如果是第一条消息）
    if len(conv.messages) == 0:
        conv.title = request.message[:50] + ("..." if len(request.message) > 50 else "")
    
    await db.commit()
    
    return ChatResponse(response=response, conversation_id=conv.id)


@router.post("/stream")
async def chat_stream(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """流式对话"""
    conv = await get_or_create_conversation(db, request.conversation_id, "agent")
    agent = get_agent(conv.id, request.model)
    
    if conv.messages:
        agent.load_history([{"role": m.role, "content": m.content} for m in conv.messages])
    
    async def generate():
        full_response = ""
        async for chunk in agent.astream(request.message):
            full_response += chunk
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        
        # 保存消息到数据库
        user_msg = Message(conversation_id=conv.id, role="user", content=request.message)
        assistant_msg = Message(conversation_id=conv.id, role="assistant", content=full_response)
        db.add(user_msg)
        db.add(assistant_msg)
        await db.commit()
        
        yield f"data: {json.dumps({'done': True, 'conversation_id': conv.id})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/conversations", response_model=list[ConversationListItem])
async def list_conversations(db: AsyncSession = Depends(get_db)):
    """获取所有 Agent 对话列表"""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.conversation_type == "agent")
        .order_by(Conversation.updated_at.desc())
        .limit(50)
    )
    return [ConversationListItem.model_validate(c) for c in result.scalars().all()]


@router.get("/conversations/{conversation_id}", response_model=ConversationSchema)
async def get_conversation(conversation_id: str, db: AsyncSession = Depends(get_db)):
    """获取对话详情"""
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
async def delete_conversation(conversation_id: str, db: AsyncSession = Depends(get_db)):
    """删除对话"""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if conv:
        await db.delete(conv)
        await db.commit()
        remove_agent(conversation_id)
    return {"status": "deleted"}

