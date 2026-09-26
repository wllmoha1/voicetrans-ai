import os
import uuid
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.config import BASE_DIR, SECRET_KEY, ALGORITHM
from backend.database import engine, get_db, Base
from backend.models import User, CallRecord
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("voice_call_app")

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Voice-to-Voice Call Translator",
    description="Real-Time Simultaneous Multilingual Voice Call Translation System",
    version="1.0.0"
)

# Enable CORS for local testing & multi-device LAN calls
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


# --- Pydantic Schemas ---
class UserRegisterSchema(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    native_language: str = "so"
    target_language: str = "en"
    preferred_voice: str = "male"


class UserLoginSchema(BaseModel):
    login: str  # Can be username or email
    password: str


class PreferencesUpdateSchema(BaseModel):
    native_language: Optional[str] = None
    target_language: Optional[str] = None
    preferred_voice: Optional[str] = None


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
    """Returns available world languages with flags and neural voices."""
    return {"languages": list(LANGUAGES.values())}


@app.post("/api/auth/register")
async def register(payload: UserRegisterSchema, db: Session = Depends(get_db)):
    # Check if username or email exists
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
    db.commit()
    db.refresh(user)
    return {"message": "Dookhyada waa la cusbooneysiiyay", "user": user}


@app.post("/api/rooms/create")
async def create_room(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Generates a random unique Room ID and saves record."""
    room_code = uuid.uuid4().hex[:8]
    call_record = CallRecord(room_id=room_code, creator_id=user.id)
    db.add(call_record)
    db.commit()
    return {"room_id": room_code, "call_url": f"/call/{room_code}"}


@app.get("/api/rooms/{room_id}/status")
async def room_status(room_id: str):
    room = room_manager.get_room(room_id)
    if not room:
        return {"exists": False, "participant_count": 0}
    return {
        "exists": True,
        "room_id": room_id,
        "participant_count": len(room.participants),
        "participants": room.get_participant_list()
    }


# --- Real-Time Call WebSocket Endpoint ---
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
    listening_lang = user.target_language if user else "en"
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
            
            # Check for WebSocket disconnect event in Starlette
            if message.get("type") == "websocket.disconnect":
                break

            # 1. Binary Audio Chunk from Microphone
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

            # 2. Text / JSON Control Messages
            elif "text" in message and message["text"]:
                import json
                try:
                    data = json.loads(message["text"])
                    msg_type = data.get("type")

                    # Heartbeat Ping to keep connection alive on Render
                    if msg_type == "ping":
                        await websocket.send_json({"type": "pong"})

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

