from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, or_, and_
from .db import get_db, engine
from .models import Base, User, Friend, FriendRequest
from .schemas import UserCreate, Token, UserOut
from .auth import verify_password, hash_password, create_access_token
from jose import JWTError, jwt
import os
from datetime import datetime

SECRET_KEY = "my_super_secret_key_change_me"
ALGORITHM = "HS256"
security = HTTPBearer()

app = FastAPI(title="User Service")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Вспомогательные утилиты

@app.on_event("startup")
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# регистрация и логин, а забыли пароль я забыл(
@app.post("/register", response_model=Token, summary="Регистрация пользователя")
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.username == user.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username taken")
    new_user = User(username=user.username, hashed_password=hash_password(user.password))
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    token = create_access_token({"sub": str(new_user.id), "username": new_user.username})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/login", response_model=Token, summary="Авторизация (вход)")
async def login(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await db.execute(select(User).where(User.username == user.username))
    db_user = db_user.scalar_one_or_none()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(db_user.id), "username": db_user.username})
    return {"access_token": token, "token_type": "bearer"}

# верификация токена
@app.get("/auth/verify", summary="Проверка JWT-токена (для API Gateway)")
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        username = payload.get("username")
        if user_id is None:
            raise JWTError
        return {"user_id": int(user_id), "username": username}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Список всех пользователей
@app.get("/users", summary="Получить список всех пользователей")
async def get_all_users(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    token = credentials.credentials
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    result = await db.execute(select(User.id, User.username))
    users = [{"id": row[0], "username": row[1]} for row in result.all()]
    return users

# Поиск пользователей
@app.get("/users/search", summary="Поиск пользователей по логину")
async def search_users(
    q: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        current_id = int(payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    if not q or len(q) < 1:
        return []
    result = await db.execute(
        select(User.id, User.username).where(
            User.username.ilike(f"%{q}%"),
            User.id != current_id
        ).limit(20)
    )
    users = [{"id": row[0], "username": row[1]} for row in result.all()]
    return users

# Отправить заявку в друзья
@app.post("/friends/request/{user_id}", summary="Отправить заявку в друзья")
async def send_friend_request(
    user_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        current_id = int(payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    if current_id == user_id:
        raise HTTPException(status_code=400, detail="Нельзя добавить себя")

    existing = await db.execute(
        select(FriendRequest).where(
            or_(
                and_(FriendRequest.from_user_id == current_id, FriendRequest.to_user_id == user_id),
                and_(FriendRequest.from_user_id == user_id, FriendRequest.to_user_id == current_id)
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Заявка уже отправлена")

    friend_exists = await db.execute(
        select(Friend).where(
            or_(
                and_(Friend.user_id == current_id, Friend.friend_id == user_id),
                and_(Friend.user_id == user_id, Friend.friend_id == current_id)
            )
        )
    )
    if friend_exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Уже друзья")

    new_request = FriendRequest(from_user_id=current_id, to_user_id=user_id, status="pending")
    db.add(new_request)
    await db.commit()
    return {"message": "Заявка отправлена"}

# Входящие заявки в друзья
@app.get("/friends/requests/incoming", summary="Получить входящие заявки")
async def get_incoming_requests(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        current_id = int(payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(
        select(FriendRequest).where(FriendRequest.to_user_id == current_id, FriendRequest.status == "pending")
    )
    requests = result.scalars().all()
    output = []
    for req in requests:
        from_user = await db.execute(select(User).where(User.id == req.from_user_id))
        from_user = from_user.scalar_one()
        output.append({
            "id": req.id,
            "from_user": {"id": from_user.id, "username": from_user.username},
            "status": req.status,
            "created_at": req.created_at
        })
    return output

# Принять заявку
@app.post("/friends/accept/{request_id}", summary="Принять заявку в друзья")
async def accept_friend_request(
    request_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        current_id = int(payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    req = await db.execute(select(FriendRequest).where(FriendRequest.id == request_id))
    req = req.scalar_one_or_none()
    if not req or req.to_user_id != current_id or req.status != "pending":
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    friend1 = Friend(user_id=req.from_user_id, friend_id=req.to_user_id)
    friend2 = Friend(user_id=req.to_user_id, friend_id=req.from_user_id)
    db.add_all([friend1, friend2])
    req.status = "accepted"
    await db.commit()
    return {"message": "Друг добавлен"}

# Список друзей
@app.get("/friends", summary="Список друзей текущего пользователя")
async def get_friends(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        current_id = int(payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(Friend).where(Friend.user_id == current_id))
    friends = result.scalars().all()
    output = []
    for f in friends:
        friend_user = await db.execute(select(User).where(User.id == f.friend_id))
        friend_user = friend_user.scalar_one()
        output.append({"id": friend_user.id, "username": friend_user.username})
    return output

# Удаление друга
@app.delete("/friends/{friend_id}", summary="Удаление друга")
async def delete_friend(
    friend_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        current_id = int(payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(
        delete(Friend).where(
            or_(
                and_(Friend.user_id == current_id, Friend.friend_id == friend_id),
                and_(Friend.user_id == friend_id, Friend.friend_id == current_id)
            )
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Friend not found")
    await db.commit()
    return {"message": "Friend deleted"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        ssl_keyfile="localhost+2-key.pem",
        ssl_certfile="localhost+2.pem"
    )