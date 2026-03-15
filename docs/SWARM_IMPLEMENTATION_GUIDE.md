# Swarm Intelligence Implementation Guide

This guide provides step-by-step instructions for implementing and running the new Swarm Intelligence architecture for the Autonomous Halal Wealth System.

## 1. System Overview

The new architecture implements a true swarm intelligence model with:

- Hyper-specialized micro-agents focusing on single tasks
- Dynamic agent creation and destruction
- Real-time communication between agents
- Evolutionary selection of successful strategies
- Artemis AI Core strategic oversight

## 2. Prerequisites

Before starting, ensure you have:

- Python 3.8 or higher
- Redis server installed and running
- Required Python packages

## 3. Installation Steps

### 3.1. Install Required Packages

```bash
pip install redis web3 pyyaml psutil aiohttp
```

### 3.2. Configure Redis

Ensure Redis is running on the default port (6379). If you need to use a different configuration, update the following files:

- `config/swarm_factory_config.yaml`
- `config/parallel_coordinator_config.yaml`
- `config/artemis_swarm_integration.yaml`

## 4. Implementation Steps

### 4.1. Create the Base Micro-Agent Template

The `MicroAgent` base class in `src/agents/micro_agent_template.py` provides the foundation for all specialized agents. This class handles:

- Communication with the swarm
- Performance tracking
- Lifecycle management
- Command processing

### 4.2. Implement Specialized Micro-Agents

Create specialized micro-agents by inheriting from the `MicroAgent` base class. For example, the `PairWatcherMicroAgent` in `src/agents/pair_watcher_micro_agent.py` specializes in monitoring token pairs on DEXes.

To create a new type of micro-agent:

1. Create a new file in `src/agents/` (e.g., `my_specialized_agent.py`)
2. Inherit from `MicroAgent`
3. Implement the required abstract methods:
   - `execute_cycle()`: Core logic executed on each cycle
   - `get_cycle_interval()`: Time between execution cycles
   - `handle_command()`: Process agent-specific commands

### 4.3. Define Agent Templates

Agent templates in YAML format define the parameters and resource requirements for each type of agent. Templates are stored in `templates/micro_agents/`.

To create a new template:

1. Create a new YAML file in `templates/micro_agents/` (e.g., `my_agent_template.yaml`)
2. Define the required fields:
   - `agent_type`: Type of agent (from `MicroAgentType` enum)
   - `name`: Human-readable name
   - `description`: Description of the agent's purpose
   - `parameters`: Default parameters for the agent
   - `module_path`: Python module path to the agent class
   - `class_name`: Name of the agent class
   - `resource_requirements`: CPU, memory, and network requirements
   - `halal_compliant`: Whether the agent is Shariah-compliant

### 4.4. Implement the Swarm Agent Factory

The `SwarmAgentFactoryV2` in `src/agents/swarm_agent_factory_v2.py` manages the creation, monitoring, and scaling of micro-agents. It:

- Loads agent templates
- Creates and destroys agents
- Monitors agent performance
- Scales successful agent types up and underperforming ones down
- Manages communication between agents

### 4.5. Implement the Parallel Opportunity Coordinator

The existing `ParallelOpportunityCoordinator` in `src/agents/parallel_opportunity_coordinator.py` handles:

- Receiving discoveries from individual agents
- Combining partial opportunities into complex arbitrage chains
- Evaluating and ranking opportunities
- Creating execution plans
- Coordinating with the execution system

### 4.6. Implement the Artemis AI Core Integration

The `ArtemisSwarmIntegrationV2` in `artemis_core/swarm_integration_v2.py` provides strategic oversight:

- Analyzes agent performance
- Generates strategic recommendations
- Validates complex opportunities
- Applies risk controls
- Dynamically reconfigures the swarm

## 5. Running the System

### 5.1. Start the Swarm System

```bash
python scripts/start_swarm_system_v2.py
```

Options:
- `--halal`: Enable Halal compliance mode
- `--debug`: Enable debug logging
- `--agents=N`: Number of initial agents to create (default: 100)

### 5.2. Start the Artemis AI Core Integration

```bash
python scripts/start_artemis_swarm_integration.py
```

Options:
- `--halal`: Enable Halal compliance mode
- `--debug`: Enable debug logging

## 6. Monitoring and Management

### 6.1. Redis Channels for Monitoring

Monitor the system by subscribing to Redis channels:

- `swarm:agent_status`: Agent status updates
- `swarm:discoveries`: Individual agent discoveries
- `swarm:composite_opportunities`: Complex opportunities
- `swarm:opportunity_executions`: Execution results
- `artemis:strategy_recommendations`: Strategic recommendations

Example using redis-cli:
```bash
redis-cli subscribe swarm:agent_status
```

### 6.2. Log Files

Check log files for detailed information:

- `logs/swarm_system_v2.log`: Swarm system logs
- `logs/artemis_swarm_integration.log`: Artemis integration logs
- `logs/swarm/`: Individual agent logs

## 7. Extending the System

### 7.1. Creating New Agent Types

To add a new type of micro-agent:

1. Add a new value to the `MicroAgentType` enum in `src/agents/swarm_agent_factory_v2.py`
2. Create a new agent class inheriting from `MicroAgent`
3. Create a template YAML file for the new agent type
4. Restart the system to load the new agent type

### 7.2. Customizing Scaling Behavior

Modify the scaling parameters in `config/swarm_factory_config.yaml`:

```yaml
scaling_parameters:
  min_performance_threshold: 0.2  # Minimum performance to avoid scaling down
  scale_up_factor: 2.0            # Factor to scale up by
  scale_down_factor: 0.5          # Factor to scale down by
  evaluation_interval_seconds: 300 # How often to evaluate performance
```

### 7.3. Implementing Custom Opportunity Types

To add a new type of arbitrage opportunity:

1. Modify the `OpportunityType` enum in `src/agents/parallel_opportunity_coordinator.py`
2. Update the opportunity detection logic in your micro-agents
3. Update the opportunity evaluation logic in the coordinator
4. Update the opportunity execution logic in the execution manager

## 8. Troubleshooting

### 8.1. Common Issues

- **Redis Connection Errors**: Ensure Redis is running and accessible
- **Agent Creation Failures**: Check resource limits and template validity
- **No Discoveries**: Verify agent parameters and market connectivity
- **High Resource Usage**: Adjust resource limits or reduce agent count

### 8.2. Debugging

Enable debug logging for more detailed information:

```bash
python scripts/start_swarm_system_v2.py --debug
python scripts/start_artemis_swarm_integration.py --debug
```

## 9. Best Practices

- **Start Small**: Begin with a small number of agents and scale up gradually
- **Monitor Resource Usage**: Keep an eye on CPU, memory, and network usage
- **Diversify Agent Types**: Use a variety of agent types to cover different opportunities
- **Regular Maintenance**: Periodically review and update agent templates
- **Backup Configuration**: Keep backups of your configuration files

## 10. Next Steps

- Implement additional specialized micro-agent types
- Enhance the opportunity evaluation algorithms
- Implement more sophisticated scaling strategies
- Develop a web dashboard for monitoring and management
- Integrate with additional data sources for better opportunity detection

For more detailed information, refer to the [Swarm Architecture V2 Documentation](SWARM_ARCHITECTURE_V2.md).