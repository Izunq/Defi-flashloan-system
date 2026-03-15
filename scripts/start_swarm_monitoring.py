"""
Swarm Monitoring System Launcher

This script starts the swarm monitoring system, which includes:
1. The swarm monitoring dashboard server
2. The message filtering and aggregation system
3. The enhanced parallel opportunity coordinator
"""

import os
import sys
import time
import json
import logging
import argparse
import threading
import subprocess
from pathlib import Path
import http.server
import socketserver
import redis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SwarmMonitoring")

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import required modules
from src.core.message_filter import MessageBus, MessagePriority
from src.agents.enhanced_parallel_opportunity_coordinator import EnhancedParallelOpportunityCoordinator


class SwarmMonitoringSystem:
    """
    Swarm Monitoring System
    
    This class manages the swarm monitoring system components:
    1. Dashboard web server
    2. Message filtering and aggregation system
    3. Enhanced parallel opportunity coordinator
    4. API server for dashboard data
    """
    
    def __init__(self, config_path=None):
        """
        Initialize the swarm monitoring system.
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Set up directories
        self._setup_directories()
        
        # Initialize Redis connection
        self._init_redis()
        
        # Initialize components
        self.message_bus = None
        self.coordinator = None
        self.dashboard_server = None
        self.api_server = None
        
        # Component threads
        self.threads = {}
        
        # Running flag
        self.running = False
        
        logger.info("Swarm Monitoring System initialized")
    
    def _load_config(self, config_path):
        """
        Load configuration from file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        # Default configuration
        config = {
            "redis": {
                "host": "localhost",
                "port": 6379,
                "db": 0
            },
            "dashboard": {
                "host": "0.0.0.0",
                "port": 8000,
                "path": "swarm_dashboard.html"
            },
            "api": {
                "host": "0.0.0.0",
                "port": 8080
            },
            "coordinator": {
                "config_path": "config/parallel_coordinator_config.json",
                "enabled": True
            },
            "message_filter": {
                "config_path": "config/message_filter_config.json",
                "enabled": True
            },
            "logging": {
                "level": "INFO",
                "file": "logs/swarm_monitoring.log"
            }
        }
        
        # Load from file if provided
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                    # Update config recursively
                    self._update_dict(config, file_config)
            except Exception as e:
                logger.error(f"Error loading config from {config_path}: {e}")
        
        return config
    
    def _update_dict(self, d, u):
        """Recursively update a dictionary"""
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._update_dict(d[k], v)
            else:
                d[k] = v
        return d
    
    def _setup_directories(self):
        """Set up necessary directories"""
        os.makedirs("logs", exist_ok=True)
        os.makedirs("data", exist_ok=True)
    
    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            redis_config = self.config["redis"]
            self.redis = redis.Redis(
                host=redis_config["host"],
                port=redis_config["port"],
                db=redis_config["db"]
            )
            self.redis.ping()  # Test connection
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Error connecting to Redis: {e}")
            raise
    
    def start_message_bus(self):
        """Start the message filtering and aggregation system"""
        if not self.config["message_filter"]["enabled"]:
            logger.info("Message filtering system disabled in config")
            return
        
        try:
            config_path = self.config["message_filter"]["config_path"]
            self.message_bus = MessageBus(self.redis, config_path)
            
            # Subscribe to system status channel to monitor components
            self.status_subscriber = self.message_bus.subscribe(
                "system:status:*",
                self._handle_system_status
            )
            
            logger.info("Message filtering system started")
            
            # Start stats collection thread
            self.threads["message_stats"] = threading.Thread(
                target=self._collect_message_stats,
                daemon=True
            )
            self.threads["message_stats"].start()
            
        except Exception as e:
            logger.error(f"Error starting message filtering system: {e}")
            raise
    
    def start_coordinator(self):
        """Start the enhanced parallel opportunity coordinator"""
        if not self.config["coordinator"]["enabled"]:
            logger.info("Parallel opportunity coordinator disabled in config")
            return
        
        try:
            config_path = self.config["coordinator"]["config_path"]
            self.coordinator = EnhancedParallelOpportunityCoordinator(config_path)
            
            # Start in a separate thread
            self.threads["coordinator"] = threading.Thread(
                target=self.coordinator.run,
                daemon=True
            )
            self.threads["coordinator"].start()
            
            logger.info("Enhanced parallel opportunity coordinator started")
        except Exception as e:
            logger.error(f"Error starting parallel opportunity coordinator: {e}")
            raise
    
    def start_dashboard_server(self):
        """Start the dashboard web server"""
        try:
            dashboard_config = self.config["dashboard"]
            host = dashboard_config["host"]
            port = dashboard_config["port"]
            
            # Create a simple HTTP server to serve the dashboard
            handler = http.server.SimpleHTTPRequestHandler
            self.dashboard_server = socketserver.TCPServer((host, port), handler)
            
            # Start in a separate thread
            self.threads["dashboard"] = threading.Thread(
                target=self.dashboard_server.serve_forever,
                daemon=True
            )
            self.threads["dashboard"].start()
            
            logger.info(f"Dashboard server started at http://{host}:{port}")
        except Exception as e:
            logger.error(f"Error starting dashboard server: {e}")
            raise
    
    def start_api_server(self):
        """Start the API server for dashboard data"""
        try:
            # Import Flask only if needed
            from flask import Flask, jsonify, request
            from flask_cors import CORS
            
            api_config = self.config["api"]
            host = api_config["host"]
            port = api_config["port"]
            
            app = Flask("SwarmMonitoringAPI")
            CORS(app)
            
            @app.route('/api/stats', methods=['GET'])
            def get_stats():
                stats = self._collect_system_stats()
                return jsonify(stats)
            
            @app.route('/api/agents', methods=['GET'])
            def get_agents():
                # Get query parameters
                status = request.args.get('status')
                type = request.args.get('type')
                chain = request.args.get('chain')
                limit = int(request.args.get('limit', 100))
                offset = int(request.args.get('offset', 0))
                
                # Get agents from Redis
                agents = self._get_agents(status, type, chain, limit, offset)
                return jsonify(agents)
            
            @app.route('/api/opportunities', methods=['GET'])
            def get_opportunities():
                # Get query parameters
                status = request.args.get('status')
                chain = request.args.get('chain')
                min_profit = request.args.get('min_profit')
                if min_profit:
                    min_profit = float(min_profit)
                limit = int(request.args.get('limit', 100))
                offset = int(request.args.get('offset', 0))
                
                # Get opportunities from coordinator
                if self.coordinator:
                    opportunities = self.coordinator.get_all_opportunities(
                        status=status,
                        chain_id=chain,
                        min_profit=min_profit,
                        limit=limit,
                        offset=offset
                    )
                else:
                    opportunities = []
                
                return jsonify(opportunities)
            
            @app.route('/api/agent/<agent_id>', methods=['GET'])
            def get_agent(agent_id):
                # Get agent details from Redis
                agent = self._get_agent_details(agent_id)
                if agent:
                    return jsonify(agent)
                return jsonify({"error": "Agent not found"}), 404
            
            @app.route('/api/opportunity/<opportunity_id>', methods=['GET'])
            def get_opportunity(opportunity_id):
                # Get opportunity details from coordinator
                if self.coordinator:
                    opportunity = self.coordinator.get_opportunity(opportunity_id)
                    if opportunity:
                        return jsonify(opportunity)
                return jsonify({"error": "Opportunity not found"}), 404
            
            @app.route('/api/agent/<agent_id>/terminate', methods=['POST'])
            def terminate_agent(agent_id):
                # Terminate agent via Redis
                success = self._terminate_agent(agent_id)
                if success:
                    return jsonify({"status": "success"})
                return jsonify({"error": "Failed to terminate agent"}), 400
            
            @app.route('/api/opportunity/<opportunity_id>/execute', methods=['POST'])
            def execute_opportunity(opportunity_id):
                # Execute opportunity via coordinator
                if self.coordinator:
                    self.coordinator._execute_opportunity(opportunity_id)
                    return jsonify({"status": "execution_started"})
                return jsonify({"error": "Coordinator not available"}), 503
            
            @app.route('/api/emergency/stop', methods=['POST'])
            def emergency_stop():
                # Emergency stop all agents
                success = self._emergency_stop()
                if success:
                    return jsonify({"status": "emergency_stop_initiated"})
                return jsonify({"error": "Failed to initiate emergency stop"}), 500
            
            # Start in a separate thread
            self.threads["api"] = threading.Thread(
                target=lambda: app.run(host=host, port=port, debug=False),
                daemon=True
            )
            self.threads["api"].start()
            
            logger.info(f"API server started at http://{host}:{port}")
        except ImportError:
            logger.error("Flask not installed. API server not started.")
        except Exception as e:
            logger.error(f"Error starting API server: {e}")
            raise
    
    def _handle_system_status(self, message):
        """
        Handle system status messages.
        
        Args:
            message: Status message
        """
        # This can be expanded to track system component status
        pass
    
    def _collect_message_stats(self):
        """Collect and publish message bus statistics"""
        while self.running:
            try:
                if self.message_bus:
                    stats = self.message_bus.get_stats()
                    
                    # Publish stats to Redis
                    self.redis.set(
                        "swarm:monitoring:message_stats",
                        json.dumps(stats)
                    )
                
                time.sleep(5)
            except Exception as e:
                logger.error(f"Error collecting message stats: {e}")
                time.sleep(1)
    
    def _collect_system_stats(self):
        """
        Collect system-wide statistics.
        
        Returns:
            System statistics dictionary
        """
        stats = {
            "timestamp": time.time(),
            "agents": {
                "total": 0,
                "active": 0,
                "idle": 0,
                "error": 0,
                "by_type": {},
                "by_chain": {}
            },
            "opportunities": {
                "total": 0,
                "pending": 0,
                "validated": 0,
                "executing": 0,
                "executed": 0,
                "failed": 0,
                "by_type": {},
                "by_chain": {}
            },
            "performance": {
                "total_profit_usd": 0,
                "success_rate": 0,
                "uptime": 0
            },
            "message_bus": {
                "subscribers": 0,
                "channels": 0,
                "message_history_size": 0
            }
        }
        
        try:
            # Get agent stats from Redis
            agent_stats = self.redis.get("swarm:monitoring:agent_stats")
            if agent_stats:
                agent_stats = json.loads(agent_stats)
                stats["agents"].update(agent_stats)
            
            # Get opportunity stats from coordinator
            if self.coordinator:
                coordinator_stats = self.coordinator.get_stats()
                
                # Update opportunity stats
                stats["opportunities"]["total"] = len(self.coordinator.opportunities)
                stats["opportunities"]["by_type"] = coordinator_stats.get("opportunities_by_type", {})
                stats["opportunities"]["by_chain"] = coordinator_stats.get("opportunities_by_chain", {})
                
                # Count by status
                status_counts = coordinator_stats.get("opportunities_by_status", {})
                for status, count in status_counts.items():
                    if status in stats["opportunities"]:
                        stats["opportunities"][status] = count
                
                # Update performance stats
                stats["performance"]["total_profit_usd"] = coordinator_stats.get("total_profit_usd", 0)
                stats["performance"]["success_rate"] = coordinator_stats.get("success_rate", 0)
                stats["performance"]["uptime"] = coordinator_stats.get("uptime_seconds", 0)
            
            # Get message bus stats
            if self.message_bus:
                message_stats = self.message_bus.get_stats()
                stats["message_bus"].update(message_stats)
        
        except Exception as e:
            logger.error(f"Error collecting system stats: {e}")
        
        return stats
    
    def _get_agents(self, status=None, agent_type=None, chain=None, limit=100, offset=0):
        """
        Get agents matching the filters.
        
        Args:
            status: Filter by status
            agent_type: Filter by agent type
            chain: Filter by blockchain
            limit: Maximum number of agents to return
            offset: Offset for pagination
            
        Returns:
            List of agents
        """
        agents = []
        
        try:
            # Get all agent IDs from Redis
            agent_keys = self.redis.keys("agent:*:status")
            
            for key in agent_keys:
                agent_id = key.decode('utf-8').split(':')[1]
                
                # Get agent data
                agent_data = self.redis.get(f"agent:{agent_id}:data")
                if not agent_data:
                    continue
                
                agent = json.loads(agent_data)
                
                # Apply filters
                if status and agent.get("status") != status:
                    continue
                
                if agent_type and agent.get("type") != agent_type:
                    continue
                
                if chain and agent.get("chain") != chain:
                    continue
                
                agents.append(agent)
            
            # Sort by ID
            agents.sort(key=lambda a: a.get("id", ""))
            
            # Apply pagination
            agents = agents[offset:offset+limit]
        
        except Exception as e:
            logger.error(f"Error getting agents: {e}")
        
        return agents
    
    def _get_agent_details(self, agent_id):
        """
        Get details of an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent details or None if not found
        """
        try:
            agent_data = self.redis.get(f"agent:{agent_id}:data")
            if agent_data:
                return json.loads(agent_data)
        except Exception as e:
            logger.error(f"Error getting agent details: {e}")
        
        return None
    
    def _terminate_agent(self, agent_id):
        """
        Terminate an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Publish termination command
            self.message_bus.publish(
                "system:commands:factory",
                {
                    "command": "terminate_agent",
                    "params": {
                        "agent_id": agent_id
                    }
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error terminating agent: {e}")
        
        return False
    
    def _emergency_stop(self):
        """
        Emergency stop all agents.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Publish emergency stop command
            self.message_bus.publish(
                "system:commands:factory",
                {
                    "command": "emergency_stop",
                    "params": {
                        "reason": "Manual emergency stop"
                    }
                },
                priority=MessagePriority.CRITICAL
            )
            return True
        except Exception as e:
            logger.error(f"Error initiating emergency stop: {e}")
        
        return False
    
    def run(self):
        """Run the swarm monitoring system"""
        self.running = True
        
        # Start components
        self.start_message_bus()
        self.start_coordinator()
        self.start_dashboard_server()
        self.start_api_server()
        
        logger.info("Swarm Monitoring System is running")
        
        try:
            # Keep the main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self.shutdown()
    
    def shutdown(self):
        """Shutdown the swarm monitoring system"""
        self.running = False
        
        # Shutdown components
        if self.message_bus:
            self.message_bus.shutdown()
        
        if self.coordinator:
            self.coordinator.shutdown()
        
        if self.dashboard_server:
            self.dashboard_server.shutdown()
        
        logger.info("Swarm Monitoring System shut down")


def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Swarm Monitoring System")
    parser.add_argument("--config", help="Path to configuration file")
    args = parser.parse_args()
    
    # Create and run monitoring system
    monitoring_system = SwarmMonitoringSystem(args.config)
    monitoring_system.run()


if __name__ == "__main__":
    main()