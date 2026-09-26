import os
import sys
import uuid
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# Automatically ensure project root is in sys.path so "Run" button in VS Code works directly
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from backend.config import BASE_DIR, SECRET_KEY, ALGORITHM
from backend.database import engine, get_db, Base, init_db
from backend.models import User, CallRecord, Friendship, ChatMessage
from backend.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    get_current_user_from_token
)
from backend.services.language_catalog import LANGUAGES
from backend.room_manager import room_manager, Participant
from backend.audio_pipeline import audio_pipeline
from backend.services.translation import TranslationService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("voice_call_app")

# Initialize database tables and run automatic migrations
init_db()

app = FastAPI(
    title="VoiceTrans AI - Professional Call & Social Translation App",
    description="Real-Time Multilingual WebRTC Calls, Friends, Chat & AI Translation",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = BASE_DIR / "frontend"

# Mount static directories
app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")

# Active user signaling connections for direct calling & real-time chat
active_user_signals: Dict[int, WebSocket] = {}
translation_service = TranslationService()


# --- Pydantic Schemas ---
class UserRegisterSchema(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    native_language: str = "so"
    target_language: str = "so"
    preferred_voice: str = "male"


class UserLoginSchema(BaseModel):
    login: str  # Can be username or email
    password: str


class PreferencesUpdateSchema(BaseModel):
    native_language: Optional[str] = None
    target_language: Optional[str] = None
    preferred_voice: Optional[str] = None
    full_name: Optional[str] = None


class AddFriendSchema(BaseModel):
    target_username: str


class SendChatMessageSchema(BaseModel):
    receiver_id: int
    text: str
    target_language: Optional[str] = None


# --- Web Page Routes ---
@app.get("/")
async def index_page():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/login")
async def login_page():
    return FileResponse(FRONTEND_DIR / "login.html")

@app.get("/register")
async def register_page():
    return FileResponse(FRONTEND_DIR / "register.html")

@app.get("/dashboard")
async def dashboard_page():
    return FileResponse(FRONTEND_DIR / "dashboard.html")

@app.get("/call/{room_id}")
async def call_page(room_id: str):
    return FileResponse(FRONTEND_DIR / "call.html")


# --- REST API Endpoints ---
@app.get("/api/languages")
async def get_languages():
    return {"languages": list(LANGUAGES.values())}


@app.post("/api/auth/register")
async def register(payload: UserRegisterSchema, db: Session = Depends(get_db)):
    existing = db.query(User).filter(
        (User.username == payload.username.strip().lower()) | 
        (User.email == payload.email.strip().lower())
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Magacan ama Email-kan mar hore ayaa la diiwaangeliyay.")

    hashed_pw = hash_password(payload.password)
    user = User(
        username=payload.username.strip().lower(),
        email=payload.email.strip().lower(),
        hashed_password=hashed_pw,
        full_name=payload.full_name.strip() if payload.full_name else payload.username,
        native_language=payload.native_language,
        target_language=payload.target_language,
        preferred_voice=payload.preferred_voice
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.username})
    return {
        "message": "Si guul leh ayaad isu diiwaangelisay!",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "native_language": user.native_language,
            "target_language": user.target_language,
            "preferred_voice": user.preferred_voice
        }
    }


@app.post("/api/auth/login")
async def login(payload: UserLoginSchema, db: Session = Depends(get_db)):
    login_id = payload.login.strip().lower()
    user = db.query(User).filter(
        (User.username == login_id) | (User.email == login_id)
    ).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email/Username ama Password-ka waa khalad."
        )

    token = create_access_token({"sub": user.username})
    return {
        "message": "Si guul leh ayaad u soo gashay!",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "native_language": user.native_language,
            "target_language": user.target_language,
            "preferred_voice": user.preferred_voice
        }
    }


@app.get("/api/auth/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "native_language": user.native_language,
        "target_language": user.target_language,
        "preferred_voice": user.preferred_voice
    }


@app.put("/api/auth/preferences")
async def update_preferences(
    payload: PreferencesUpdateSchema, 
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if payload.native_language:
        user.native_language = payload.native_language
    if payload.target_language:
        user.target_language = payload.target_language
    if payload.preferred_voice:
        user.preferred_voice = payload.preferred_voice
    if payload.full_name:
        user.full_name = payload.full_name
    db.commit()
    db.refresh(user)
    return {"message": "Dookhyada waa la cusbooneysiiyay", "user": user}


# --- Friends & Social System ---
@app.get("/api/users/search")
async def search_users(q: str = Query("", min_length=1), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    users = db.query(User).filter(
        User.id != current_user.id,
        or_(
            User.username.ilike(f"%{q}%"),
            User.full_name.ilike(f"%{q}%")
        )
    ).limit(15).all()

    # Get friendship status for each
    results = []
    for u in users:
        is_friend = db.query(Friendship).filter(
            or_(
                and_(Friendship.user_id == current_user.id, Friendship.friend_id == u.id),
                and_(Friendship.user_id == u.id, Friendship.friend_id == current_user.id)
            )
        ).first() is not None

        results.append({
            "id": u.id,
            "username": u.username,
            "full_name": u.full_name,
            "native_language": u.native_language,
            "is_friend": is_friend
        })
    return {"users": results}


@app.get("/api/friends")
async def get_friends(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    friendships = db.query(Friendship).filter(
        or_(
            Friendship.user_id == current_user.id,
            Friendship.friend_id == current_user.id
        )
    ).all()

    friend_ids = set()
    for f in friendships:
        fid = f.friend_id if f.user_id == current_user.id else f.user_id
        friend_ids.add(fid)

    friends = db.query(User).filter(User.id.in_(friend_ids)).all() if friend_ids else []
    return {
        "friends": [
            {
                "id": f.id,
                "username": f.username,
                "full_name": f.full_name,
                "native_language": f.native_language,
                "target_language": f.target_language,
                "is_online": f.id in active_user_signals
            }
            for f in friends
        ]
    }


@app.post("/api/friends/add")
async def add_friend(payload: AddFriendSchema, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    target = db.query(User).filter(User.username == payload.target_username.strip().lower()).first()
    if not target:
        raise HTTPException(status_code=404, detail="Qofkaas lama helin.")
    if target.id == current_user.id:
        raise HTTPException(status_code=400, detail="Isu dari maysid naftaada.")

    existing = db.query(Friendship).filter(
        or_(
            and_(Friendship.user_id == current_user.id, Friendship.friend_id == target.id),
            and_(Friendship.user_id == target.id, Friendship.friend_id == current_user.id)
        )
    ).first()

    if not existing:
        friendship = Friendship(user_id=current_user.id, friend_id=target.id, status="accepted")
        db.add(friendship)
        db.commit()

        # Notify target if online
        if target.id in active_user_signals:
            try:
                await active_user_signals[target.id].send_json({
                    "type": "new_friend",
                    "friend": {
                        "id": current_user.id,
                        "username": current_user.username,
                        "full_name": current_user.full_name
                    }
                })
            except Exception:
                pass

    return {"message": f"{target.full_name or target.username} waa laguugu daray asxaabtaada!"}


# --- 1-on-1 Chat with Auto-Translate ---
@app.get("/api/chat/{friend_id}")
async def get_chat_history(friend_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    messages = db.query(ChatMessage).filter(
        or_(
            and_(ChatMessage.sender_id == current_user.id, ChatMessage.receiver_id == friend_id),
            and_(ChatMessage.sender_id == friend_id, ChatMessage.receiver_id == current_user.id)
        )
    ).order_by(ChatMessage.created_at.asc()).limit(60).all()

    return {
        "messages": [
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "receiver_id": m.receiver_id,
                "original_text": m.original_text,
                "translated_text": m.translated_text,
                "source_lang": m.source_lang,
                "target_lang": m.target_lang,
                "created_at": m.created_at.isoformat(),
                "is_me": m.sender_id == current_user.id
            }
            for m in messages
        ]
    }


@app.post("/api/chat/send")
async def send_chat_message(payload: SendChatMessageSchema, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    receiver = db.query(User).filter(User.id == payload.receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Qofka fariinta loo dirayo lama helin.")

    source_lang = current_user.native_language or "so"
    target_lang = payload.target_language or receiver.native_language or "en"

    # Translate text
    translated = await translation_service.translate_text(payload.text, source_lang, target_lang)

    msg = ChatMessage(
        sender_id=current_user.id,
        receiver_id=receiver.id,
        original_text=payload.text,
        translated_text=translated,
        source_lang=source_lang,
        target_lang=target_lang
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    msg_data = {
        "id": msg.id,
        "sender_id": msg.sender_id,
        "sender_name": current_user.full_name or current_user.username,
        "receiver_id": msg.receiver_id,
        "original_text": msg.original_text,
        "translated_text": msg.translated_text,
        "source_lang": msg.source_lang,
        "target_lang": msg.target_lang,
        "created_at": msg.created_at.isoformat()
    }

    # If receiver is online on signaling socket, send instant push message
    if receiver.id in active_user_signals:
        try:
            await active_user_signals[receiver.id].send_json({
                "type": "chat_message",
                "message": msg_data
            })
        except Exception:
            pass

    return {"message": "Fariinta waa la diray", "data": msg_data}


# --- Call Management ---
@app.post("/api/rooms/create")
async def create_room(
    call_type: str = "voice",
    user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    room_code = uuid.uuid4().hex[:8]
    call_record = CallRecord(room_id=room_code, creator_id=user.id, call_type=call_type)
    db.add(call_record)
    db.commit()
    return {"room_id": room_code, "call_url": f"/call/{room_code}?type={call_type}"}


# --- User Personal Signaling Socket (Direct Calling & Ringing) ---
@app.websocket("/ws/signal/{user_id}")
async def signaling_websocket(websocket: WebSocket, user_id: int):
    await websocket.accept()
    active_user_signals[user_id] = websocket
    logger.info(f"User {user_id} connected to personal signaling socket.")

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif msg_type == "call_user":
                # Ring another user: caller -> target
                target_id = data.get("target_id")
                if target_id and target_id in active_user_signals:
                    await active_user_signals[target_id].send_json({
                        "type": "incoming_call",
                        "caller_id": user_id,
                        "caller_name": data.get("caller_name", "Saaxiib"),
                        "room_id": data.get("room_id"),
                        "call_type": data.get("call_type", "voice")
                    })

    except WebSocketDisconnect:
        pass
    finally:
        active_user_signals.pop(user_id, None)
        logger.info(f"User {user_id} signaling socket disconnected.")


# --- WebRTC Call Room & AI Translation WebSocket Hub ---
@app.websocket("/ws/call/{room_id}")
async def call_websocket(
    websocket: WebSocket,
    room_id: str,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    await websocket.accept()

    session_id = uuid.uuid4().hex[:8]

    # Authenticate user from query token or fallback to guest caller
    user: Optional[User] = None
    if token:
        user = get_current_user_from_token(token, db)
    
    user_id = user.id if user else int(uuid.uuid4().int % 1000000)
    username = user.username if user else f"caller_{user_id}"
    full_name = user.full_name if user else f"Wacade {user_id}"
    speaking_lang = user.native_language if user else "so"
    listening_lang = user.target_language if user else "so"
    voice_gender = user.preferred_voice if user else "male"

    participant = Participant(
        session_id=session_id,
        user_id=user_id,
        username=username,
        full_name=full_name,
        websocket=websocket,
        speaking_language=speaking_lang,
        listening_language=listening_lang,
        voice_gender=voice_gender
    )

    room = room_manager.join_room(room_id, participant)

    # 1. Send direct init message to this connecting client
    await websocket.send_json({
        "type": "init",
        "my_session_id": session_id,
        "my_participant": participant.to_dict(),
        "participants": room.get_participant_list()
    })

    # 2. Broadcast to other participants that a new peer joined
    await room_manager.broadcast_json(room_id, {
        "type": "peer_joined",
        "peer": participant.to_dict(),
        "participants": room.get_participant_list()
    }, exclude_session_id=session_id)

    logger.info(f"WebSocket session {session_id} connected: User {username} in room {room_id}")

    try:
        while True:
            message = await websocket.receive()
            
            if message.get("type") == "websocket.disconnect":
                break

            # 1. Binary Audio Chunk from Microphone (AI speech-to-speech translation)
            if "bytes" in message and message["bytes"]:
                audio_bytes = message["bytes"]
                asyncio.create_task(
                    audio_pipeline.process_speech_chunk(
                        room_id=room_id,
                        speaker=participant,
                        audio_bytes=audio_bytes,
                        audio_format="webm"
                    )
                )

            # 2. Text / JSON Control Messages (WebRTC Signaling, Heartbeat & Controls)
            elif "text" in message and message["text"]:
                import json
                try:
                    data = json.loads(message["text"])
                    msg_type = data.get("type")

                    # Keep-alive heartbeat (ensures Render never disconnects idle call)
                    if msg_type == "ping":
                        await websocket.send_json({"type": "pong"})

                    # WebRTC Direct Audio/Video Signaling Relay (Offer, Answer, ICE)
                    elif msg_type in ["webrtc_offer", "webrtc_answer", "webrtc_ice"]:
                        data["sender_session_id"] = participant.session_id
                        await room_manager.broadcast_json(room_id, data, exclude_session_id=participant.session_id)

                    elif msg_type == "speaking_state":
                        participant.is_speaking = data.get("is_speaking", False)
                        await room_manager.broadcast_json(room_id, {
                            "type": "peer_speaking",
                            "session_id": participant.session_id,
                            "user_id": participant.user_id,
                            "is_speaking": participant.is_speaking
                        }, exclude_session_id=participant.session_id)

                    elif msg_type == "update_languages":
                        if "speaking_language" in data:
                            participant.speaking_language = data["speaking_language"]
                        if "listening_language" in data:
                            participant.listening_language = data["listening_language"]
                        if "voice_gender" in data:
                            participant.voice_gender = data["voice_gender"]

                        await room_manager.broadcast_json(room_id, {
                            "type": "languages_updated",
                            "peer": participant.to_dict(),
                            "participants": room.get_participant_list()
                        })

                    elif msg_type == "leave_call":
                        break

                except Exception as e:
                    logger.error(f"Error parsing incoming JSON message: {e}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: Session {session_id} from room {room_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
    finally:
        room_manager.leave_room(room_id, participant.session_id)
        # Notify counterpart
        await room_manager.broadcast_json(room_id, {
            "type": "peer_left",
            "session_id": participant.session_id,
            "user_id": participant.user_id,
            "username": participant.username,
            "participants": room.get_participant_list()
        })


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print("\n" + "=" * 60)
    print(f"[*] VoiceTrans Server is starting locally:")
    print(f"[*] Open in browser: http://localhost:{port}")
    print("=" * 60 + "\n")
    uvicorn.run("backend.app:app", host="0.0.0.0", port=port, reload=True)

