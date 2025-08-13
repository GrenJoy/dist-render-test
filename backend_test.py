#!/usr/bin/env python3
"""
Backend Testing Suite for Discord-like Voice Chat Application
Tests WebSocket signaling server, room management API, chat functionality, and file uploads
"""

import asyncio
import json
import requests
import websockets
import uuid
from datetime import datetime
import time
import os
import io
from dotenv import load_dotenv

# Try to load environment variables from different locations
env_paths = ['/app/frontend/.env', '/app/backend/.env', '/app/.env']
for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        break

# Get backend URL from environment or use default
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://voice-connect-22.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"
WS_BASE = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://') + "/api"

print(f"Testing Discord-like backend at: {API_BASE}")
print(f"Testing WebSocket at: {WS_BASE}")

class DiscordChatTester:
    def __init__(self):
        self.test_results = []
        self.created_rooms = []
        self.test_user_id = str(uuid.uuid4())
        self.test_username = "TestUser_" + str(uuid.uuid4())[:8]
        self.test_user_id_2 = str(uuid.uuid4())
        self.test_username_2 = "TestUser2_" + str(uuid.uuid4())[:8]
        
    def log_test(self, test_name, success, message="", details=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
    
    def test_health_check(self):
        """Test GET /api/health - Health check endpoint"""
        try:
            response = requests.get(f"{API_BASE}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_test("Health Check", True, f"API healthy: {data.get('database', 'unknown')} database")
                    return True
                else:
                    self.log_test("Health Check", False, f"API unhealthy: {data}")
                    return False
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Health Check", False, f"Connection error: {str(e)}")
            return False
    
    def test_api_root(self):
        """Test GET /api/ - Root API endpoint"""
        try:
            response = requests.get(f"{API_BASE}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_test("API Root", True, f"API responding: {data['message']}")
                    return True
                else:
                    self.log_test("API Root", False, "Response missing 'message' field")
                    return False
            else:
                self.log_test("API Root", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("API Root", False, f"Connection error: {str(e)}")
            return False
    
    def test_create_room(self):
        """Test POST /api/rooms - Create new room"""
        try:
            room_data = {"name": "Discord Test Room"}
            response = requests.post(f"{API_BASE}/rooms", json=room_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['id', 'name', 'created_at', 'active_users']
                
                if all(field in data for field in required_fields):
                    self.created_rooms.append(data['id'])
                    self.log_test("Create Room", True, f"Room created: {data['name']} (ID: {data['id']})")
                    return data['id']
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Create Room", False, f"Missing fields: {missing}")
                    return None
            else:
                self.log_test("Create Room", False, f"HTTP {response.status_code}: {response.text}")
                return None
        except Exception as e:
            self.log_test("Create Room", False, f"Error: {str(e)}")
            return None
    
    def test_get_room(self, room_id):
        """Test GET /api/rooms/{room_id} - Get room details with users"""
        try:
            response = requests.get(f"{API_BASE}/rooms/{room_id}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    self.log_test("Get Room", False, f"Room not found: {data['error']}")
                    return False
                
                required_fields = ['id', 'active_users', 'users']
                if all(field in data for field in required_fields):
                    self.log_test("Get Room", True, f"Room retrieved: {data.get('name', 'Unknown')} (Active users: {data['active_users']}, Users list: {len(data['users'])})")
                    return True
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Get Room", False, f"Missing fields: {missing}")
                    return False
            else:
                self.log_test("Get Room", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Room", False, f"Error: {str(e)}")
            return False
    
    def test_list_rooms(self):
        """Test GET /api/rooms - List all rooms with user info"""
        try:
            response = requests.get(f"{API_BASE}/rooms", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    # Check if rooms have user information
                    has_user_info = all('users' in room and 'active_users' in room for room in data)
                    self.log_test("List Rooms", True, f"Retrieved {len(data)} rooms with user info: {has_user_info}")
                    return True
                else:
                    self.log_test("List Rooms", False, "Response is not a list")
                    return False
            else:
                self.log_test("List Rooms", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("List Rooms", False, f"Error: {str(e)}")
            return False
    
    def test_get_room_messages(self, room_id):
        """Test GET /api/rooms/{room_id}/messages - Get room messages"""
        try:
            response = requests.get(f"{API_BASE}/rooms/{room_id}/messages", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'messages' in data and isinstance(data['messages'], list):
                    self.log_test("Get Room Messages", True, f"Retrieved {len(data['messages'])} messages")
                    return True
                else:
                    self.log_test("Get Room Messages", False, "Response missing 'messages' field or not a list")
                    return False
            else:
                self.log_test("Get Room Messages", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Room Messages", False, f"Error: {str(e)}")
            return False
    
    def test_send_message(self, room_id):
        """Test POST /api/rooms/{room_id}/messages - Send text message"""
        try:
            message_data = {
                "user_id": self.test_user_id,
                "username": self.test_username,
                "message": "Hello from Discord-like chat test!",
                "message_type": "text"
            }
            response = requests.post(f"{API_BASE}/rooms/{room_id}/messages", json=message_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['id', 'room_id', 'user_id', 'username', 'message', 'message_type', 'timestamp']
                
                if all(field in data for field in required_fields):
                    self.log_test("Send Message", True, f"Message sent: '{data['message']}' by {data['username']}")
                    return data
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Send Message", False, f"Missing fields: {missing}")
                    return None
            else:
                self.log_test("Send Message", False, f"HTTP {response.status_code}: {response.text}")
                return None
        except Exception as e:
            self.log_test("Send Message", False, f"Error: {str(e)}")
            return None
    
    def test_upload_image(self, room_id):
        """Test POST /api/rooms/{room_id}/upload - Upload image file"""
        try:
            # Create a simple test image (1x1 pixel PNG)
            test_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
            
            files = {
                'file': ('test_image.png', io.BytesIO(test_image_data), 'image/png')
            }
            data = {
                'user_id': self.test_user_id,
                'username': self.test_username
            }
            
            response = requests.post(f"{API_BASE}/rooms/{room_id}/upload", files=files, data=data, timeout=10)
            
            if response.status_code == 200:
                response_data = response.json()
                required_fields = ['id', 'room_id', 'user_id', 'username', 'message_type', 'file_url']
                
                if all(field in response_data for field in required_fields):
                    if response_data['message_type'] == 'image' and response_data['file_url']:
                        self.log_test("Upload Image", True, f"Image uploaded: {response_data['file_url']} by {response_data['username']}")
                        return response_data
                    else:
                        self.log_test("Upload Image", False, "Invalid message_type or missing file_url")
                        return None
                else:
                    missing = [f for f in required_fields if f not in response_data]
                    self.log_test("Upload Image", False, f"Missing fields: {missing}")
                    return None
            else:
                self.log_test("Upload Image", False, f"HTTP {response.status_code}: {response.text}")
                return None
        except Exception as e:
            self.log_test("Upload Image", False, f"Error: {str(e)}")
            return None
    
    async def test_websocket_with_user_params(self, room_id):
        """Test WebSocket connection with user_id and username parameters"""
        try:
            ws_url = f"{WS_BASE}/ws/{room_id}?user_id={self.test_user_id}&username={self.test_username}"
            print(f"Connecting to WebSocket: {ws_url}")
            
            async with websockets.connect(ws_url) as websocket:
                self.log_test("WebSocket Connection with User Params", True, f"Connected to room {room_id} as {self.test_username}")
                
                # Test join message
                join_message = {"type": "join", "room_id": room_id}
                await websocket.send(json.dumps(join_message))
                
                # Wait for room_info response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(response)
                    
                    if data.get("type") == "room_info":
                        # Check if response contains room data and messages
                        if 'data' in data and 'messages' in data:
                            self.log_test("WebSocket Join with Room Info", True, f"Received room_info with {len(data['messages'])} messages")
                            return True
                        else:
                            self.log_test("WebSocket Join with Room Info", False, "Missing room data or messages in response")
                            return False
                    else:
                        self.log_test("WebSocket Join with Room Info", False, f"Unexpected response: {data}")
                        return False
                except asyncio.TimeoutError:
                    self.log_test("WebSocket Join with Room Info", False, "No response to join message")
                    return False
                    
        except Exception as e:
            self.log_test("WebSocket Connection with User Params", False, f"Connection error: {str(e)}")
            return False
    
    async def test_voice_status_management(self, room_id):
        """Test voice call status management (join_voice, leave_voice)"""
        try:
            ws_url = f"{WS_BASE}/ws/{room_id}?user_id={self.test_user_id}&username={self.test_username}"
            
            async with websockets.connect(ws_url) as websocket:
                # Test join_voice
                join_voice_message = {"type": "join_voice"}
                await websocket.send(json.dumps(join_voice_message))
                
                # Should receive user_voice_update
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(response)
                    
                    if data.get("type") == "user_voice_update" and data.get("is_in_voice") == True:
                        self.log_test("Join Voice Status", True, f"User {data.get('username')} joined voice")
                        
                        # Test leave_voice
                        leave_voice_message = {"type": "leave_voice"}
                        await websocket.send(json.dumps(leave_voice_message))
                        
                        # Should receive user_voice_update with is_in_voice: false
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=5)
                            data = json.loads(response)
                            
                            if data.get("type") == "user_voice_update" and data.get("is_in_voice") == False:
                                self.log_test("Leave Voice Status", True, f"User {data.get('username')} left voice")
                                return True
                            else:
                                self.log_test("Leave Voice Status", False, f"Unexpected response: {data}")
                                return False
                        except asyncio.TimeoutError:
                            self.log_test("Leave Voice Status", False, "No response to leave_voice")
                            return False
                    else:
                        self.log_test("Join Voice Status", False, f"Unexpected response: {data}")
                        return False
                except asyncio.TimeoutError:
                    self.log_test("Join Voice Status", False, "No response to join_voice")
                    return False
                    
        except Exception as e:
            self.log_test("Voice Status Management", False, f"Error: {str(e)}")
            return False
    
    async def test_typing_indicators(self, room_id):
        """Test typing indicators functionality"""
        try:
            ws_url_1 = f"{WS_BASE}/ws/{room_id}?user_id={self.test_user_id}&username={self.test_username}"
            ws_url_2 = f"{WS_BASE}/ws/{room_id}?user_id={self.test_user_id_2}&username={self.test_username_2}"
            
            async with websockets.connect(ws_url_1) as ws1, \
                       websockets.connect(ws_url_2) as ws2:
                
                await asyncio.sleep(0.5)  # Wait for connections to be established
                
                # Send typing indicator from ws1
                typing_message = {"type": "typing", "is_typing": True}
                await ws1.send(json.dumps(typing_message))
                
                # ws2 should receive user_typing event
                try:
                    response = await asyncio.wait_for(ws2.recv(), timeout=5)
                    data = json.loads(response)
                    
                    if data.get("type") == "user_typing" and data.get("is_typing") == True:
                        self.log_test("Typing Indicators", True, f"User {data.get('username')} is typing")
                        
                        # Test stop typing
                        stop_typing_message = {"type": "typing", "is_typing": False}
                        await ws1.send(json.dumps(stop_typing_message))
                        
                        try:
                            response = await asyncio.wait_for(ws2.recv(), timeout=5)
                            data = json.loads(response)
                            
                            if data.get("type") == "user_typing" and data.get("is_typing") == False:
                                self.log_test("Stop Typing Indicators", True, f"User {data.get('username')} stopped typing")
                                return True
                            else:
                                self.log_test("Stop Typing Indicators", False, f"Unexpected response: {data}")
                                return False
                        except asyncio.TimeoutError:
                            self.log_test("Stop Typing Indicators", False, "No response to stop typing")
                            return False
                    else:
                        self.log_test("Typing Indicators", False, f"Unexpected response: {data}")
                        return False
                except asyncio.TimeoutError:
                    self.log_test("Typing Indicators", False, "No typing indicator received")
                    return False
                    
        except Exception as e:
            self.log_test("Typing Indicators", False, f"Error: {str(e)}")
            return False
    
    async def test_websocket_chat_broadcast(self, room_id):
        """Test real-time chat message broadcasting via WebSocket"""
        try:
            ws_url_1 = f"{WS_BASE}/ws/{room_id}?user_id={self.test_user_id}&username={self.test_username}"
            ws_url_2 = f"{WS_BASE}/ws/{room_id}?user_id={self.test_user_id_2}&username={self.test_username_2}"
            
            async with websockets.connect(ws_url_1) as ws1, \
                       websockets.connect(ws_url_2) as ws2:
                
                await asyncio.sleep(0.5)  # Wait for connections
                
                # Send a message via REST API
                message_data = {
                    "user_id": self.test_user_id,
                    "username": self.test_username,
                    "message": "WebSocket broadcast test message",
                    "message_type": "text"
                }
                
                # Send message via REST API (should broadcast via WebSocket)
                response = requests.post(f"{API_BASE}/rooms/{room_id}/messages", json=message_data, timeout=10)
                
                if response.status_code == 200:
                    # Both WebSocket connections should receive the new_message event
                    try:
                        # Check ws1 receives the broadcast
                        response1 = await asyncio.wait_for(ws1.recv(), timeout=5)
                        data1 = json.loads(response1)
                        
                        # Check ws2 receives the broadcast
                        response2 = await asyncio.wait_for(ws2.recv(), timeout=5)
                        data2 = json.loads(response2)
                        
                        if (data1.get("type") == "new_message" and data2.get("type") == "new_message" and
                            data1.get("message", {}).get("message") == message_data["message"]):
                            self.log_test("WebSocket Chat Broadcast", True, "Message broadcasted to all connected users")
                            return True
                        else:
                            self.log_test("WebSocket Chat Broadcast", False, f"Unexpected broadcast data: {data1}, {data2}")
                            return False
                    except asyncio.TimeoutError:
                        self.log_test("WebSocket Chat Broadcast", False, "No broadcast received")
                        return False
                else:
                    self.log_test("WebSocket Chat Broadcast", False, f"Failed to send message: {response.status_code}")
                    return False
                    
        except Exception as e:
            self.log_test("WebSocket Chat Broadcast", False, f"Error: {str(e)}")
            return False
    
    async def test_user_connection_events(self, room_id):
        """Test user_joined and user_left events with user information"""
        try:
            ws_url_1 = f"{WS_BASE}/ws/{room_id}?user_id={self.test_user_id}&username={self.test_username}"
            ws_url_2 = f"{WS_BASE}/ws/{room_id}?user_id={self.test_user_id_2}&username={self.test_username_2}"
            
            # First connection
            async with websockets.connect(ws_url_1) as ws1:
                await asyncio.sleep(0.5)
                
                # Second connection should trigger user_joined event
                async with websockets.connect(ws_url_2) as ws2:
                    try:
                        # ws1 should receive user_joined event
                        response = await asyncio.wait_for(ws1.recv(), timeout=5)
                        data = json.loads(response)
                        
                        if (data.get("type") == "user_joined" and 
                            data.get("user", {}).get("username") == self.test_username_2):
                            self.log_test("User Joined Event with Info", True, f"User {data['user']['username']} joined (Total: {data.get('total_users')})")
                        else:
                            self.log_test("User Joined Event with Info", False, f"Unexpected event: {data}")
                            return False
                            
                    except asyncio.TimeoutError:
                        self.log_test("User Joined Event with Info", False, "No user_joined event received")
                        return False
                
                # ws2 disconnected, ws1 should receive user_left event
                try:
                    response = await asyncio.wait_for(ws1.recv(), timeout=5)
                    data = json.loads(response)
                    
                    if (data.get("type") == "user_left" and 
                        data.get("user", {}).get("username") == self.test_username_2):
                        self.log_test("User Left Event with Info", True, f"User {data['user']['username']} left (Total: {data.get('total_users')})")
                        return True
                    else:
                        self.log_test("User Left Event with Info", False, f"Unexpected event: {data}")
                        return False
                        
                except asyncio.TimeoutError:
                    self.log_test("User Left Event with Info", False, "No user_left event received")
                    return False
                    
        except Exception as e:
            self.log_test("User Connection Events", False, f"Error: {str(e)}")
            return False
    
    async def test_webrtc_signaling(self, room_id):
        """Test WebRTC signaling message forwarding (offer, answer, ice-candidate)"""
        try:
            ws_url_1 = f"{WS_BASE}/ws/{room_id}?user_id={self.test_user_id}&username={self.test_username}"
            ws_url_2 = f"{WS_BASE}/ws/{room_id}?user_id={self.test_user_id_2}&username={self.test_username_2}"
            
            async with websockets.connect(ws_url_1) as ws1, \
                       websockets.connect(ws_url_2) as ws2:
                
                await asyncio.sleep(0.5)
                
                # Test offer forwarding
                offer_message = {
                    "type": "offer",
                    "offer": {"type": "offer", "sdp": "test-sdp-offer"}
                }
                await ws1.send(json.dumps(offer_message))
                
                try:
                    response = await asyncio.wait_for(ws2.recv(), timeout=5)
                    data = json.loads(response)
                    
                    if data.get("type") == "offer":
                        self.log_test("WebRTC Offer Forwarding", True, "Offer message forwarded successfully")
                        
                        # Test answer back
                        answer_message = {
                            "type": "answer",
                            "answer": {"type": "answer", "sdp": "test-sdp-answer"}
                        }
                        await ws2.send(json.dumps(answer_message))
                        
                        try:
                            response = await asyncio.wait_for(ws1.recv(), timeout=5)
                            data = json.loads(response)
                            
                            if data.get("type") == "answer":
                                self.log_test("WebRTC Answer Forwarding", True, "Answer message forwarded successfully")
                                
                                # Test ICE candidate
                                ice_message = {
                                    "type": "ice-candidate",
                                    "candidate": {
                                        "candidate": "candidate:test",
                                        "sdpMLineIndex": 0,
                                        "sdpMid": "0"
                                    }
                                }
                                await ws1.send(json.dumps(ice_message))
                                
                                try:
                                    response = await asyncio.wait_for(ws2.recv(), timeout=5)
                                    data = json.loads(response)
                                    
                                    if data.get("type") == "ice-candidate":
                                        self.log_test("WebRTC ICE Candidate Forwarding", True, "ICE candidate forwarded successfully")
                                        return True
                                    else:
                                        self.log_test("WebRTC ICE Candidate Forwarding", False, f"Unexpected response: {data}")
                                        return False
                                except asyncio.TimeoutError:
                                    self.log_test("WebRTC ICE Candidate Forwarding", False, "No ICE candidate received")
                                    return False
                            else:
                                self.log_test("WebRTC Answer Forwarding", False, f"Unexpected response: {data}")
                                return False
                        except asyncio.TimeoutError:
                            self.log_test("WebRTC Answer Forwarding", False, "No answer received")
                            return False
                    else:
                        self.log_test("WebRTC Offer Forwarding", False, f"Unexpected response: {data}")
                        return False
                except asyncio.TimeoutError:
                    self.log_test("WebRTC Offer Forwarding", False, "No offer received")
                    return False
                    
        except Exception as e:
            self.log_test("WebRTC Signaling", False, f"Error: {str(e)}")
            return False
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("DISCORD-LIKE BACKEND TEST SUMMARY")
        print("="*70)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%" if total > 0 else "No tests run")
        
        print("\nFailed Tests:")
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            for result in failed_tests:
                print(f"❌ {result['test']}: {result['message']}")
        else:
            print("None")
        
        print("\nPassed Tests:")
        passed_tests = [result for result in self.test_results if result['success']]
        if passed_tests:
            for result in passed_tests:
                print(f"✅ {result['test']}: {result['message']}")
        else:
            print("None")
        
        return passed, total

async def main():
    """Run all Discord-like backend tests"""
    tester = DiscordChatTester()
    
    print("Starting Discord-like Voice Chat Backend Tests...")
    print("="*70)
    
    # Test basic API endpoints
    print("\n🔍 Testing Basic API Endpoints...")
    health_ok = tester.test_health_check()
    api_root_ok = tester.test_api_root()
    
    if not (health_ok or api_root_ok):
        print("❌ Basic API tests failed - stopping tests")
        tester.print_summary()
        return
    
    # Test room management
    print("\n🔍 Testing Room Management...")
    room_id = tester.test_create_room()
    if room_id:
        tester.test_get_room(room_id)
    tester.test_list_rooms()
    
    # Test chat functionality
    if room_id:
        print("\n🔍 Testing Chat Functionality...")
        tester.test_get_room_messages(room_id)
        tester.test_send_message(room_id)
        tester.test_upload_image(room_id)
    
    # Test WebSocket functionality
    if room_id:
        print("\n🔍 Testing WebSocket Functionality...")
        await tester.test_websocket_with_user_params(room_id)
        await tester.test_voice_status_management(room_id)
        await tester.test_typing_indicators(room_id)
        await tester.test_websocket_chat_broadcast(room_id)
        await tester.test_user_connection_events(room_id)
        await tester.test_webrtc_signaling(room_id)
    else:
        print("❌ Skipping WebSocket tests - no room created")
    
    # Print final summary
    passed, total = tester.print_summary()
    
    if passed == total and total > 0:
        print("\n🎉 All tests passed!")
    elif total > 0:
        print(f"\n⚠️  {total - passed} test(s) failed")
    else:
        print("\n❌ No tests were run")

if __name__ == "__main__":
    asyncio.run(main())