#!/usr/bin/env python3
"""
Start Sentinel System
Starts all components of the Sentinel Integration System
"""

import os
import sys
import time
import signal
import logging
import argparse
import threading
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sentinel_system.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("sentinel_system")

# Global variables
running = True
components = {}

def signal_handler(sig, frame):
    """Handle termination signals"""
    global running
    logger.info(f"Received signal {sig}, shutting down...")
    running = False

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Start Sentinel Integration System")
    parser.add_argument("--config", default="sentinel_config.yaml", help="Path to sentinel configuration file")
    parser.add_argument("--alert-config", default="alert_routing_config.yaml", help="Path to alert routing configuration file")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Logging level")
    parser.add_argument("--no-websocket", action="store_true", help="Disable WebSocket broadcaster")
    parser.add_argument("--no-contract", action="store_true", help="Disable contract manager")
    parser.add_argument("--no-advanced", action="store_true", help="Disable advanced features")
    return parser.parse_args()

def setup_logging(log_level):
    """Set up logging with specified level"""
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    logging.getLogger().setLevel(numeric_level)
    logger.info(f"Log level set to {log_level}")

def start_sentinel_coordinator(args):
    """Start the Sentinel Coordinator"""
    logger.info("Starting Sentinel Coordinator...")
    
    try:
        from sentinel_coordinator import SentinelCoordinator
        
        # Initialize contract manager if enabled
        contract_manager = None
        if not args.no_contract:
            from sentinel_contract_manager import SentinelContractManager
            
            contract_manager = SentinelContractManager(
                web3_provider=os.environ.get("WEB3_PROVIDER_URL", "http://localhost:8545"),
                abi_registry_path=os.environ.get("ABI_REGISTRY_PATH", "contract_abi_registry.json")
            )
            components["contract_manager"] = contract_manager
            logger.info("Contract manager initialized")
        
        # Initialize WebSocket broadcaster if enabled
        websocket_broadcaster = None
        if not args.no_websocket:
            from sentinel_websocket_broadcaster import SentinelWebSocketBroadcaster
            
            websocket_broadcaster = SentinelWebSocketBroadcaster(
                websocket_url=os.environ.get("WEBSOCKET_URL", "ws://localhost:8080"),
                reconnect_interval=5
            )
            components["websocket_broadcaster"] = websocket_broadcaster
            logger.info("WebSocket broadcaster initialized")
        
        # Initialize coordinator
        coordinator = SentinelCoordinator(
            contract_manager=contract_manager,
            websocket_broadcaster=websocket_broadcaster,
            config_path=args.config
        )
        components["coordinator"] = coordinator
        
        # Initialize alert routing engine
        from alert_routing_engine import AlertRoutingEngine
        
        alert_routing_engine = AlertRoutingEngine(config_path=args.alert_config)
        components["alert_routing_engine"] = alert_routing_engine
        
        # Set alert routing engine in coordinator
        coordinator.alert_routing_engine = alert_routing_engine
        
        logger.info("Sentinel Coordinator started")
        return coordinator
    except Exception as e:
        logger.error(f"Failed to start Sentinel Coordinator: {e}")
        raise

def start_advanced_features(args):
    """Start advanced features if enabled"""
    if args.no_advanced:
        logger.info("Advanced features disabled")
        return
    
    logger.info("Starting advanced features...")
    
    try:
        # Start Alert Correlation Engine
        from alert_correlation_engine import AlertCorrelationEngine
        
        correlation_engine = AlertCorrelationEngine(config_path=args.config)
        components["correlation_engine"] = correlation_engine
        logger.info("Alert Correlation Engine started")
        
        # Start Predictive Alerting Engine
        from predictive_alerting_engine import PredictiveAlertingEngine
        
        predictive_engine = PredictiveAlertingEngine(config_path=args.config)
        components["predictive_engine"] = predictive_engine
        logger.info("Predictive Alerting Engine started")
        
        # Start Multi-Chain Support
        from multi_chain_support import MultiChainSupport
        
        multi_chain = MultiChainSupport(config_path=args.config)
        multi_chain.start_monitoring(interval=60)
        components["multi_chain"] = multi_chain
        logger.info("Multi-Chain Support started")
        
        logger.info("Advanced features started")
    except Exception as e:
        logger.error(f"Failed to start advanced features: {e}")
        logger.warning("Continuing without advanced features")

def start_api_server():
    """Start the API server"""
    logger.info("Starting API server...")
    
    try:
        import flask
        from flask import Flask, jsonify, request
        
        app = Flask("sentinel_api")
        
        @app.route("/health", methods=["GET"])
        def health_check():
            return jsonify({"status": "ok", "components": list(components.keys())})
        
        @app.route("/alerts", methods=["GET"])
        def get_alerts():
            # Get alerts from alert routing engine
            if "alert_routing_engine" in components:
                alerts = components["alert_routing_engine"].alert_history
                return jsonify({"alerts": alerts})
            return jsonify({"alerts": [], "error": "Alert routing engine not available"})
        
        @app.route("/status", methods=["GET"])
        def get_status():
            status = {
                "system": "running",
                "uptime": time.time() - start_time,
                "components": {}
            }
            
            # Add component status
            for name, component in components.items():
                status["components"][name] = "running"
            
            return jsonify(status)
        
        # Start server in a separate thread
        def run_server():
            app.run(host="0.0.0.0", port=8081, debug=False, use_reloader=False)
        
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()
        
        components["api_server"] = app
        logger.info("API server started on port 8081")
    except ImportError:
        logger.warning("Flask not installed, API server not started")
    except Exception as e:
        logger.error(f"Failed to start API server: {e}")
        logger.warning("Continuing without API server")

def monitor_system():
    """Monitor system and components"""
    logger.info("Starting system monitor...")
    
    while running:
        try:
            # Check component health
            for name, component in list(components.items()):
                if hasattr(component, "connected") and not component.connected:
                    logger.warning(f"Component {name} is disconnected, attempting reconnection...")
                    if hasattr(component, "_reconnect"):
                        component._reconnect()
            
            # Sleep for a while
            time.sleep(30)
        except Exception as e:
            logger.error(f"Error in system monitor: {e}")
            time.sleep(10)  # Sleep and retry

def shutdown_system():
    """Shutdown all components"""
    logger.info("Shutting down system...")
    
    # Shutdown components in reverse order
    for name, component in reversed(list(components.items())):
        try:
            if hasattr(component, "shutdown"):
                logger.info(f"Shutting down {name}...")
                component.shutdown()
            elif hasattr(component, "close"):
                logger.info(f"Closing {name}...")
                component.close()
        except Exception as e:
            logger.error(f"Error shutting down {name}: {e}")
    
    logger.info("System shutdown complete")

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Parse arguments
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Record start time
    start_time = time.time()
    
    try:
        # Start components
        logger.info("Starting Sentinel Integration System...")
        
        # Start coordinator
        coordinator = start_sentinel_coordinator(args)
        
        # Start advanced features
        start_advanced_features(args)
        
        # Start API server
        start_api_server()
        
        # Start system monitor
        monitor_thread = threading.Thread(target=monitor_system)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        logger.info("Sentinel Integration System started successfully")
        
        # Keep main thread alive
        while running:
            time.sleep(1)
    except Exception as e:
        logger.error(f"Error starting system: {e}")
    finally:
        # Shutdown system
        shutdown_system()