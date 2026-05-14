from pydantic import BaseModel
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserOut(BaseModel):
    id: int
    username: str

class FriendRequestOut(BaseModel):
    id: int
    from_user: UserOut
    to_user: UserOut
    status: str
    created_at: datetime

class FriendOut(BaseModel):
    id: int
    friend: UserOut
    created_at: datetime