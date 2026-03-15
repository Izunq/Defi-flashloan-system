# Mock Redis Service for Testing
import socket
import threading
import time
import json
from datetime import datetime

class MockRedisServer:
    def __init__(self, host='localhost', port=6379):
        self.host = host
        self.port = port
        self.data = {}
        self.server_socket = None
        self.running = False
        
    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            
            print(f"🚀 Mock Redis server started on {self.host}:{self.port}")
            
            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client, 
                        args=(client_socket,)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                except socket.error:
                    if self.running:
                        print("❌ Socket error occurred")
                    break
                    
        except Exception as e:
            print(f"❌ Failed to start mock Redis server: {e}")
            
    def handle_client(self, client_socket):
        try:
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                    
                # Simple Redis protocol simulation
                response = self.process_command(data.strip())
                client_socket.send(response.encode('utf-8'))
                
        except Exception as e:
            print(f"Client handling error: {e}")
        finally:
            client_socket.close()
            
    def process_command(self, command):
        parts = command.split()
        if not parts:
            return "-ERR empty command\r\n"
            
        cmd = parts[0].upper()
        
        if cmd == "PING":
            return "+PONG\r\n"
        elif cmd == "SET" and len(parts) >= 3:
            key, value = parts[1], ' '.join(parts[2:])
            self.data[key] = value
            return "+OK\r\n"
        elif cmd == "GET" and len(parts) >= 2:
            key = parts[1]
            value = self.data.get(key)
            if value:
                return f"+{value}\r\n"
            else:
                return "$-1\r\n"
        elif cmd == "DEL" and len(parts) >= 2:
            key = parts[1]
            if key in self.data:
                del self.data[key]
                return ":1\r\n"
            else:
                return ":0\r\n"
        else:
            return "-ERR unknown command\r\n"
            
    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()

if __name__ == "__main__":
    server = MockRedisServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down mock Redis server...")
        server.stop()
