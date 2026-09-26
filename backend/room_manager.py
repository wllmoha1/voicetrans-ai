"""
Call Room Manager for WebSocket-based real-time call sessions.
Tracks connected participants using unique session IDs for reliable peer pairing.
"""

from typing import Dict, Optional, Any
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)

class Participant:
    def __init__(
        self,
        session_id: str,
        user_id: int,
        username: str,
        full_name: str,
        websocket: WebSocket,
        speaking_language: str = "so",
        listening_language: str = "en",
        voice_gender: str = "male"
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.username = username
        self.full_name = full_name
        self.websocket = websocket
        self.speaking_language = speaking_language
        self.listening_language = listening_language
        self.voice_gender = voice_gender
        self.is_speaking = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "username": self.username,
            "full_name": self.full_name,
            "speaking_language": self.speaking_language,
            "listening_language": self.listening_language,
            "voice_gender": self.voice_gender,
            "is_speaking": self.is_speaking
        }


class Room:
    def __init__(self, room_id: str):
        self.room_id = room_id
        # Keyed by session_id to guarantee unique entries even if same user opens 2 tabs
        self.participants: Dict[str, Participant] = {}

    def add_participant(self, participant: Participant):
        self.participants[participant.session_id] = participant

    def remove_participant(self, session_id: str) -> Optional[Participant]:
        return self.participants.pop(session_id, None)

    def get_counterpart(self, current_session_id: str) -> Optional[Participant]:
        """Gets the other participant in the room."""
        for sid, p in self.participants.items():
            if sid != current_session_id:
                return p
        return None

    def get_participant_list(self):
        return [p.to_dict() for p in self.participants.values()]


class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}

    def get_or_create_room(self, room_id: str) -> Room:
        if room_id not in self.rooms:
            self.rooms[room_id] = Room(room_id)
        return self.rooms[room_id]

    def get_room(self, room_id: str) -> Optional[Room]:
        return self.rooms.get(room_id)

    def join_room(self, room_id: str, participant: Participant) -> Room:
        room = self.get_or_create_room(room_id)
        room.add_participant(participant)
        logger.info(f"Session {participant.session_id} ({participant.full_name}) joined room {room_id}. Total: {len(room.participants)}")
        return room

    def leave_room(self, room_id: str, session_id: str):
        room = self.get_room(room_id)
        if room:
            room.remove_participant(session_id)
            logger.info(f"Session {session_id} left room {room_id}. Remaining: {len(room.participants)}")
            if len(room.participants) == 0:
                del self.rooms[room_id]
                logger.info(f"Room {room_id} deleted because it became empty.")

    async def broadcast_json(self, room_id: str, data: dict, exclude_session_id: Optional[str] = None):
        """Sends a JSON message to all participants in a room."""
        room = self.get_room(room_id)
        if not room:
            return

        for sid, p in list(room.participants.items()):
            if exclude_session_id is not None and sid == exclude_session_id:
                continue
            try:
                await p.websocket.send_json(data)
            except Exception as e:
                logger.warning(f"Failed to send JSON to session {sid} in room {room_id}: {e}")

    async def send_audio_bytes(self, websocket: WebSocket, audio_bytes: bytes):
        """Sends binary audio bytes to a specific participant."""
        try:
            await websocket.send_bytes(audio_bytes)
        except Exception as e:
            logger.warning(f"Failed to send audio bytes to participant: {e}")


room_manager = RoomManager()
