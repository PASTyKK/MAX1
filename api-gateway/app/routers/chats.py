from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete  # обязательно импортировать select и delete
from ..db import get_db
from .. import crud, schemas, dependencies, models

router = APIRouter(prefix="/chats", tags=["chats"])

@router.post("/", response_model=schemas.ChatOut)
async def create_chat(chat: schemas.ChatCreate, current_user=Depends(dependencies.get_current_user), db: AsyncSession = Depends(get_db)):
    return await crud.create_chat(db, chat, current_user["user_id"])

@router.get("/", response_model=list[schemas.ChatOut])
async def list_chats(current_user=Depends(dependencies.get_current_user), db: AsyncSession = Depends(get_db)):
    return await crud.get_chats_for_user(db, current_user["user_id"])

@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: int,
    current_user=Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Проверяем существование чата
    chat = await db.execute(select(models.Chat).where(models.Chat.id == chat_id))
    chat = chat.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Проверяем, является ли пользователь участником чата
    membership = await db.execute(
        select(models.chat_members).where(
            models.chat_members.c.chat_id == chat_id,
            models.chat_members.c.user_id == current_user["user_id"]
        )
    )
    if membership.first() is None:
        raise HTTPException(status_code=403, detail="You are not a member of this chat")

    # Удаляем все сообщения чата
    await db.execute(delete(models.Message).where(models.Message.chat_id == chat_id))
    # Удаляем записи об участниках чата
    await db.execute(delete(models.chat_members).where(models.chat_members.c.chat_id == chat_id))
    # Удаляем сам чат
    await db.execute(delete(models.Chat).where(models.Chat.id == chat_id))

    await db.commit()
    return {"message": "Chat deleted"}