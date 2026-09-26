from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from backend.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    
    # User's default native spoken language (e.g. 'so', 'en', 'ar')
    native_language = Column(String(20), default="so")
    
    # User's default listening/target language (e.g. 'so', 'en', 'ar')
    target_language = Column(String(20), default="so")
    
    # Preferred voice gender ('male' or 'female')
    preferred_voice = Column(String(10), default="male")
    
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    call_records = relationship("CallRecord", back_populates="creator")


class Friendship(Base):
    __tablename__ = "friendships"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    friend_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="accepted")  # 'pending', 'accepted'
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=True)
    source_lang = Column(String(20), default="so")
    target_lang = Column(String(20), default="en")
    created_at = Column(DateTime, default=datetime.utcnow)


class CallRecord(Base):
    __tablename__ = "call_records"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String(64), index=True, nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    call_type = Column(String(20), default="voice")  # 'voice' or 'video'
    status = Column(String(20), default="active")    # 'active', 'ended'
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    creator = relationship("User", back_populates="call_records")
