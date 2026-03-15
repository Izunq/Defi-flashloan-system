# Swarm Monitoring System

## Overview

The Swarm Monitoring System is a comprehensive solution for managing and monitoring the Swarm Intelligence architecture. It addresses the challenges of operational complexity and information overload in a system with thousands of autonomous agents.

This document provides instructions for setting up and using the monitoring system, which includes:

1. **Swarm Monitoring Dashboard**: A visual interface for monitoring agent activity
2. **Intelligent Message Filtering**: A system for efficient message routing
3. **Enhanced Parallel Opportunity Coordinator**: A service for assembling multi-step arbitrage opportunities

## Key Features

### Swarm Monitoring Dashboard

The dashboard provides real-time visibility into the swarm's activities:

- **Agent Distribution Visualization**: See the total number of active agents and their types
- **Real-time Activity Tracking**: Visualize agent activity on a per-chain or per-asset basis
- **Profitability Analysis**: Track the profitability of different agent "species"
- **Manual Intervention**: Terminate rogue or underperforming agent clusters if necessary
- **Performance Metrics**: Monitor system-wide performance and resource usage

### Intelligent Message Filtering and Aggregation

The message filtering system prevents information overload in the communication bus:

- **Hierarchical Channel Structure**: Organized channels (e.g., opportunities:bsc:cake-usdt)
- **Content-based Filtering**: Agents only receive messages relevant to their function
- **Message Aggregation**: Similar messages are combined to reduce volume
- **Rate Limiting**: Prevents message flooding
- **Priority-based Delivery**: Critical messages are delivered first

### Enhanced Parallel Opportunity Coordinator

The coordinator serves as the brain of the swarm:

- **Opportunity Assembly**: Combines partial opportunities into executable trades
- **Graph Theory Algorithms**: Identifies profitable multi-step paths
- **Transaction Construction**: Builds the final transaction payload
- **Risk Assessment**: Evaluates opportunities before execution
- **Execution Management**: Handles the execution of validated opportunities

## Installation

### Prerequisites

- Python 3.8+
- Redis server
- Web3 provider (for blockchain interaction)
- Required Python packages:
  - redis
  - networkx
  - web3
  - flask (for API server)
  - flask-cors (for API server)
  - numpy

### Setup

1. Install required packages:

```bash
pip install redis networkx web3 flask flask-cors numpy
```

2. Ensure Redis is running:

```bash
redis-server
```

3. Configure the system by editing the configuration files:
   - `config/swarm_monitoring_config.json`: Main configuration
   - `config/message_filter_config.json`: Message filtering configuration
   - `config/parallel_coordinator_config.json`: Opportunity coordinator configuration

## Usage

### Starting the Monitoring System

Run the following command to start the complete monitoring system:

```bash
python scripts/start_swarm_monitoring.py --config config/swarm_monitoring_config.json
```

This will start:
- The swarm monitoring dashboard web server
- The message filtering and aggregation system
- The enhanced parallel opportunity coordinator
- The API server for dashboard data

### Accessing the Dashboard

Open your web browser and navigate to:

```
http://localhost:8000/swarm_dashboard.html
```

### API Endpoints

The monitoring system provides a REST API for programmatic access:

- `GET /api/stats`: Get system-wide statistics
- `GET /api/agents`: Get a list of agents (with optional filters)
- `GET /api/opportunities`: Get a list of opportunities (with optional filters)
- `GET /api/agent/{agent_id}`: Get details of a specific agent
- `GET /api/opportunity/{opportunity_id}`: Get details of a specific opportunity
- `POST /api/agent/{agent_id}/terminate`: Terminate a specific agent
- `POST /api/opportunity/{opportunity_id}/execute`: Execute a specific opportunity
- `POST /api/emergency/stop`: Emergency stop all agents

## Configuration

### Main Configuration (`swarm_monitoring_config.json`)

```json
{
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
        "enabled": true
    },
    "message_filter": {
        "config_path": "config/message_filter_config.json",
        "enabled": true
    }
}
```

### Message Filter Configuration (`message_filter_config.json`)

```json
{
    "rate_limits": {
        "system:alerts:*": 10,
        "opportunities:*": 100,
        "*": 1000
    },
    "aggregation_rules": [
        {
            "channel_pattern": "metrics:*",
            "window_seconds": 5.0,
            "max_messages": 100,
            "aggregate_fields": ["value"],
            "aggregate_function": "avg"
        }
    ]
}
```

### Parallel Coordinator Configuration (`parallel_coordinator_config.json`)

```json
{
    "opportunity": {
        "min_profit_usd": 1.0,
        "max_risk_score": 0.7,
        "max_gas_cost_percentage": 0.5,
        "min_components": 2,
        "max_components": 10
    },
    "execution": {
        "auto_execute": false,
        "max_concurrent_executions": 3
    }
}
```

## Architecture

### Component Interaction

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Swarm Agents   │◄────┤  Message Filter  │────►│ Opportunity     │
│  (Thousands)    │     │  & Aggregation   │     │ Coordinator     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         ▲                       ▲                       ▲
         │                       │                       │
         │                       │                       │
         │                       ▼                       │
         │               ┌─────────────────┐             │
         └───────────────┤  Monitoring     │─────────────┘
                         │  Dashboard      │
                         └─────────────────┘
                                 ▲
                                 │
                                 ▼
                         ┌─────────────────┐
                         │  Artemis AI     │
                         │  Core           │
                         └─────────────────┘
```

### Communication Flow

1. Micro-agents publish discoveries to `swarm:discoveries`
2. The Message Filter routes messages to appropriate subscribers
3. The Parallel Opportunity Coordinator listens for discoveries and combines them
4. Composite opportunities are published to `swarm:composite_opportunities`
5. Artemis AI Core validates opportunities
6. The Coordinator executes validated opportunities
7. Results are published to `swarm:opportunity_executions`
8. The Monitoring Dashboard visualizes all activity

## Troubleshooting

### Common Issues

1. **Dashboard not loading**:
   - Ensure the web server is running on the configured port
   - Check browser console for JavaScript errors

2. **Agents not appearing in dashboard**:
   - Verify Redis connection
   - Check that agents are publishing status updates

3. **Message filtering not working**:
   - Verify Redis pub/sub functionality
   - Check channel patterns in configuration

4. **Opportunity coordinator not finding opportunities**:
   - Ensure agents are publishing discoveries
   - Check minimum profit and risk thresholds

### Logs

Log files are stored in the `logs/` directory:
- `logs/swarm_monitoring.log`: Main monitoring system logs
- `logs/coordinator.log`: Opportunity coordinator logs

## Advanced Usage

### Custom Agent Types

To add support for new agent types in the dashboard:

1. Update the agent type definitions in the dashboard HTML
2. Add corresponding colors and icons
3. Ensure agents publish their type in status messages

### Emergency Procedures

In case of system issues:

1. Use the "Emergency Stop" button on the dashboard to halt all agents
2. Check logs for error messages
3. Restart the system with corrected configuration

## Future Enhancements

Planned improvements to the monitoring system:

1. **Machine Learning Integration**: Predictive analytics for agent performance
2. **Advanced Visualization**: 3D network graphs of opportunity paths
3. **Automated Scaling**: AI-driven optimization of agent distribution
4. **Alerting System**: Notifications for critical events
5. **Historical Analysis**: Long-term performance tracking and reporting

## Conclusion

The Swarm Monitoring System provides comprehensive visibility and control over the Swarm Intelligence architecture. By addressing the challenges of operational complexity and information overload, it enables effective management of thousands of autonomous agents working together to discover and exploit arbitrage opportunities.

For further assistance, please refer to the detailed documentation for each component or contact the system administrators.