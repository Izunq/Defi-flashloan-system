#!/usr/bin/env python3
"""
Sentinel WebSocket Broadcaster
Bridge between sentinel alerts and WebSocket service
"""

import os
import sys
import json
import time
import yaml
import logging
import asyncio
import websockets
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict, is_dataclass
from datetime import datetime
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sentinel_websocket_broadcaster.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SentinelWebSocketBroadcaster")

class AlertPriority(Enum):
    """Alert priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class SentinelAlert:
    """Standardized alert format for WebSocket broadcasting"""
    alert_id: str
    source: str  # "oracle", "mev", "strategy"
    priority: str  # AlertPriority value
    title: str
    message: str
    timestamp: int
    details: Dict[str, Any]
    recommended_actions: List[str]
    acknowledged: bool = False
    resolved: bool = False
    resolution_time: Optional[int] = None
    resolution_details: Optional[str] = None

class EnhancedJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles dataclasses and enums"""
    def default(self, obj):
        if is_dataclass(obj):
            return asdict(obj)
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)

class SentinelWebSocketBroadcaster:
    """
    Bridge between sentinel alerts and WebSocket service
    """
    
    def __init__(self, config_path: str = "sentinel_config.yaml"):
        """Initialize the WebSocket broadcaster"""
        self.config = self._load_config(config_path)
        self.ws_config = self.config.get("integration", {}).get("websocket", {})
        
        # WebSocket connection
        self.ws_endpoint = self.ws_config.get("endpoint", "ws://localhost:8080")
        self.reconnect_interval = self.ws_config.get("reconnect_interval", 5)
        self.max_retries = self.ws_config.get("max_retries", 3)
        self.ws_connection = None
        
        # Alert buffer for batching and retry
        self.alert_buffer = []
        self.buffer_size = self.ws_config.get("buffer_size", 1000)
        self.compression = self.ws_config.get("compression", True)
        
        # Connection state
        self.is_connected = False
        self.connection_task = None
        self.broadcast_task = None
        
        logger.info("Sentinel WebSocket Broadcaster initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Config file {config_path} not found")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            sys.exit(1)
    
    async def start(self):
        """Start the WebSocket broadcaster"""
        if not self.ws_config.get("enabled", True):
            logger.warning("WebSocket broadcasting is disabled in config")
            return
        
        logger.info("Starting Sentinel WebSocket Broadcaster")
        self.connection_task = asyncio.create_task(self._maintain_connection())
        self.broadcast_task = asyncio.create_task(self._process_alert_buffer())
    
    async def stop(self):
        """Stop the WebSocket broadcaster"""
        logger.info("Stopping Sentinel WebSocket Broadcaster")
        
        if self.connection_task:
            self.connection_task.cancel()
            try:
                await self.connection_task
            except asyncio.CancelledError:
                pass
            self.connection_task = None
        
        if self.broadcast_task:
            self.broadcast_task.cancel()
            try:
                await self.broadcast_task
            except asyncio.CancelledError:
                pass
            self.broadcast_task = None
        
        if self.ws_connection and self.is_connected:
            await self.ws_connection.close()
            self.ws_connection = None
            self.is_connected = False
    
    async def _maintain_connection(self):
        """Maintain WebSocket connection with retry logic"""
        retry_count = 0
        
        while True:
            try:
                if not self.is_connected:
                    logger.info(f"Connecting to WebSocket server at {self.ws_endpoint}")
                    self.ws_connection = await websockets.connect(self.ws_endpoint)
                    self.is_connected = True
                    retry_count = 0
                    logger.info("Successfully connected to WebSocket server")
                    
                    # Send initial connection message
                    await self._send_message({
                        "type": "connection",
                        "client": "sentinel_broadcaster",
                        "timestamp": int(time.time())
                    })
                
                # Keep the connection alive
                await asyncio.sleep(30)
                
                # Send heartbeat
                if self.is_connected:
                    await self._send_message({
                        "type": "heartbeat",
                        "timestamp": int(time.time())
                    })
            
            except (websockets.exceptions.ConnectionClosed, 
                    websockets.exceptions.InvalidStatusCode,
                    ConnectionRefusedError) as e:
                self.is_connected = False
                retry_count += 1
                
                if retry_count > self.max_retries:
                    logger.error(f"Failed to connect after {self.max_retries} attempts. Waiting longer before retry.")
                    await asyncio.sleep(self.reconnect_interval * 5)
                    retry_count = 0
                else:
                    logger.warning(f"WebSocket connection error: {e}. Retrying in {self.reconnect_interval} seconds...")
                    await asyncio.sleep(self.reconnect_interval)
            
            except Exception as e:
                logger.error(f"Unexpected error in WebSocket connection: {e}")
                self.is_connected = False
                await asyncio.sleep(self.reconnect_interval)
    
    async def _send_message(self, message: Dict[str, Any]) -> bool:
        """Send a message to the WebSocket server"""
        if not self.is_connected or not self.ws_connection:
            return False
        
        try:
            message_json = json.dumps(message, cls=EnhancedJSONEncoder)
            await self.ws_connection.send(message_json)
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.is_connected = False
            return False
    
    async def _process_alert_buffer(self):
        """Process and send alerts from the buffer"""
        while True:
            try:
                if self.alert_buffer and self.is_connected:
                    # Get the oldest alert from the buffer
                    alert = self.alert_buffer[0]
                    
                    # Try to send the alert
                    success = await self._send_alert(alert)
                    
                    if success:
                        # Remove the alert from the buffer if sent successfully
                        self.alert_buffer.pop(0)
                        logger.debug(f"Successfully sent alert {alert.get('alert_id', 'unknown')}")
                    else:
                        # If sending failed, wait before retrying
                        await asyncio.sleep(self.reconnect_interval)
                
                # Wait a short time before processing the next alert
                await asyncio.sleep(0.1)
            
            except Exception as e:
                logger.error(f"Error processing alert buffer: {e}")
                await asyncio.sleep(1)
    
    async def _send_alert(self, alert: Union[Dict[str, Any], SentinelAlert]) -> bool:
        """Send an alert to the WebSocket server"""
        if isinstance(alert, SentinelAlert):
            alert_dict = asdict(alert)
        else:
            alert_dict = alert
        
        message = {
            "type": "data",
            "channel": "sentinel_alerts",
            "alert": alert_dict,
            "timestamp": int(time.time())
        }
        
        return await self._send_message(message)
    
    def add_alert(self, alert: Union[Dict[str, Any], SentinelAlert]) -> bool:
        """Add an alert to the buffer for broadcasting"""
        if len(self.alert_buffer) >= self.buffer_size:
            logger.warning(f"Alert buffer full ({self.buffer_size} items). Dropping oldest alert.")
            self.alert_buffer.pop(0)
        
        self.alert_buffer.append(alert)
        logger.debug(f"Added alert to buffer. Buffer size: {len(self.alert_buffer)}")
        return True
    
    def convert_oracle_alert(self, oracle_alert: Any) -> SentinelAlert:
        """Convert an Oracle Sentinel alert to standardized format"""
        # Map threat level to priority
        priority_map = {
            "LOW": AlertPriority.LOW.value,
            "MEDIUM": AlertPriority.MEDIUM.value,
            "HIGH": AlertPriority.HIGH.value,
            "CRITICAL": AlertPriority.CRITICAL.value,
            "EMERGENCY": AlertPriority.EMERGENCY.value
        }
        
        priority = priority_map.get(oracle_alert.threat_level.value, AlertPriority.MEDIUM.value)
        
        return SentinelAlert(
            alert_id=oracle_alert.alert_id,
            source="oracle",
            priority=priority,
            title=f"Oracle Alert: {oracle_alert.alert_type.value}",
            message=f"Oracle anomaly detected for {oracle_alert.asset} with {oracle_alert.deviation:.2f}% deviation",
            timestamp=oracle_alert.timestamp,
            details={
                "asset": oracle_alert.asset,
                "price": oracle_alert.price,
                "expected_price": oracle_alert.expected_price,
                "deviation": oracle_alert.deviation,
                "source": oracle_alert.source,
                "confidence": oracle_alert.confidence,
                "alert_type": oracle_alert.alert_type.value,
                "false_positive_probability": oracle_alert.false_positive_probability
            },
            recommended_actions=oracle_alert.recommended_actions,
            acknowledged=False,
            resolved=oracle_alert.resolved,
            resolution_time=oracle_alert.resolution_time,
            resolution_details=oracle_alert.resolution_details
        )
    
    def convert_mev_alert(self, mev_alert: Any) -> SentinelAlert:
        """Convert a MEV Sentinel alert to standardized format"""
        # Map threat level to priority
        priority_map = {
            "LOW": AlertPriority.LOW.value,
            "MEDIUM": AlertPriority.MEDIUM.value,
            "HIGH": AlertPriority.HIGH.value,
            "CRITICAL": AlertPriority.CRITICAL.value,
            "EMERGENCY": AlertPriority.EMERGENCY.value
        }
        
        priority = priority_map.get(mev_alert.threat_level.value, AlertPriority.MEDIUM.value)
        
        return SentinelAlert(
            alert_id=mev_alert.alert_id,
            source="mev",
            priority=priority,
            title=f"MEV Alert: {mev_alert.attack_type.value}",
            message=f"MEV attack detected: {mev_alert.attack_type.value}",
            timestamp=mev_alert.timestamp,
            details={
                "attack_type": mev_alert.attack_type.value,
                "profit": mev_alert.profit,
                "gas_used": mev_alert.gas_used,
                "attacker": mev_alert.attacker_address,
                "victim": mev_alert.victim_address,
                "confidence": mev_alert.confidence
            },
            recommended_actions=mev_alert.recommended_actions,
            acknowledged=False,
            resolved=mev_alert.resolved,
            resolution_time=mev_alert.resolution_time,
            resolution_details=mev_alert.resolution_details
        )
    
    def convert_strategy_alert(self, strategy_alert: Any) -> SentinelAlert:
        """Convert a Strategy Sentinel alert to standardized format"""
        # Map alert level to priority
        priority_map = {
            "LOW": AlertPriority.LOW.value,
            "MEDIUM": AlertPriority.MEDIUM.value,
            "HIGH": AlertPriority.HIGH.value,
            "CRITICAL": AlertPriority.CRITICAL.value,
            "EMERGENCY": AlertPriority.EMERGENCY.value
        }
        
        priority = priority_map.get(strategy_alert.alert_level.value, AlertPriority.MEDIUM.value)
        
        return SentinelAlert(
            alert_id=strategy_alert.alert_id,
            source="strategy",
            priority=priority,
            title=f"Strategy Alert: {strategy_alert.strategy_id}",
            message=strategy_alert.message,
            timestamp=strategy_alert.timestamp,
            details=strategy_alert.details,
            recommended_actions=strategy_alert.recommended_actions,
            acknowledged=False,
            resolved=strategy_alert.resolved,
            resolution_time=strategy_alert.resolution_time,
            resolution_details=strategy_alert.resolution_details
        )

async def main():
    """Main entry point"""
    broadcaster = SentinelWebSocketBroadcaster()
    
    try:
        await broadcaster.start()
        
        # Keep the program running
        while True:
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Shutting down...")
    
    finally:
        await broadcaster.stop()

if __name__ == "__main__":
    asyncio.run(main())