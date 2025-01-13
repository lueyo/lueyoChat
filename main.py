from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import datetime

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lista para almacenar conexiones activas
connections: List[WebSocket] = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.append(websocket)
    try:
        while True:
            try:
                data = await websocket.receive_json()
                username = data.get("username", "anon")
                content = data.get("content")
                timestamp = data.get("timestamp")
                if content is None or timestamp is None:
                    continue  # Ignorar mensajes sin contenido o sin timestamp
                # Convertir el timestamp numérico a una cadena legible
                timestamp_str = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                message = f"{timestamp_str} - {username}: {content}"
                # Enviar el mensaje a todos los clientes conectados
                for connection in connections:
                    if connection != websocket:
                        await connection.send_text(message)
            except ValueError:
                await websocket.send_text("Error: Invalid JSON received.")
            except Exception as e:
                await websocket.send_text(f"Error: {str(e)}")
    except WebSocketDisconnect:
        connections.remove(websocket)
    except Exception as e:
        connections.remove(websocket)
        print(f"Error: {str(e)}")