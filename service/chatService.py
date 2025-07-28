from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel


class RoomModel(BaseModel):
    uuid: str
    connected_users: int


class ChatService:
    def __init__(self):
        # Dictionary mapping room UUID to set of WebSocket connections
        self.rooms: Dict[str, Set[WebSocket]] = {}

    async def connect(self, room_uuid: str, websocket: WebSocket):
        if room_uuid not in self.rooms:
            self.rooms[room_uuid] = set()
        self.rooms[room_uuid].add(websocket)

    def disconnect(self, room_uuid: str, websocket: WebSocket):
        if room_uuid in self.rooms:
            self.rooms[room_uuid].discard(websocket)
            if not self.rooms[room_uuid]:
                # Remove room if no connections left
                del self.rooms[room_uuid]

    async def broadcast(self, room_uuid: str, message: dict, sender_websocket: WebSocket):
        if room_uuid in self.rooms:
            for connection in self.rooms[room_uuid]:
                if connection != sender_websocket:
                    await connection.send_json(message)

    async def handle_websocket(self, websocket: WebSocket, room_uuid: str):
        await websocket.accept()
        await self.connect(room_uuid, websocket)
        try:
            while True:
                try:
                    data = await websocket.receive_json()
                    username = data.get("username", "anon")
                    content = data.get("content")
                    timestamp = data.get("timestamp")
                    color = data.get("color", "#11BC61")
                    if content is None or timestamp is None:
                        continue  # Ignore messages without content or timestamp
                    message = {
                        "timestamp": timestamp,
                        "username": username,
                        "color": color,
                        "content": content
                    }
                    await self.broadcast(room_uuid, message, websocket)
                except ValueError:
                    await websocket.send_text("Error: Invalid JSON received.")
                except Exception as e:
                    await websocket.send_text(f"Error: {str(e)}")
        except WebSocketDisconnect:
            self.disconnect(room_uuid, websocket)
        except Exception as e:
            self.disconnect(room_uuid, websocket)
            print(f"Error: {str(e)}")
