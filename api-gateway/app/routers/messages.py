from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from .. import crud, schemas, dependencies
import redis.asyncio as redis
import json
import os

router = APIRouter(prefix="/messages", tags=["messages"])
redis_client = redis.from_url("redis://localhost:6379")

@router.post("/{chat_id}", response_model=schemas.MessageOut)
async def send_message(chat_id: int, msg: schemas.MessageCreate, current_user=Depends(dependencies.get_current_user), db: AsyncSession = Depends(get_db)):
    new_msg = await crud.create_message(db, chat_id, current_user["user_id"], msg.text)
    # Публикуем уведомление, но если Redis не работает — просто пишем в консоль
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

@router.post("/{chat_id}", response_model=schemas.MessageOut)
async def send_message(chat_id: int, msg: schemas.MessageCreate, current_user=Depends(dependencies.get_current_user),
                       db: AsyncSession = Depends(get_db)):
    # Проверка, что пользователь участник чата
    # (опущено для краткости)
    new_msg = await crud.create_message(db, chat_id, current_user["user_id"], msg.text)

    # Публикуем событие в Redis для уведомлений
    await redis_client.publish("notifications", json.dumps({
        "type": "new_message",
        "chat_id": chat_id,
        "message": new_msg.text,
        "sender_id": current_user["user_id"],
        "timestamp": new_msg.sent_at.isoformat()
    }))
    return new_msg


@router.get("/{chat_id}", response_model=list[schemas.MessageOut])
async def get_messages(chat_id: int, limit: int = 50, current_user=Depends(dependencies.get_current_user),
                       db: AsyncSession = Depends(get_db)):
    return await crud.get_messages(db, chat_id, limit)


# WebSocket для live-чата (опционально)
@router.websocket("/ws/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: int, token: str):
    await websocket.accept()
    # Верификация через user-service (упрощённо)
    # ... (реализация соединения, broadcast через Redis)