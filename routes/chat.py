"""
Chat API - QuantBrains Agent
"""
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import json

from database import get_db
from models import Conversation, Message, User
from schemas import ChatRequest, ChatResponse, ConversationSchema, ConversationListItem
from agent import get_agent, remove_agent
from routes.auth import get_current_user
from config import get_settings

router = APIRouter()


async def check_ai_usage_limit(
    user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> User | None:
    """
    检查用户 AI 使用额度
    - 未登录用户: 不允许使用 (返回 401)
    - 付费用户: 无限制
    - 免费用户: 限制次数 (默认 1 次/24小时)
    """
    if not user:
        raise HTTPException(status_code=401, detail="Login required to use AI analysis")
    
    # 付费用户无限制
    if user.is_premium:
        return user
    
    settings = get_settings()
    now = datetime.utcnow()
    
    # 检查是否需要重置计数
    if user.ai_usage_reset_at and now >= user.ai_usage_reset_at:
        user.ai_usage_count = 0
        user.ai_usage_reset_at = None
    
    # 检查是否超出限制
    if user.ai_usage_count >= settings.free_ai_limit:
        reset_time = user.ai_usage_reset_at or (now + timedelta(hours=settings.free_ai_reset_hours))
        hours_left = int((reset_time - now).total_seconds() / 3600)
        raise HTTPException(
            status_code=429, 
            detail=f"Free usage limit reached ({settings.free_ai_limit}/day). Resets in {hours_left}h. Upgrade to Premium for unlimited access."
        )
    
    return user


async def increment_ai_usage(user: User, db: AsyncSession):
    """增加用户 AI 使用次数"""
    if user.is_premium:
        return  # 付费用户不计数
    
    settings = get_settings()
    now = datetime.utcnow()
    
    user.ai_usage_count += 1
    
    # 设置重置时间 (如果还没设置)
    if not user.ai_usage_reset_at:
        user.ai_usage_reset_at = now + timedelta(hours=settings.free_ai_reset_hours)
    
    await db.commit()


async def get_or_create_conversation(
    db: AsyncSession, 
    conversation_id: str | None,
    conversation_type: str = "agent",
    user_id: str | None = None
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
    conv = Conversation(
        id=str(uuid.uuid4()), 
        conversation_type=conversation_type,
        user_id=user_id
    )
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
async def chat(
    request: ChatRequest, 
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_ai_usage_limit)  # 检查用量限制
):
    """与 QuantBrains Agent 对话 (需要登录，免费用户有次数限制)"""
    # 获取或创建对话
    conv = await get_or_create_conversation(db, request.conversation_id, "agent", user.id if user else None)
    
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
    
    # 增加用户使用次数
    await increment_ai_usage(user, db)
    
    await db.commit()
    
    return ChatResponse(response=response, conversation_id=conv.id)


@router.get("/usage")
async def get_usage(
    user: User | None = Depends(get_current_user),  # 不检查限制，只获取用户
    db: AsyncSession = Depends(get_db)
):
    """获取用户 AI 使用情况 (不需要额度也能查)"""
    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    
    settings = get_settings()
    now = datetime.utcnow()
    
    # 检查是否需要重置
    if user.ai_usage_reset_at and now >= user.ai_usage_reset_at:
        remaining = settings.free_ai_limit
        reset_at = None
    else:
        remaining = max(0, settings.free_ai_limit - user.ai_usage_count)
        reset_at = user.ai_usage_reset_at.isoformat() if user.ai_usage_reset_at else None
    
    return {
        "is_premium": user.is_premium,
        "used": user.ai_usage_count,
        "limit": settings.free_ai_limit if not user.is_premium else -1,  # -1 表示无限
        "remaining": remaining if not user.is_premium else -1,
        "reset_at": reset_at
    }


@router.post("/stream")
async def chat_stream(
    request: ChatRequest, 
    db: AsyncSession = Depends(get_db),
    user: User = Depends(check_ai_usage_limit)  # 检查用量限制
):
    """流式对话 (需要登录，免费用户有次数限制)"""
    conv = await get_or_create_conversation(db, request.conversation_id, "agent", user.id if user else None)
    agent = get_agent(conv.id, request.model)
    
    if conv.messages:
        agent.load_history([{"role": m.role, "content": m.content} for m in conv.messages])
    
    # 先增加使用次数 (在流式响应开始前)
    await increment_ai_usage(user, db)
    
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

