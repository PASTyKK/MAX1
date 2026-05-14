from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, ForeignKey, Boolean, DateTime, func
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)

class Friend(Base):
    __tablename__ = "friends"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)          # кто добавил
    friend_id = Column(Integer, nullable=False)        # на кого добавил
    created_at = Column(DateTime, default=datetime.utcnow)

# Таблица заявок в друзья
class FriendRequest(Base):
    __tablename__ = "friend_requests"
    id = Column(Integer, primary_key=True)
    from_user_id = Column(Integer, nullable=False)
    to_user_id = Column(Integer, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)