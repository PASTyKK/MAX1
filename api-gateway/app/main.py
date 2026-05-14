from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware   # импортируем CORS
from .routers import chats, messages
from .db import engine
from .models import Base

# 1. Сначала создаём экземпляр приложения
app = FastAPI(title="Chat API Gateway")

# 2. Затем добавляем middleware (CORS) — обязательно ПОСЛЕ создания app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Инициализация БД при старте
@app.on_event("startup")
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 4. Подключаем роутеры
app.include_router(chats.router)
app.include_router(messages.router)