#!/bin/bash
# Bash script to start the Phase 2 system
# This script starts Redis, Celery worker, and the main application

echo "=== Starting Phase 2 System ==="

# Check if Redis is running
if pgrep redis-server > /dev/null
then
    echo "Redis server is already running."
else
    echo "Starting Redis server..."
    redis-server &
    sleep 2
fi

# Start Celery worker in a new terminal
echo "Starting Celery worker..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e 'tell app "Terminal" to do script "cd '"$PWD"' && celery -A pipelines.arbitrage_pipeline worker --loglevel=info"'
else
    # Linux
    gnome-terminal -- bash -c "cd $PWD && celery -A pipelines.arbitrage_pipeline worker --loglevel=info; exec bash" || \
    xterm -e "cd $PWD && celery -A pipelines.arbitrage_pipeline worker --loglevel=info" || \
    konsole -e "cd $PWD && celery -A pipelines.arbitrage_pipeline worker --loglevel=info" || \
    echo "Could not open a new terminal. Please start Celery worker manually."
fi

# Wait for Celery to initialize
sleep 3

# Start the main application
echo "Starting main application..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e 'tell app "Terminal" to do script "cd '"$PWD"' && python main.py"'
else
    # Linux
    gnome-terminal -- bash -c "cd $PWD && python main.py; exec bash" || \
    xterm -e "cd $PWD && python main.py" || \
    konsole -e "cd $PWD && python main.py" || \
    echo "Could not open a new terminal. Please start main application manually."
fi

# Start the market data simulator
echo "Starting market data simulator..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e 'tell app "Terminal" to do script "cd '"$PWD"' && python market_data_simulator.py"'
else
    # Linux
    gnome-terminal -- bash -c "cd $PWD && python market_data_simulator.py; exec bash" || \
    xterm -e "cd $PWD && python market_data_simulator.py" || \
    konsole -e "cd $PWD && python market_data_simulator.py" || \
    echo "Could not open a new terminal. Please start market data simulator manually."
fi

# Open the monitoring dashboard
echo "Opening monitoring dashboard..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open monitoring_dashboard.html
else
    # Linux
    xdg-open monitoring_dashboard.html || \
    firefox monitoring_dashboard.html || \
    google-chrome monitoring_dashboard.html || \
    echo "Could not open the dashboard. Please open monitoring_dashboard.html manually."
fi

echo "=== Phase 2 System Started ==="
echo "Press Ctrl+C in each terminal to stop the components when done."