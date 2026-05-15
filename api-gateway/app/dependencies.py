import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

USER_SERVICE_URL = "https://localhost:8001"   # обязательно https
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    async with httpx.AsyncClient(verify=False) as client:   # отключаем проверку сертификата для локального теста
        resp = await client.get(
            f"{USER_SERVICE_URL}/auth/verify",
            headers={"Authorization": f"Bearer {token}"}
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_data = resp.json()
    user_data["token"] = token
    return user_data