#!/usr/bin/env python3
"""
Test TCP connection to Suntech protocol server
"""
import socket
import time

def test_suntech_connection():
    """Test connection to Suntech protocol server"""
    
    # Suntech message
    message = "ST300STT;907126119;04;1097B;20250920;15:44:33;33e530;-03.843813;-038.615475;000.013;000.00;11;1;26663840;14.07;000000;1;0019;295746;0.0;0;0;00000000000000;0"
    
    print(f"Testing connection to localhost:5011")
    print(f"Message to send: {message}")
    print()
    
    try:
        # Create TCP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        
        # Connect to server
        print("Connecting to server...")
        sock.connect(('localhost', 5011))
        print("✅ Connected successfully!")
        
        # Send message
        print("Sending message...")
        sock.send(message.encode('utf-8'))
        print("✅ Message sent!")
        
        # Wait a bit
        time.sleep(2)
        
        # Try to receive response (optional)
        try:
            sock.settimeout(1)
            response = sock.recv(1024)
            if response:
                print(f"📨 Received response: {response}")
            else:
                print("📭 No response received (this is normal for Suntech)")
        except socket.timeout:
            print("📭 No response received (timeout - this is normal)")
        
        # Close connection
        sock.close()
        print("✅ Connection closed")
        
        print()
        print("🎯 Test completed successfully!")
        print("Now check the API logs for Suntech protocol activity.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'sock' in locals():
            sock.close()

if __name__ == "__main__":
    test_suntech_connection()
