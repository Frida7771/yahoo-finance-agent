"""
Watchlist API Routes - 用户自选股管理
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Watchlist, User
from routes.auth import get_current_user, require_user

router = APIRouter()


# Pydantic schemas
class WatchlistCreate(BaseModel):
    name: str
    symbols: list[str] = []


class WatchlistUpdate(BaseModel):
    name: Optional[str] = None
    symbols: Optional[list[str]] = None


class WatchlistResponse(BaseModel):
    id: int
    name: str
    symbols: list[str]
    
    @classmethod
    def from_db(cls, watchlist: Watchlist) -> "WatchlistResponse":
        symbols = [s.strip() for s in watchlist.symbols.split(",") if s.strip()]
        return cls(id=watchlist.id, name=watchlist.name, symbols=symbols)


# Routes
@router.get("", response_model=list[WatchlistResponse])
async def get_watchlists(
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户的所有自选股列表"""
    result = await db.execute(
        select(Watchlist).where(Watchlist.user_id == user.id).order_by(Watchlist.created_at)
    )
    watchlists = result.scalars().all()
    
    # 如果用户没有任何列表，创建默认的
    if not watchlists:
        default_lists = [
            Watchlist(user_id=user.id, name="Tech", symbols="AAPL,MSFT,NVDA,GOOGL,META"),
            Watchlist(user_id=user.id, name="Finance", symbols="JPM,BAC,GS,MS"),
        ]
        for wl in default_lists:
            db.add(wl)
        await db.commit()
        
        # 重新查询
        result = await db.execute(
            select(Watchlist).where(Watchlist.user_id == user.id).order_by(Watchlist.created_at)
        )
        watchlists = result.scalars().all()
    
    return [WatchlistResponse.from_db(wl) for wl in watchlists]


@router.post("", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
async def create_watchlist(
    data: WatchlistCreate,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db)
):
    """创建新的自选股列表"""
    watchlist = Watchlist(
        user_id=user.id,
        name=data.name,
        symbols=",".join(data.symbols)
    )
    db.add(watchlist)
    await db.commit()
    await db.refresh(watchlist)
    
    return WatchlistResponse.from_db(watchlist)


@router.put("/{watchlist_id}", response_model=WatchlistResponse)
async def update_watchlist(
    watchlist_id: int,
    data: WatchlistUpdate,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db)
):
    """更新自选股列表"""
    result = await db.execute(
        select(Watchlist).where(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == user.id
        )
    )
    watchlist = result.scalar_one_or_none()
    
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    if data.name is not None:
        watchlist.name = data.name
    if data.symbols is not None:
        watchlist.symbols = ",".join(data.symbols)
    
    await db.commit()
    await db.refresh(watchlist)
    
    return WatchlistResponse.from_db(watchlist)


@router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watchlist(
    watchlist_id: int,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db)
):
    """删除自选股列表"""
    result = await db.execute(
        select(Watchlist).where(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == user.id
        )
    )
    watchlist = result.scalar_one_or_none()
    
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    # 确保至少保留一个列表
    count_result = await db.execute(
        select(Watchlist).where(Watchlist.user_id == user.id)
    )
    count = len(count_result.scalars().all())
    
    if count <= 1:
        raise HTTPException(status_code=400, detail="Cannot delete the last watchlist")
    
    await db.delete(watchlist)
    await db.commit()


@router.post("/{watchlist_id}/symbols/{symbol}")
async def add_symbol(
    watchlist_id: int,
    symbol: str,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db)
):
    """添加股票到列表"""
    result = await db.execute(
        select(Watchlist).where(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == user.id
        )
    )
    watchlist = result.scalar_one_or_none()
    
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    symbols = [s.strip() for s in watchlist.symbols.split(",") if s.strip()]
    symbol = symbol.upper()
    
    if symbol not in symbols:
        symbols.append(symbol)
        watchlist.symbols = ",".join(symbols)
        await db.commit()
    
    return {"message": f"Added {symbol}", "symbols": symbols}


@router.delete("/{watchlist_id}/symbols/{symbol}")
async def remove_symbol(
    watchlist_id: int,
    symbol: str,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db)
):
    """从列表移除股票"""
    result = await db.execute(
        select(Watchlist).where(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == user.id
        )
    )
    watchlist = result.scalar_one_or_none()
    
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    symbols = [s.strip() for s in watchlist.symbols.split(",") if s.strip()]
    symbol = symbol.upper()
    
    if symbol in symbols:
        symbols.remove(symbol)
        watchlist.symbols = ",".join(symbols)
        await db.commit()
    
    return {"message": f"Removed {symbol}", "symbols": symbols}

