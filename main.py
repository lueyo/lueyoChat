from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from service.chatService import ChatService
import datetime

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chat_service = ChatService()

@app.websocket("/ws")
async def websocket_root(websocket: WebSocket):
    await chat_service.handle_websocket(websocket, "root")

@app.websocket("/ws/{room_uuid}")
async def websocket_endpoint(websocket: WebSocket, room_uuid: str):
    await chat_service.handle_websocket(websocket, room_uuid)

@app.get("/ping")
async def pong():
    return {"ping": "pong"}
