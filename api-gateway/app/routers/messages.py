from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db import get_db
from .. import crud, schemas, dependencies, models
import redis.asyncio as redis
import json
import os

router = APIRouter(prefix="/messages", tags=["messages"])
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL)

@router.post("/{chat_id}", response_model=schemas.MessageOut, summary="Отправить сообщение в чат")
async def send_message(
    chat_id: int,
    msg: schemas.MessageCreate,
    current_user=Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    membership = await db.execute(
        select(models.chat_members).where(
            models.chat_members.c.chat_id == chat_id,
            models.chat_members.c.user_id == current_user["user_id"]
        )
    )
    if membership.first() is None:
        raise HTTPException(status_code=403, detail="Not a member")
    new_msg = await crud.create_message(db, chat_id, current_user["user_id"], msg.text)
    try:
        await redis_client.publish("notifications", json.dumps({
            "type": "new_message",
            "chat_id": chat_id,
            "message": new_msg.text,
            "sender_id": current_user["user_id"],
            "timestamp": new_msg.sent_at.isoformat()
        }))
    except Exception as e:
        print(f"Redis publish failed: {e}")
    return new_msg

@router.get("/{chat_id}", response_model=list[schemas.MessageOut], summary="Получить историю сообщений")
async def get_messages(
    chat_id: int,
    limit: int = 50,
    current_user=Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await crud.get_messages(db, chat_id, limit)

@router.websocket("/ws/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: int, token: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        pass