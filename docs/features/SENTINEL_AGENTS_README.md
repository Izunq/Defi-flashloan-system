# Sentinel Agents Layer

The Sentinel Agents Layer provides specialized monitoring and protection for the flashloan system. Each sentinel agent is designed to focus on a specific domain of monitoring, providing dedicated and specialized logic rather than general monitoring.

## Architecture Overview

The Sentinel Agents Layer consists of:

1. **Oracle Sentinel** - Monitors oracle data integrity and security
2. **MEV Sentinel** - Protects against MEV attacks (frontrunning, backrunning, sandwich attacks)
3. **Strategy Sentinel** - Monitors trading strategy execution and performance
4. **Sentinel Coordinator** - Manages and coordinates all sentinel agents

## Sentinel Agents

### Oracle Sentinel (`oracle_sentinel.py`)

The Oracle Sentinel is responsible for:

- Monitoring price data from multiple oracle sources
- Detecting anomalies and manipulation attempts
- Using statistical and ML-based methods for anomaly detection
- Alerting on suspicious oracle behavior
- Tracking oracle reliability and reputation

Key features:
- Multi-source oracle data validation
- Machine learning-based anomaly detection
- Historical price deviation analysis
- Alert generation with recommended actions

### MEV Sentinel (`mev_sentinel.py`)

The MEV Sentinel is responsible for:

- Monitoring for MEV attacks (frontrunning, backrunning, sandwich attacks)
- Protecting transactions from MEV extraction
- Implementing protection strategies (private mempools, randomized submission)
- Analyzing transaction patterns for MEV activity

Key features:
- Transaction monitoring and analysis
- MEV attack detection
- Protection strategy implementation
- Transaction routing through private mempools

### Strategy Sentinel (`strategy_sentinel.py`)

The Strategy Sentinel is responsible for:

- Monitoring trading strategy execution
- Tracking performance metrics
- Detecting anomalies in strategy behavior
- Alerting on strategy execution issues
- Providing performance analytics

Key features:
- Strategy execution tracking
- Performance metrics calculation
- Baseline comparison
- Execution abort capabilities
- Performance optimization recommendations

## Sentinel Coordinator

The Sentinel Coordinator (`sentinel_coordinator.py`) manages all sentinel agents and provides:

- Centralized control of all sentinel agents
- Health monitoring of sentinel agents
- Alert aggregation and prioritization
- System-wide status reporting

## Configuration

Each sentinel agent has its own configuration file:

- `oracle_sentinel_config.yaml`
- `mev_sentinel_config.yaml`
- `strategy_sentinel_config.yaml`

The Sentinel Coordinator uses a master configuration file (`sentinel_config.yaml`) that includes settings for all agents.

## Usage

To start the entire sentinel system:

```bash
python sentinel_coordinator.py
```

To start individual sentinel agents:

```bash
python oracle_sentinel.py
python mev_sentinel.py
python strategy_sentinel.py
```

## Integration

The sentinel agents integrate with the rest of the system through:

1. Direct monitoring of blockchain data
2. Alert generation for other system components
3. Protection strategy implementation
4. Performance data collection and analysis

## Database

Each sentinel agent maintains its own database for:

- Historical data storage
- Alert history
- Performance metrics
- Baseline calculations

## Alerts

Alerts are categorized by severity:
- INFO/LOW - Informational, no immediate action required
- WARNING/MEDIUM - Potential issue, should be investigated
- CRITICAL/HIGH - Serious issue requiring immediate attention
- EMERGENCY - Critical system issue requiring immediate intervention

Each alert includes:
- Detailed information about the issue
- Recommended actions
- Contextual data for investigation