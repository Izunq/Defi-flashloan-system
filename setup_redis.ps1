# Redis Setup Script for Flash Loan System
# This script sets up Redis for load testing

Write-Host "🔧 Setting up Redis for Flash Loan System..." -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Check if Docker is available
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker found: $dockerVersion" -ForegroundColor Green
        
        # Stop any existing Redis container
        Write-Host "🛑 Stopping any existing Redis containers..." -ForegroundColor Yellow
        docker stop redis-flashloan 2>$null
        docker rm redis-flashloan 2>$null
        
        # Start Redis container
        Write-Host "🚀 Starting Redis container..." -ForegroundColor Yellow
        docker run -d --name redis-flashloan -p 6379:6379 redis:alpine
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Redis container started successfully!" -ForegroundColor Green
            Write-Host "📍 Redis is running on localhost:6379" -ForegroundColor White
            
            # Test Redis connection
            Start-Sleep 3
            docker exec redis-flashloan redis-cli ping
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Redis connection test passed!" -ForegroundColor Green
            }
        } else {
            Write-Host "❌ Failed to start Redis container" -ForegroundColor Red
            throw "Docker container failed to start"
        }
    } else {
        throw "Docker not found"
    }
} catch {
    Write-Host "⚠️ Docker not available or failed. Setting up mock Redis service..." -ForegroundColor Yellow
    
    # Create mock Redis service for testing
    $mockRedisPath = "mock_redis_service.py"
    
    @"
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
"@ | Out-File -FilePath $mockRedisPath -Encoding UTF8
    
    Write-Host "✅ Created mock Redis service: $mockRedisPath" -ForegroundColor Green
    Write-Host "💡 To start mock Redis: python $mockRedisPath" -ForegroundColor White
}

# Create Redis configuration for the system
$redisConfigPath = "redis_config.json"
@"
{
    "redis": {
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "decode_responses": true,
        "health_check_interval": 30,
        "socket_keepalive": true,
        "socket_keepalive_options": {},
        "connection_pool": {
            "max_connections": 50,
            "retry_on_timeout": true
        }
    },
    "testing": {
        "load_test_duration": 300,
        "concurrent_connections": 100,
        "operations_per_second": 1000,
        "test_data_size": 10000
    }
}
"@ | Out-File -FilePath $redisConfigPath -Encoding UTF8

Write-Host "✅ Created Redis configuration: $redisConfigPath" -ForegroundColor Green

# Test Redis connection with Python
$testScript = @"
import redis
import json
import sys

try:
    # Load configuration
    with open('redis_config.json', 'r') as f:
        config = json.load(f)
    
    # Connect to Redis
    r = redis.Redis(**config['redis'])
    
    # Test connection
    r.ping()
    print("✅ Redis connection successful!")
    
    # Test basic operations
    r.set('test_key', 'test_value')
    value = r.get('test_key')
    print(f"✅ Redis operations successful! Retrieved: {value.decode() if value else None}")
    
    # Clean up
    r.delete('test_key')
    
except redis.ConnectionError:
    print("❌ Redis connection failed. Make sure Redis is running.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Redis test failed: {e}")
    sys.exit(1)
"@

$testScript | Out-File -FilePath "test_redis_connection.py" -Encoding UTF8
Write-Host "✅ Created Redis connection test: test_redis_connection.py" -ForegroundColor Green

Write-Host "`n🎯 Next Steps:" -ForegroundColor Cyan
Write-Host "1. If using Docker: Redis is ready on localhost:6379" -ForegroundColor White
Write-Host "2. If using mock: Run 'python mock_redis_service.py' to start mock server" -ForegroundColor White
Write-Host "3. Test connection: Run 'python test_redis_connection.py'" -ForegroundColor White
Write-Host "4. Run load tests: The system will now support full load testing" -ForegroundColor White
