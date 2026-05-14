from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class ChatCreate(BaseModel):
    name: str
    member_ids: List[int]   # ID пользователей, которых добавить (включая создателя)

class ChatOut(BaseModel):
    id: int
    name: str
    created_at: datetime

class MessageCreate(BaseModel):
    text: str

class MessageOut(BaseModel):
    id: int
    sender_id: int
    text: str
    sent_at: datetime