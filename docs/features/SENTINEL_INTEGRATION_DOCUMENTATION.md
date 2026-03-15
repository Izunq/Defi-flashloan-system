# Sentinel Integration System Documentation

## Overview

The Sentinel Integration System is a comprehensive monitoring and alerting framework designed to protect DeFi operations from various threats and anomalies. It integrates multiple sentinel agents, provides real-time alerts through various channels, and can automatically execute emergency actions when critical issues are detected.

## Architecture

The system follows a modular architecture with the following key components:

### Core Components

1. **Sentinel Coordinator** (`sentinel_coordinator.py`)
   - Central coordination of sentinel agents
   - Alert processing and routing
   - Emergency action execution
   - Shared state management

2. **Alert Routing Engine** (`alert_routing_engine.py`)
   - Routes alerts to appropriate channels
   - Handles alert deduplication and throttling
   - Manages alert batching and prioritization
   - Supports multiple notification channels

3. **Sentinel Contract Manager** (`sentinel_contract_manager.py`)
   - Manages interactions with smart contracts
   - Executes emergency actions (pause/unpause)
   - Handles transaction signing and submission
   - Manages contract ABI registry

4. **Sentinel WebSocket Broadcaster** (`sentinel_websocket_broadcaster.py`)
   - Broadcasts alerts via WebSocket
   - Handles connection management and reconnection
   - Provides real-time updates to frontend

### Alert Channel Managers

1. **Email Alert Manager** (`email_alert_manager.py`)
   - Sends alerts via email
   - Formats alerts for email presentation
   - Handles rate limiting and batching
   - Supports HTML formatting

2. **Slack Alert Manager** (`slack_alert_manager.py`)
   - Sends alerts to Slack channels
   - Formats alerts for Slack presentation
   - Supports message threading and reactions
   - Handles user mentions based on severity

3. **SMS Alert Manager** (`sms_alert_manager.py`)
   - Sends alerts via SMS
   - Formats alerts to fit SMS character limits
   - Supports multiple SMS providers (Twilio, AWS SNS)
   - Prioritizes critical alerts

4. **Webhook Alert Manager** (`webhook_alert_manager.py`)
   - Sends alerts to external systems via webhooks
   - Supports custom payload formatting
   - Handles retry logic and error handling
   - Provides delivery confirmation

### Advanced Features

1. **Alert Correlation Engine** (`alert_correlation_engine.py`)
   - Correlates related alerts to reduce noise
   - Uses multiple correlation models (similarity, temporal, causal)
   - Generates summary insights
   - Reduces alert fatigue

2. **Predictive Alerting Engine** (`predictive_alerting_engine.py`)
   - Predicts potential issues before they occur
   - Uses multiple prediction models (LSTM, ARIMA, Isolation Forest)
   - Monitors various metrics (price, volume, gas, etc.)
   - Provides confidence levels for predictions

3. **Multi-Chain Support** (`multi_chain_support.py`)
   - Supports monitoring multiple blockchain networks
   - Normalizes data across chains
   - Provides chain-specific thresholds and configurations
   - Supports cross-chain correlation of events

### Frontend Integration

1. **Sentinel Alert Panel** (`SentinelAlertPanel.tsx`)
   - React component for displaying alerts
   - Supports filtering and sorting
   - Provides interactive alert management
   - Responsive design for different screen sizes

2. **Sentinel Alerts Hook** (`useSentinelAlerts.ts`)
   - React hook for managing alert state
   - Handles WebSocket connection
   - Provides alert filtering and sorting
   - Manages alert acknowledgment and dismissal

3. **WebSocket Service** (`SentinelWebSocketService.js`)
   - Backend service for WebSocket communication
   - Handles client connections and subscriptions
   - Manages alert broadcasting
   - Provides alert history

## Configuration

The system uses YAML configuration files for flexible setup:

### Main Configuration Files

1. **Sentinel Configuration** (`sentinel_config.yaml`)
   - Global settings for the sentinel system
   - Configuration for individual sentinel agents
   - Integration settings for WebSocket, contracts, etc.
   - Security and observability configuration

2. **Alert Routing Configuration** (`alert_routing_config.yaml`)
   - Alert routing rules based on severity and source
   - Channel-specific configuration
   - Throttling and batching settings
   - Emergency contact information

3. **Contract ABI Registry** (`contract_abi_registry.json`)
   - ABI definitions for smart contracts
   - Function signatures for emergency actions
   - Contract addresses and deployment information
   - Chain-specific contract details

### Configuration Examples

#### Sentinel Configuration

```yaml
# Global settings
global:
  log_level: INFO
  db_path: "sentinel_data.db"

# Security Configuration
security:
  encryption:
    websocket_tls: true
    alert_encryption: "AES-256"
  authentication:
    api_keys: true
    jwt_tokens: true
  rate_limiting:
    per_ip: 100  # requests per minute
    per_user: 500  # requests per minute

# Oracle Sentinel Configuration
oracle_sentinel:
  enabled: true
  monitoring_interval: 10  # seconds
  web3_provider: "http://localhost:8545"
  assets: ["ETH", "BTC", "USDT", "USDC"]
  oracle_sources: ["chainlink", "uniswap", "compound"]

# Integration Configuration
integration:
  websocket:
    enabled: true
    endpoint: "ws://localhost:8080"
  contract_interaction:
    enabled: true
    abi_registry: "contract_abi_registry.json"
    auto_pause_threshold: "CRITICAL"
```

#### Alert Routing Configuration

```yaml
# Global settings
global_settings:
  deduplication_window: 300  # seconds
  rate_limit: 10  # alerts per minute per channel
  batch_size: 5
  batch_timeout: 30  # seconds

# Routing rules
routing_rules:
  oracle_sentinel:
    LOW:
      channels: ["websocket"]
      throttle: 0
    MEDIUM:
      channels: ["websocket", "slack"]
      throttle: 300
    HIGH:
      channels: ["websocket", "slack", "email"]
      throttle: 600
    CRITICAL:
      channels: ["websocket", "slack", "email", "sms"]
      throttle: 0
      emergency_contacts: true
    EMERGENCY:
      channels: ["all_channels"]
      throttle: 0
      emergency_contacts: true
      contract_action: "pause_all"
```

## Alert Flow

The alert flow through the system follows these steps:

1. **Alert Generation**
   - Sentinel agent detects an anomaly or threat
   - Alert is created with severity, source, and details
   - Alert is sent to the Sentinel Coordinator

2. **Alert Processing**
   - Sentinel Coordinator receives the alert
   - Alert is validated and enriched with additional data
   - Alert is broadcast via WebSocket for real-time updates

3. **Alert Routing**
   - Alert Routing Engine determines appropriate channels
   - Alert is checked for duplicates and throttling
   - Alert is formatted for each channel
   - Alert is sent to each channel

4. **Emergency Actions**
   - For critical/emergency alerts, check if action needed
   - If threshold met, execute emergency action via Contract Manager
   - Pause affected contracts to prevent further damage
   - Notify emergency contacts

5. **Alert Correlation**
   - Alert Correlation Engine analyzes the alert
   - Related alerts are grouped together
   - Summary insights are generated
   - Alert noise is reduced

## Emergency Action Flow

The emergency action flow is triggered for critical or emergency alerts:

1. **Threshold Check**
   - Alert severity is compared to auto-pause threshold
   - If severity meets or exceeds threshold, action is triggered
   - Specific alert types may also trigger actions regardless of severity

2. **Contract Determination**
   - Determine which contracts to pause based on alert source
   - For oracle alerts, pause strategies relying on price data
   - For MEV alerts, pause arbitrage executors
   - For emergency severity, pause all contracts

3. **Action Execution**
   - Contract Manager executes pause function on affected contracts
   - Transaction is signed with emergency wallet
   - Gas price is bumped to ensure quick inclusion
   - Transaction hash is logged for tracking

4. **Notification**
   - Emergency contacts are notified via multiple channels
   - Alert includes details of the action taken
   - Dashboard is updated with contract status
   - Follow-up actions are suggested

## Installation and Setup

### Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher (for frontend)
- Web3 provider (Infura, Alchemy, or local node)
- SMTP server for email alerts
- Slack webhook URL for Slack alerts
- Twilio account for SMS alerts (optional)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/sentinel-integration.git
   cd sentinel-integration
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Configure YAML files**
   ```bash
   cp sentinel_config.example.yaml sentinel_config.yaml
   cp alert_routing_config.example.yaml alert_routing_config.yaml
   # Edit configuration files as needed
   ```

6. **Start the system**
   ```bash
   # Start backend
   python start_sentinel_system.py
   
   # Start frontend (in another terminal)
   cd frontend
   npm start
   ```

## Testing

The system includes a comprehensive testing framework:

### Testing Framework

The `sentinel_testing_framework.py` provides:

1. **Unit Tests**
   - Tests for individual components
   - Mocked dependencies for isolation
   - Coverage for core functionality

2. **Integration Tests**
   - Tests for component interactions
   - Partial mocking of external dependencies
   - Verification of data flow between components

3. **End-to-End Tests**
   - Tests for full system functionality
   - Mock services for external dependencies
   - Verification of complete alert flow

4. **Load Tests**
   - Tests for performance under stress
   - High volume alert processing
   - Concurrent alert handling

### Running Tests

```bash
# Run all tests
python sentinel_testing_framework.py

# Run specific test types
python sentinel_testing_framework.py --unit
python sentinel_testing_framework.py --integration
python sentinel_testing_framework.py --e2e
python sentinel_testing_framework.py --load

# Generate test report
python sentinel_testing_framework.py --report
```

## Security Considerations

The system implements several security measures:

1. **Encryption**
   - WebSocket TLS for secure communication
   - AES-256 encryption for sensitive alert data
   - Encrypted storage for credentials and keys

2. **Authentication**
   - API key authentication for external access
   - JWT tokens for frontend authentication
   - Multi-factor authentication for critical actions

3. **Rate Limiting**
   - Per-IP rate limiting to prevent abuse
   - Per-user rate limiting for authenticated users
   - Graduated rate limits based on endpoint sensitivity

4. **Audit Logging**
   - Comprehensive logging of all actions
   - Secure storage of audit logs
   - Retention policy for compliance

5. **Private Key Management**
   - Secure storage of private keys
   - Key rotation policies
   - Minimal privilege principle

## Observability and Monitoring

The system provides comprehensive observability:

1. **Metrics**
   - Prometheus-compatible metrics
   - Custom metrics for alert processing
   - Performance metrics for system health

2. **Logging**
   - Structured JSON logging
   - Multiple log destinations
   - Configurable log levels

3. **Tracing**
   - Distributed tracing for request flow
   - Sampling for high-volume environments
   - Integration with Jaeger

4. **Health Checks**
   - Endpoint health checks
   - Database connection checks
   - External service dependency checks

5. **Dashboards**
   - Grafana dashboards for system metrics
   - Alert dashboards for operational overview
   - Performance dashboards for optimization

## Advanced Features

### AI-Powered Alert Correlation

The Alert Correlation Engine uses multiple models to correlate related alerts:

1. **Similarity Model**
   - Uses cosine similarity to find textually similar alerts
   - Identifies alerts describing the same issue in different ways
   - Reduces duplicate notifications

2. **Temporal Model**
   - Groups alerts that occur within a time window
   - Identifies cascading failures
   - Provides timeline view of related events

3. **Causal Model**
   - Uses Bayesian networks to identify causal relationships
   - Learns from historical alert patterns
   - Identifies root causes of issues

### Predictive Alerting

The Predictive Alerting Engine uses machine learning to predict issues:

1. **Price Prediction (LSTM)**
   - Predicts price movements and volatility
   - Alerts on potential price drops or spikes
   - Provides confidence levels for predictions

2. **Volume Anomaly Detection (Isolation Forest)**
   - Detects abnormal trading volume patterns
   - Identifies potential market manipulation
   - Alerts before significant market moves

3. **Gas Price Prediction (ARIMA)**
   - Predicts gas price spikes
   - Alerts when gas prices may impact transaction costs
   - Helps optimize transaction timing

### Multi-Chain Support

The Multi-Chain Support module enables monitoring across blockchains:

1. **Chain Connections**
   - Manages connections to multiple networks
   - Handles chain-specific RPC endpoints
   - Provides unified interface for interactions

2. **Cross-Chain Correlation**
   - Correlates events across different chains
   - Identifies coordinated activities
   - Provides holistic view of multi-chain operations

3. **Chain-Specific Thresholds**
   - Configurable thresholds for each chain
   - Adapts to different gas price environments
   - Customizes alerting based on chain characteristics

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failures**
   - Check WebSocket server is running
   - Verify network connectivity and firewall settings
   - Check TLS certificate if using secure WebSocket

2. **Alert Delivery Issues**
   - Verify channel configuration (SMTP, Slack webhook, etc.)
   - Check rate limiting and throttling settings
   - Verify network connectivity to external services

3. **Contract Interaction Failures**
   - Check Web3 provider connection
   - Verify contract addresses and ABIs
   - Check gas price and gas limit settings
   - Verify private key is correct and has sufficient funds

### Logging and Debugging

1. **Enable Debug Logging**
   ```yaml
   # In sentinel_config.yaml
   global:
     log_level: DEBUG
   ```

2. **Check Log Files**
   - Main log: `sentinel.log`
   - Alert routing log: `alert_routing.log`
   - Contract manager log: `contract_manager.log`
   - WebSocket log: `websocket.log`

3. **Use Testing Framework**
   ```bash
   python sentinel_testing_framework.py --debug
   ```

## Maintenance and Operations

### Routine Maintenance

1. **Log Rotation**
   - Logs are automatically rotated based on size
   - Archive old logs periodically
   - Clean up logs older than retention period

2. **Database Maintenance**
   - Backup shared database regularly
   - Run cleanup scripts to remove old data
   - Check database size and performance

3. **Configuration Updates**
   - Review and update thresholds periodically
   - Adjust alert routing based on team feedback
   - Update contract ABIs after deployments

### Monitoring the Monitors

1. **System Health Checks**
   - Monitor CPU, memory, and disk usage
   - Set up alerts for system resource issues
   - Monitor WebSocket connection count

2. **Alert Processing Metrics**
   - Track alert volume and processing time
   - Monitor alert delivery success rate
   - Track emergency action execution

3. **External Dependency Checks**
   - Monitor Web3 provider connectivity
   - Check SMTP, Slack, and other external services
   - Verify contract accessibility

## Contributing

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Add tests for your changes**
5. **Run the test suite**
6. **Submit a pull request**

### Coding Standards

- Follow PEP 8 for Python code
- Use TypeScript for frontend code
- Write comprehensive docstrings
- Include unit tests for new features

### Documentation

- Update documentation for new features
- Document configuration changes
- Provide examples for new functionality
- Update troubleshooting guide for new issues

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For questions or support, contact the development team at:
- Email: sentinel-support@example.com
- Slack: #sentinel-integration channel