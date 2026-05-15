from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import chats, messages
from .db import engine
from .models import Base

app = FastAPI(title="Chat API Gateway")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(chats.router)
app.include_router(messages.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        ssl_keyfile="localhost+2-key.pem",
        ssl_certfile="localhost+2.pem"
    )