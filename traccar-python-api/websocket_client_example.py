#!/usr/bin/env python3
"""
WebSocket client example for testing real-time updates.
"""

import asyncio
import websockets
import json
import sys
from datetime import datetime


async def websocket_client(user_id: int = 1):
    """WebSocket client for testing real-time updates."""
    uri = f"ws://localhost:8000/ws/{user_id}"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected to WebSocket for user {user_id}")
            
            # Send welcome message
            welcome_msg = {
                "type": "heartbeat",
                "data": {}
            }
            await websocket.send(json.dumps(welcome_msg))
            
            # Subscribe to positions
            subscribe_msg = {
                "type": "subscribe",
                "data": {"type": "positions"}
            }
            await websocket.send(json.dumps(subscribe_msg))
            print("📡 Subscribed to position updates")
            
            # Subscribe to events
            subscribe_events = {
                "type": "subscribe",
                "data": {"type": "events"}
            }
            await websocket.send(json.dumps(subscribe_events))
            print("📡 Subscribed to event updates")
            
            # Subscribe to device updates
            subscribe_devices = {
                "type": "subscribe",
                "data": {"type": "devices"}
            }
            await websocket.send(json.dumps(subscribe_devices))
            print("📡 Subscribed to device updates")
            
            # Listen for messages
            print("🎧 Listening for real-time updates...")
            print("Press Ctrl+C to exit")
            
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    msg_type = data.get("type", "unknown")
                    
                    if msg_type == "position":
                        pos_data = data.get("data", {})
                        print(f"[{timestamp}] 📍 POSITION: Device {pos_data.get('device_name')} at {pos_data.get('latitude')}, {pos_data.get('longitude')}")
                    
                    elif msg_type == "event":
                        event_data = data.get("data", {})
                        print(f"[{timestamp}] ⚡ EVENT: {event_data.get('type')} for device {event_data.get('device_name')}")
                    
                    elif msg_type == "device_status":
                        device_data = data.get("data", {})
                        old_status = device_data.get("old_status")
                        new_status = device_data.get("status")
                        print(f"[{timestamp}] 🔄 DEVICE: {device_data.get('name')} status changed from {old_status} to {new_status}")
                    
                    elif msg_type == "info":
                        info_data = data.get("data", {})
                        print(f"[{timestamp}] ℹ️  INFO: {info_data.get('message', 'No message')}")
                    
                    elif msg_type == "heartbeat":
                        print(f"[{timestamp}] 💓 HEARTBEAT")
                    
                    else:
                        print(f"[{timestamp}] ❓ UNKNOWN: {msg_type} - {data}")
                
                except websockets.exceptions.ConnectionClosed:
                    print("❌ WebSocket connection closed")
                    break
                except json.JSONDecodeError:
                    print(f"[{timestamp}] 📝 TEXT: {message}")
                except Exception as e:
                    print(f"❌ Error: {e}")
                    break
    
    except ConnectionRefusedError:
        print("❌ Could not connect to WebSocket server. Make sure the server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Connection error: {e}")


async def send_test_messages():
    """Send test messages to trigger WebSocket broadcasts."""
    import aiohttp
    
    # You would need to get a valid JWT token first
    print("📤 To test WebSocket broadcasts, use the API endpoints:")
    print("   POST /api/ws/test-position?device_id=1&latitude=-23.5505&longitude=-46.6333")
    print("   POST /api/ws/test-event?device_id=1&event_type=deviceOnline")
    print("   POST /api/positions/ (create a new position)")
    print("   POST /api/events/ (create a new event)")


if __name__ == "__main__":
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    print(f"🚀 Starting WebSocket client for user {user_id}")
    print("=" * 50)
    
    try:
        asyncio.run(websocket_client(user_id))
    except KeyboardInterrupt:
        print("\n👋 WebSocket client stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

