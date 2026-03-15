"""
Main Application Entry Point
--------------------------
This script starts all the services required for the arbitrage system.
"""

import threading
import time

from pipelines.arbitrage_pipeline import start_pipeline_listener
from services.monitoring_service import start_monitoring_listener as start_monitor, run_flask_app

if __name__ == "__main__":
    print("--- Starting Arbitrage Bot Backend Services ---")

    # 1. Start the pipeline listener
    # This subscribes to 'market-data-events' and sends them to Celery
    start_pipeline_listener()
    print("[MAIN] Arbitrage pipeline listener started.")

    # 2. Start the monitoring listener
    # This subscribes to 'monitoring-events' to collect logs
    start_monitor()
    print("[MAIN] Monitoring service listener started.")

    # 3. Start the Flask app for the dashboard in a separate thread
    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    flask_thread.start()
    print("[MAIN] Monitoring dashboard API started at http://127.0.0.1:5001")
    
    print("\n--- System is running. ---")
    print("You must run a Celery worker in a separate terminal:")
    print("celery -A pipelines.arbitrage_pipeline worker --loglevel=info")
    
    # Keep the main thread alive to let background threads run
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n--- Shutting down services ---")