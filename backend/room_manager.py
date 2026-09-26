"""
Call Room Manager for WebSocket-based real-time call sessions.
Tracks connected participants, their selected languages, and audio streaming routes.
"""

from typing import Dict, Optional, Any
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)

class Participant:
    def __init__(
        self,
        user_id: int,
        username: str,
        full_name: str,
        websocket: WebSocket,
        speaking_language: str = "so",
        listening_language: str = "en",
        voice_gender: str = "male"
    ):
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
        self.participants: Dict[int, Participant] = {}

    def add_participant(self, participant: Participant):
        self.participants[participant.user_id] = participant

    def remove_participant(self, user_id: int) -> Optional[Participant]:
        return self.participants.pop(user_id, None)

    def get_counterpart(self, current_user_id: int) -> Optional[Participant]:
        """In a 2-person call, gets the other participant."""
        for uid, p in self.participants.items():
            if uid != current_user_id:
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
        logger.info(f"User {participant.username} (ID: {participant.user_id}) joined room {room_id}")
        return room

    def leave_room(self, room_id: str, user_id: int):
        room = self.get_room(room_id)
        if room:
            room.remove_participant(user_id)
            logger.info(f"User ID {user_id} left room {room_id}")
            if len(room.participants) == 0:
                del self.rooms[room_id]
                logger.info(f"Room {room_id} deleted because it became empty.")

    async def broadcast_json(self, room_id: str, data: dict, exclude_user_id: Optional[int] = None):
        """Sends a JSON message to all participants in a room."""
        room = self.get_room(room_id)
        if not room:
            return

        for uid, p in list(room.participants.items()):
            if exclude_user_id is not None and uid == exclude_user_id:
                continue
            try:
                await p.websocket.send_json(data)
            except Exception as e:
                logger.warning(f"Failed to send JSON to user {uid} in room {room_id}: {e}")

    async def send_audio_bytes(self, websocket: WebSocket, audio_bytes: bytes):
        """Sends binary audio bytes to a specific participant."""
        try:
            await websocket.send_bytes(audio_bytes)
        except Exception as e:
            logger.warning(f"Failed to send audio bytes to participant: {e}")


room_manager = RoomManager()
