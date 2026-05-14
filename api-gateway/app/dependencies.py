import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

USER_SERVICE_URL = "http://localhost:8001"   # ← обязательно localhost, порт 8001

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{USER_SERVICE_URL}/auth/verify",
            headers={"Authorization": f"Bearer {token}"}
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return resp.json()