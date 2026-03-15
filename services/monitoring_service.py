"""
Monitoring Service Module
-----------------------
This module provides a Flask API with WebSocket support for real-time monitoring
of the system status and events.
"""

from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO  # Import SocketIO
import threading
from datetime import datetime

from core.event_bus import event_bus

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins for SocketIO
# Wrap the app with SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory storage for system status (in a real app, use a database)
system_status = {
    "status": "Initializing",
    "last_event_timestamp": None,
    "events": [],
    "trade_counts": {"success": 0, "error": 0, "info": 0},
}
MAX_EVENTS = 50  # Store the last 50 events

def monitoring_event_handler(data: dict):
    """
    Handles events from the bus and emits them over WebSocket.
    
    Args:
        data: Event data from the event bus
    """
    print(f"[MONITOR] Received event: {data}")
    timestamp = datetime.utcnow().isoformat()
    
    # Create the event log entry
    event_log = {"timestamp": timestamp, **data}

    # Update system status
    system_status["last_event_timestamp"] = timestamp
    system_status["events"].insert(0, event_log)
    if len(system_status["events"]) > MAX_EVENTS:
        system_status["events"].pop()
    if data.get('status') in system_status['trade_counts']:
        system_status['trade_counts'][data['status']] += 1
    system_status["status"] = "Running"
    
    # Emit the event to all connected frontend clients
    socketio.emit('new_event', event_log)
    
    # Also emit an update for the summary status
    socketio.emit('status_update', {
        'status': system_status['status'],
        'trade_counts': system_status['trade_counts']
    })

# API endpoint remains for polling or initial data load
@app.route('/api/status', methods=['GET'])
def get_status():
    """
    API endpoint to get the current system status.
    
    Returns:
        JSON response with system status
    """
    return jsonify(system_status)

# When a client connects, send them the current state
@socketio.on('connect')
def handle_connect():
    """
    Handle new WebSocket connections.
    Send the initial state to the client.
    """
    print('Client connected')
    socketio.emit('initial_state', system_status)

def start_monitoring_listener():
    """
    Subscribes the monitor to its event channel.
    """
    event_bus.subscribe('monitoring-events', monitoring_event_handler)

def run_flask_app():
    """
    Runs the Flask web server with SocketIO support.
    """
    # Use socketio.run() instead of app.run()
    socketio.run(app, port=5001, debug=False, allow_unsafe_werkzeug=True)