from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from ..db import get_db
from .. import crud, schemas, dependencies, models
import httpx

router = APIRouter(prefix="/chats", tags=["chats"])

@router.post("/", response_model=schemas.ChatOut)
async def create_chat(
    chat: schemas.ChatCreate,
    current_user=Depends(dependencies.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_id = current_user["user_id"]
    # максимум 3 участника в группе
    if len(chat.member_ids) > 3:
        raise HTTPException(status_code=400, detail="Группа может содержать не более 3 участников")
    # ============================================================
    print(f"[CREATE] name={chat.name}, member_ids={chat.member_ids}, user={user_id}")
    if len(chat.member_ids) == 2:
        other_id = [uid for uid in chat.member_ids if uid != user_id][0]
        user_chats = await crud.get_chats_for_user(db, user_id)
        for c in user_chats:
            members_res = await db.execute(select(models.chat_members.c.user_id).where(models.chat_members.c.chat_id == c.id))
            members = [row[0] for row in members_res.all()]
            if set(members) == {user_id, other_id}:
                return schemas.ChatOut(id=c.id, name=c.name, created_at=c.created_at)
    elif len(chat.member_ids) > 2:
        user_chats = await crud.get_chats_for_user(db, user_id)
        for c in user_chats:
            if c.name == chat.name:
                raise HTTPException(status_code=400, detail="Чат с таким названием уже существует")
    new_chat = await crud.create_chat(db, chat, user_id)
    return new_chat

@router.get("/", response_model=list[schemas.ChatOut])
async def list_chats(current_user=Depends(dependencies.get_current_user), db: AsyncSession = Depends(get_db)):
    return await crud.get_chats_for_user(db, current_user["user_id"])

@router.delete("/{chat_id}")
async def delete_chat(chat_id: int, current_user=Depends(dependencies.get_current_user), db: AsyncSession = Depends(get_db)):
    chat = await db.execute(select(models.Chat).where(models.Chat.id == chat_id))
    chat = chat.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    membership = await db.execute(select(models.chat_members).where(models.chat_members.c.chat_id == chat_id, models.chat_members.c.user_id == current_user["user_id"]))
    if membership.first() is None:
        raise HTTPException(status_code=403, detail="Not a member")
    await db.execute(delete(models.Message).where(models.Message.chat_id == chat_id))
    await db.execute(delete(models.chat_members).where(models.chat_members.c.chat_id == chat_id))
    await db.execute(delete(models.Chat).where(models.Chat.id == chat_id))
    await db.commit()
    return {"message": "Chat deleted"}

@router.get("/{chat_id}/members")
async def get_chat_members(chat_id: int, current_user=Depends(dependencies.get_current_user), db: AsyncSession = Depends(get_db)):
    membership = await db.execute(select(models.chat_members).where(models.chat_members.c.chat_id == chat_id, models.chat_members.c.user_id == current_user["user_id"]))
    if membership.first() is None:
        raise HTTPException(status_code=403, detail="Not a member")
    result = await db.execute(select(models.chat_members.c.user_id).where(models.chat_members.c.chat_id == chat_id))
    member_ids = [row[0] for row in result.all()]
    async with httpx.AsyncClient(verify=False) as client:
        resp = await client.get(f"{dependencies.USER_SERVICE_URL}/users", headers={"Authorization": f"Bearer {current_user['token']}"})
        if resp.status_code != 200:
            return [{"id": uid, "username": f"User {uid}"} for uid in member_ids]
        all_users = resp.json()
        return [{"id": u["id"], "username": u["username"]} for u in all_users if u["id"] in member_ids]