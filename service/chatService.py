from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import time


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
        # Broadcast new user connected message
        connected_users = len(self.rooms[room_uuid])
        message = {
            "timestamp": str(int(time.time())),
            "username": "Room",
            "color": "#5E59EE",
            "content": f"New User connected, user online {connected_users}"
        }
        await self.broadcast_to_all(room_uuid, message)

    def disconnect(self, room_uuid: str, websocket: WebSocket):
        if room_uuid in self.rooms:
            self.rooms[room_uuid].discard(websocket)
            connected_users = len(self.rooms[room_uuid])
            # Broadcast user disconnected message
            message = {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "username": "Room",
                "color": "#5E59EE",
                "content": f"User disconnected, user online {connected_users}"
            }
            # Since disconnect is not async, schedule broadcast asynchronously
            import asyncio
            asyncio.create_task(self.broadcast_to_all(room_uuid, message))
            if not self.rooms[room_uuid]:
                # Remove room if no connections left
                del self.rooms[room_uuid]

    async def broadcast(self, room_uuid: str, message: dict, sender_websocket: WebSocket):
        if room_uuid in self.rooms:
            for connection in self.rooms[room_uuid]:
                if connection != sender_websocket:
                    await connection.send_json(message)

    async def broadcast_to_all(self, room_uuid: str, message: dict):
        if room_uuid in self.rooms:
            for connection in self.rooms[room_uuid]:
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
