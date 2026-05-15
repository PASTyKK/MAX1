from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from . import models, schemas

async def create_chat(db: AsyncSession, chat_data: schemas.ChatCreate, owner_id: int):
    chat = models.Chat(name=chat_data.name, created_by=owner_id)
    db.add(chat)
    await db.flush()
    member_ids = set(chat_data.member_ids)
    member_ids.add(owner_id)
    for member_id in member_ids:
        await db.execute(models.chat_members.insert().values(chat_id=chat.id, user_id=member_id))
    await db.commit()
    await db.refresh(chat)
    return chat

async def get_chats_for_user(db: AsyncSession, user_id: int):
    stmt = select(models.Chat).join(models.chat_members).where(models.chat_members.c.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalars().all()

async def create_message(db: AsyncSession, chat_id: int, sender_id: int, text: str):
    msg = models.Message(chat_id=chat_id, sender_id=sender_id, text=text)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg

async def get_messages(db: AsyncSession, chat_id: int, limit: int = 50):
    stmt = select(models.Message).where(models.Message.chat_id == chat_id).order_by(models.Message.sent_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()