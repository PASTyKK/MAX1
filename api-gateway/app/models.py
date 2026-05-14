from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# Ассоциативная таблица для участников группового чата
chat_members = Table(
    'chat_members', Base.metadata,
    Column('chat_id', Integer, ForeignKey('chats.id')),
    Column('user_id', Integer)  # user_id хранится как внешний ключ к user-service
)


class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # название группового чата
    is_private = Column(Integer, default=0)  # 0 - группа, 1 - личный чат (2 участника)
    created_by = Column(Integer)  # user_id создателя
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("Message", back_populates="chat")


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey('chats.id'))
    sender_id = Column(Integer)  # user_id отправителя
    text = Column(String, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)

    chat = relationship("Chat", back_populates="messages")