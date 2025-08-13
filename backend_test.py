#!/usr/bin/env python3
"""
Backend Testing Suite for Voice Chat WebRTC Application
Tests WebSocket signaling server, room management API, and connection management
"""

import asyncio
import json
import requests
import websockets
import uuid
from datetime import datetime
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from frontend environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://voice-connect-22.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"
WS_BASE = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://') + "/api"

print(f"Testing backend at: {API_BASE}")
print(f"Testing WebSocket at: {WS_BASE}")

class VoiceChatTester:
    def __init__(self):
        self.test_results = []
        self.created_rooms = []
        
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
        """Test GET /api/ health check endpoint"""
        try:
            response = requests.get(f"{API_BASE}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_test("Health Check", True, f"API responding: {data['message']}")
                    return True
                else:
                    self.log_test("Health Check", False, "Response missing 'message' field")
                    return False
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Health Check", False, f"Connection error: {str(e)}")
            return False
    
    def test_create_room(self):
        """Test POST /api/rooms - Create new room"""
        try:
            room_data = {"name": "Test Voice Room"}
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
        """Test GET /api/rooms/{room_id} - Get room details"""
        try:
            response = requests.get(f"{API_BASE}/rooms/{room_id}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    self.log_test("Get Room", False, f"Room not found: {data['error']}")
                    return False
                
                if 'id' in data and 'active_users' in data:
                    self.log_test("Get Room", True, f"Room retrieved: {data.get('name', 'Unknown')} (Active users: {data['active_users']})")
                    return True
                else:
                    self.log_test("Get Room", False, "Response missing required fields")
                    return False
            else:
                self.log_test("Get Room", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Room", False, f"Error: {str(e)}")
            return False
    
    def test_list_rooms(self):
        """Test GET /api/rooms - List all rooms"""
        try:
            response = requests.get(f"{API_BASE}/rooms", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("List Rooms", True, f"Retrieved {len(data)} rooms")
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
    
    async def test_websocket_connection(self, room_id):
        """Test WebSocket connection to /api/ws/{room_id}"""
        try:
            ws_url = f"{WS_BASE}/ws/{room_id}"
            print(f"Connecting to WebSocket: {ws_url}")
            
            async with websockets.connect(ws_url) as websocket:
                self.log_test("WebSocket Connection", True, f"Connected to room {room_id}")
                
                # Test join message
                join_message = {"type": "join", "room_id": room_id}
                await websocket.send(json.dumps(join_message))
                
                # Wait for room_info response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(response)
                    
                    if data.get("type") == "room_info":
                        self.log_test("WebSocket Join", True, "Received room_info response")
                        return True
                    else:
                        self.log_test("WebSocket Join", False, f"Unexpected response: {data}")
                        return False
                except asyncio.TimeoutError:
                    self.log_test("WebSocket Join", False, "No response to join message")
                    return False
                    
        except Exception as e:
            self.log_test("WebSocket Connection", False, f"Connection error: {str(e)}")
            return False
    
    async def test_websocket_signaling(self, room_id):
        """Test WebRTC signaling message forwarding"""
        try:
            ws_url = f"{WS_BASE}/ws/{room_id}"
            
            # Create two WebSocket connections
            async with websockets.connect(ws_url) as ws1, \
                       websockets.connect(ws_url) as ws2:
                
                self.log_test("Multiple WebSocket Connections", True, "Two connections established")
                
                # Wait a moment for connections to be registered
                await asyncio.sleep(0.5)
                
                # Send offer from ws1
                offer_message = {
                    "type": "offer",
                    "offer": {"type": "offer", "sdp": "test-sdp-offer"}
                }
                await ws1.send(json.dumps(offer_message))
                
                # Check if ws2 receives the offer
                try:
                    response = await asyncio.wait_for(ws2.recv(), timeout=5)
                    data = json.loads(response)
                    
                    if data.get("type") == "offer":
                        self.log_test("WebRTC Signaling", True, "Offer message forwarded successfully")
                        
                        # Test answer back
                        answer_message = {
                            "type": "answer",
                            "answer": {"type": "answer", "sdp": "test-sdp-answer"}
                        }
                        await ws2.send(json.dumps(answer_message))
                        
                        # Check if ws1 receives the answer
                        try:
                            response = await asyncio.wait_for(ws1.recv(), timeout=5)
                            data = json.loads(response)
                            
                            if data.get("type") == "answer":
                                self.log_test("WebRTC Answer", True, "Answer message forwarded successfully")
                                return True
                            else:
                                self.log_test("WebRTC Answer", False, f"Unexpected response: {data}")
                                return False
                        except asyncio.TimeoutError:
                            self.log_test("WebRTC Answer", False, "No answer received")
                            return False
                            
                    else:
                        self.log_test("WebRTC Signaling", False, f"Unexpected response: {data}")
                        return False
                        
                except asyncio.TimeoutError:
                    self.log_test("WebRTC Signaling", False, "No offer received")
                    return False
                    
        except Exception as e:
            self.log_test("WebRTC Signaling", False, f"Error: {str(e)}")
            return False
    
    async def test_user_events(self, room_id):
        """Test user_joined and user_left events"""
        try:
            ws_url = f"{WS_BASE}/ws/{room_id}"
            
            # First connection
            async with websockets.connect(ws_url) as ws1:
                await asyncio.sleep(0.5)
                
                # Second connection should trigger user_joined event
                async with websockets.connect(ws_url) as ws2:
                    try:
                        # ws1 should receive user_joined event
                        response = await asyncio.wait_for(ws1.recv(), timeout=5)
                        data = json.loads(response)
                        
                        if data.get("type") == "user_joined":
                            self.log_test("User Joined Event", True, f"Event received with {data.get('total_users')} users")
                        else:
                            self.log_test("User Joined Event", False, f"Unexpected event: {data}")
                            return False
                            
                    except asyncio.TimeoutError:
                        self.log_test("User Joined Event", False, "No user_joined event received")
                        return False
                
                # ws2 disconnected, ws1 should receive user_left event
                try:
                    response = await asyncio.wait_for(ws1.recv(), timeout=5)
                    data = json.loads(response)
                    
                    if data.get("type") == "user_left":
                        self.log_test("User Left Event", True, f"Event received with {data.get('total_users')} users")
                        return True
                    else:
                        self.log_test("User Left Event", False, f"Unexpected event: {data}")
                        return False
                        
                except asyncio.TimeoutError:
                    self.log_test("User Left Event", False, "No user_left event received")
                    return False
                    
        except Exception as e:
            self.log_test("User Events", False, f"Error: {str(e)}")
            return False
    
    async def test_ice_candidate_forwarding(self, room_id):
        """Test ICE candidate message forwarding"""
        try:
            ws_url = f"{WS_BASE}/ws/{room_id}"
            
            async with websockets.connect(ws_url) as ws1, \
                       websockets.connect(ws_url) as ws2:
                
                await asyncio.sleep(0.5)
                
                # Send ICE candidate from ws1
                ice_message = {
                    "type": "ice-candidate",
                    "candidate": {
                        "candidate": "candidate:test",
                        "sdpMLineIndex": 0,
                        "sdpMid": "0"
                    }
                }
                await ws1.send(json.dumps(ice_message))
                
                # Check if ws2 receives the ICE candidate
                try:
                    response = await asyncio.wait_for(ws2.recv(), timeout=5)
                    data = json.loads(response)
                    
                    if data.get("type") == "ice-candidate":
                        self.log_test("ICE Candidate Forwarding", True, "ICE candidate forwarded successfully")
                        return True
                    else:
                        self.log_test("ICE Candidate Forwarding", False, f"Unexpected response: {data}")
                        return False
                        
                except asyncio.TimeoutError:
                    self.log_test("ICE Candidate Forwarding", False, "No ICE candidate received")
                    return False
                    
        except Exception as e:
            self.log_test("ICE Candidate Forwarding", False, f"Error: {str(e)}")
            return False
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("BACKEND TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        print("\nFailed Tests:")
        for result in self.test_results:
            if not result['success']:
                print(f"❌ {result['test']}: {result['message']}")
        
        print("\nPassed Tests:")
        for result in self.test_results:
            if result['success']:
                print(f"✅ {result['test']}: {result['message']}")
        
        return passed, total

async def main():
    """Run all backend tests"""
    tester = VoiceChatTester()
    
    print("Starting Voice Chat Backend Tests...")
    print("="*60)
    
    # Test API endpoints
    print("\n🔍 Testing API Endpoints...")
    health_ok = tester.test_health_check()
    
    if not health_ok:
        print("❌ Health check failed - stopping tests")
        tester.print_summary()
        return
    
    # Create a test room
    room_id = tester.test_create_room()
    if room_id:
        tester.test_get_room(room_id)
    
    tester.test_list_rooms()
    
    # Test WebSocket functionality
    if room_id:
        print("\n🔍 Testing WebSocket Functionality...")
        await tester.test_websocket_connection(room_id)
        await tester.test_websocket_signaling(room_id)
        await tester.test_user_events(room_id)
        await tester.test_ice_candidate_forwarding(room_id)
    else:
        print("❌ Skipping WebSocket tests - no room created")
    
    # Print final summary
    passed, total = tester.print_summary()
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")

if __name__ == "__main__":
    asyncio.run(main())