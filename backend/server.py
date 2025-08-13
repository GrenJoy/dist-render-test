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

# WebRTC Signaling and Chat
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[Dict]] = {}  # room_id -> list of {websocket, user_id, username}
        self.connection_users: Dict[WebSocket, Dict] = {}  # websocket -> {room_id, user_id, username}

    async def connect(self, websocket: WebSocket, room_id: str, user_id: str, username: str):
        await websocket.accept()
        
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        
        user_data = {
            'websocket': websocket,
            'user_id': user_id,
            'username': username,
            'is_in_voice': False
        }
        
        self.active_connections[room_id].append(user_data)
        self.connection_users[websocket] = {
            'room_id': room_id,
            'user_id': user_id,
            'username': username
        }
        
        # Update user status in database
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"is_online": True, "username": username}},
            upsert=True
        )
        
        # Notify others in room about new connection  
        await self.broadcast_to_room(room_id, {
            "type": "user_joined",
            "room_id": room_id,
            "user": {
                "id": user_id,
                "username": username,
                "is_in_voice": False
            },
            "total_users": len(self.active_connections[room_id])
        }, exclude=websocket)

    def disconnect(self, websocket: WebSocket):
        user_data = self.connection_users.get(websocket)
        if user_data:
            room_id = user_data['room_id']
            if room_id in self.active_connections:
                # Remove user from room
                self.active_connections[room_id] = [
                    conn for conn in self.active_connections[room_id] 
                    if conn['websocket'] != websocket
                ]
                
                # Clean up empty rooms
                if not self.active_connections[room_id]:
                    del self.active_connections[room_id]
                    
            del self.connection_users[websocket]
            return user_data
        return None

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except:
            pass

    async def broadcast_to_room(self, room_id: str, message: dict, exclude: WebSocket = None):
        if room_id in self.active_connections:
            for connection_data in self.active_connections[room_id]:
                connection = connection_data['websocket']
                if connection != exclude:
                    try:
                        await connection.send_text(json.dumps(message))
                    except:
                        pass

    def get_room_users(self, room_id: str):
        if room_id in self.active_connections:
            return [
                {
                    "id": conn['user_id'],
                    "username": conn['username'],
                    "is_in_voice": conn.get('is_in_voice', False)
                }
                for conn in self.active_connections[room_id]
            ]
        return []

    async def update_voice_status(self, room_id: str, user_id: str, is_in_voice: bool):
        if room_id in self.active_connections:
            for conn in self.active_connections[room_id]:
                if conn['user_id'] == user_id:
                    conn['is_in_voice'] = is_in_voice
                    break

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
    
    # Get active users
    active_users = manager.get_room_users(room_id)
    room["active_users"] = len(active_users)
    room["users"] = active_users
    
    return room

@api_router.get("/rooms")
async def get_rooms():
    rooms = await db.rooms.find().to_list(100)
    for room in rooms:
        # Convert ObjectId to string and remove it
        if "_id" in room:
            del room["_id"]
        active_users = manager.get_room_users(room["id"])
        room["active_users"] = len(active_users)
        room["users"] = active_users
    return rooms

# Chat endpoints
@api_router.get("/rooms/{room_id}/messages")
async def get_room_messages(room_id: str, limit: int = 50):
    messages = await db.messages.find({"room_id": room_id}).sort("timestamp", -1).limit(limit).to_list(limit)
    for message in messages:
        if "_id" in message:
            del message["_id"]
    return {"messages": list(reversed(messages))}

@api_router.post("/rooms/{room_id}/messages")
async def send_message(room_id: str, message_data: dict):
    chat_message = ChatMessage(
        room_id=room_id,
        user_id=message_data.get("user_id"),
        username=message_data.get("username"),
        message=message_data.get("message"),
        message_type=message_data.get("message_type", "text")
    )
    
    # Save to database
    message_dict = chat_message.dict()
    await db.messages.insert_one(message_dict)
    
    # Remove _id for response
    if "_id" in message_dict:
        del message_dict["_id"]
    
    # Broadcast to room via WebSocket
    await manager.broadcast_to_room(room_id, {
        "type": "new_message",
        "message": message_dict
    })
    
    return message_dict

@api_router.post("/rooms/{room_id}/upload")
async def upload_file(room_id: str, file: UploadFile = File(...), user_id: str = Form(...), username: str = Form(...)):
    # Validate file type
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Неподдерживаемый тип файла")
    
    # Generate unique filename
    file_extension = file.filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = uploads_dir / unique_filename
    
    # Save file
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка при сохранении файла")
    
    # Create message with file
    file_url = f"/uploads/{unique_filename}"
    chat_message = ChatMessage(
        room_id=room_id,
        user_id=user_id,
        username=username,
        message=f"Отправил изображение: {file.filename}",
        message_type="image",
        file_url=file_url
    )
    
    # Save to database
    message_dict = chat_message.dict()
    await db.messages.insert_one(message_dict)
    
    # Remove _id for response
    if "_id" in message_dict:
        del message_dict["_id"]
    
    # Broadcast to room
    await manager.broadcast_to_room(room_id, {
        "type": "new_message",
        "message": message_dict
    })
    
    return message_dict

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