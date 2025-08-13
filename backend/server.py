from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import json
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import uuid
from datetime import datetime
import aiofiles
import shutil

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create uploads directory
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)

# Create the main app without a prefix
app = FastAPI()

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Pydantic models
class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    room_id: str
    user_id: str
    username: str
    message: str
    message_type: str = "text"  # text, image, file
    file_url: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    avatar_url: Optional[str] = None
    is_online: bool = True
    is_in_voice: bool = False

# WebRTC Signaling
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}  # room_id -> list of websockets
        self.connection_rooms: Dict[WebSocket, str] = {}  # websocket -> room_id

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        
        self.active_connections[room_id].append(websocket)
        self.connection_rooms[websocket] = room_id
        
        # Notify others in room about new connection
        await self.broadcast_to_room(room_id, {
            "type": "user_joined",
            "room_id": room_id,
            "total_users": len(self.active_connections[room_id])
        }, exclude=websocket)

    def disconnect(self, websocket: WebSocket):
        room_id = self.connection_rooms.get(websocket)
        if room_id and room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
            if websocket in self.connection_rooms:
                del self.connection_rooms[websocket]
            
            # Clean up empty rooms
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except:
            pass

    async def broadcast_to_room(self, room_id: str, message: dict, exclude: WebSocket = None):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                if connection != exclude:
                    try:
                        await connection.send_text(json.dumps(message))
                    except:
                        pass

manager = ConnectionManager()

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Voice Chat API"}

@api_router.get("/health")
async def health_check():
    try:
        # Test MongoDB connection
        await db.command("ping")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@api_router.post("/rooms")
async def create_room(room_data: dict):
    # Check if room already exists
    existing_room = await db.rooms.find_one({"id": room_data.get("id")})
    if existing_room:
        # Return existing room
        if "_id" in existing_room:
            del existing_room["_id"]
        existing_room["active_users"] = len(manager.active_connections.get(existing_room["id"], []))
        return existing_room
    
    # Create new room
    room = {
        "id": room_data.get("id", str(uuid.uuid4())),
        "name": room_data.get("name", "New Room"),
        "created_at": datetime.utcnow(),
        "active_users": 0
    }
    await db.rooms.insert_one(room)
    
    # Return room without ObjectId
    if "_id" in room:
        del room["_id"]
    return room

@api_router.get("/rooms/{room_id}")
async def get_room(room_id: str):
    room = await db.rooms.find_one({"id": room_id})
    if not room:
        return {"error": "Room not found"}
    
    # Convert ObjectId to string and remove it
    if "_id" in room:
        del room["_id"]
    
    # Count active connections
    active_users = len(manager.active_connections.get(room_id, []))
    room["active_users"] = active_users
    
    return room

@api_router.get("/rooms")
async def get_rooms():
    rooms = await db.rooms.find().to_list(100)
    for room in rooms:
        # Convert ObjectId to string and remove it
        if "_id" in room:
            del room["_id"]
        room["active_users"] = len(manager.active_connections.get(room["id"], []))
    return rooms

# WebSocket endpoint for signaling
@api_router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Forward signaling messages to other peers in the room
            if message.get("type") in ["offer", "answer", "ice-candidate"]:
                await manager.broadcast_to_room(room_id, message, exclude=websocket)
            elif message.get("type") == "join":
                # Send current room info
                room_info = await get_room(room_id)
                await manager.send_personal_message({
                    "type": "room_info",
                    "data": room_info
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        # Notify others about user leaving
        if room_id in manager.active_connections:
            await manager.broadcast_to_room(room_id, {
                "type": "user_left",
                "room_id": room_id,
                "total_users": len(manager.active_connections[room_id])
            })

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()