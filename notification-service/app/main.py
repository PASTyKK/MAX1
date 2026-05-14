from fastapi import FastAPI
import redis.asyncio as redis
import asyncio
import json

app = FastAPI()
redis_client = redis.from_url("redis://localhost:6379")

async def notification_worker():
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("notifications")
    async for message in pubsub.listen():
        if message["type"] == "message":
            data = json.loads(message["data"])
            print(f"🔔 Уведомление: новое сообщение в чате {data['chat_id']} от {data['sender_id']}: {data['message']}")

@app.on_event("startup")
async def start_worker():
    asyncio.create_task(notification_worker())

@app.get("/health")
async def health():
    return {"status": "ok"}