from jose import JWTError, jwt
from datetime import datetime, timedelta
import bcrypt
import os

SECRET_KEY = "my_super_secret_key_change_me"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def verify_password(plain, hashed):
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def hash_password(pwd):
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)