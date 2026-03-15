#!/usr/bin/env python3
"""
Sentinel Performance Optimization Tool
This script analyzes and optimizes the performance of the Sentinel Agent system.
It identifies bottlenecks, optimizes resource usage, and provides recommendations.
"""

import os
import sys
import time
import json
import psutil
import logging
import argparse
import cProfile
import pstats
from memory_profiler import profile as memory_profile
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sentinel_optimization.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("sentinel_optimization")

# Import sentinel components
try:
    from sentinel_coordinator import SentinelCoordinator
    from sentinel_websocket_broadcaster import SentinelWebSocketBroadcaster
    from sentinel_contract_manager import SentinelContractManager
    from emergency_action_executor import EmergencyActionExecutor
    from monitoring_bridge_orchestrator import MonitoringBridgeOrchestrator
    from oracle_sentinel import OracleSentinel
    from mev_sentinel import MEVSentinel
    from strategy_sentinel import StrategySentinel
except ImportError as e:
    logger.error(f"Failed to import sentinel components: {e}")
    sys.exit(1)

class SentinelPerformanceOptimizer:
    """Performance optimization tool for Sentinel Agent system"""
    
    def __init__(self, config_path="sentinel_config.yaml"):
        """Initialize the optimizer with configuration"""
        logger.info("Initializing Sentinel Performance Optimizer")
        
        # Load configuration
        try:
            with open(config_path, "r") as f:
                import yaml
                self.config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
            
        # Initialize components for testing
        self.coordinator = SentinelCoordinator(config_path=config_path)
        self.oracle_sentinel = OracleSentinel(
            coordinator=self.coordinator,
            config_path="oracle_sentinel_config.yaml"
        )
        self.mev_sentinel = MEVSentinel(
            coordinator=self.coordinator,
            config_path="mev_sentinel_config.yaml"
        )
        self.strategy_sentinel = StrategySentinel(
            coordinator=self.coordinator,
            config_path="strategy_sentinel_config.yaml"
        )
        
        # Performance metrics
        self.metrics = {
            "cpu_usage": [],
            "memory_usage": [],
            "execution_times": {},
            "bottlenecks": [],
            "recommendations": []
        }
    
    def profile_component(self, component, method_name, *args, **kwargs):
        """Profile a specific component method"""
        logger.info(f"Profiling {component.__class__.__name__}.{method_name}")
        
        # CPU profiling
        profiler = cProfile.Profile()
        profiler.enable()
        
        # Memory usage before
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Execute the method
        start_time = time.time()
        result = getattr(component, method_name)(*args, **kwargs)
        execution_time = time.time() - start_time
        
        # Memory usage after
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before
        
        # Disable profiler and analyze results
        profiler.disable()
        stats = pstats.Stats(profiler)
        
        # Record metrics
        component_name = component.__class__.__name__
        method_key = f"{component_name}.{method_name}"
        self.metrics["execution_times"][method_key] = execution_time
        self.metrics["cpu_usage"].append({
            "component": component_name,
            "method": method_name,
            "cpu_time": stats.total_tt
        })
        self.metrics["memory_usage"].append({
            "component": component_name,
            "method": method_name,
            "memory_mb": memory_used
        })
        
        # Save detailed profile results
        stats.dump_stats(f"{component_name}_{method_name}_profile.prof")
        
        logger.info(f"Profiling results for {method_key}:")
        logger.info(f"  Execution time: {execution_time:.4f} seconds")
        logger.info(f"  Memory usage: {memory_used:.2f} MB")
        
        return result
    
    def analyze_websocket_performance(self):
        """Analyze WebSocket broadcaster performance"""
        logger.info("Analyzing WebSocket broadcaster performance")
        
        # Profile message sending
        broadcaster = self.coordinator.websocket_broadcaster
        
        # Test with different message sizes
        for size in [1, 10, 100, 1000]:
            test_message = {
                "sentinel": "test",
                "data": "X" * (size * 1024),  # Size in KB
                "timestamp": time.time()
            }
            
            # Profile sending
            self.profile_component(
                broadcaster, 
                "send_message", 
                test_message
            )
    
    def analyze_contract_interaction_performance(self):
        """Analyze contract interaction performance"""
        logger.info("Analyzing contract interaction performance")
        
        # Profile contract manager
        contract_manager = self.coordinator.contract_manager
        
        # Test emergency pause function
        self.profile_component(
            contract_manager,
            "emergency_pause",
            "AIStrategyV35"
        )
    
    def analyze_monitoring_bridge_performance(self):
        """Analyze monitoring bridge performance"""
        logger.info("Analyzing monitoring bridge performance")
        
        # Profile monitoring bridge
        bridge = MonitoringBridgeOrchestrator(
            config_path="unified_monitoring_config.yaml"
        )
        
        # Test data aggregation
        self.profile_component(
            bridge,
            "get_aggregated_monitoring_data"
        )
    
    def analyze_sentinel_performance(self):
        """Analyze individual sentinel performance"""
        logger.info("Analyzing sentinel performance")
        
        # Profile each sentinel's main check method
        self.profile_component(self.oracle_sentinel, "run_single_check")
        self.profile_component(self.mev_sentinel, "run_single_check")
        self.profile_component(self.strategy_sentinel, "run_single_check")
    
    def identify_bottlenecks(self):
        """Identify performance bottlenecks"""
        logger.info("Identifying performance bottlenecks")
        
        # Analyze execution times
        slow_operations = []
        for method, time_taken in self.metrics["execution_times"].items():
            if time_taken > 1.0:  # More than 1 second is considered slow
                slow_operations.append({
                    "method": method,
                    "execution_time": time_taken
                })
        
        # Analyze memory usage
        high_memory_operations = []
        for usage in self.metrics["memory_usage"]:
            if usage["memory_mb"] > 100:  # More than 100MB is considered high
                high_memory_operations.append(usage)
        
        # Record bottlenecks
        self.metrics["bottlenecks"] = {
            "slow_operations": slow_operations,
            "high_memory_operations": high_memory_operations
        }
        
        # Log findings
        if slow_operations:
            logger.warning(f"Found {len(slow_operations)} slow operations")
            for op in slow_operations:
                logger.warning(f"  {op['method']}: {op['execution_time']:.2f} seconds")
        
        if high_memory_operations:
            logger.warning(f"Found {len(high_memory_operations)} high memory operations")
            for op in high_memory_operations:
                logger.warning(f"  {op['component']}.{op['method']}: {op['memory_mb']:.2f} MB")
    
    def generate_recommendations(self):
        """Generate performance optimization recommendations"""
        logger.info("Generating optimization recommendations")
        
        recommendations = []
        
        # Check for slow operations
        for op in self.metrics["bottlenecks"]["slow_operations"]:
            method = op["method"]
            time_taken = op["execution_time"]
            
            if "websocket" in method.lower():
                recommendations.append({
                    "component": method,
                    "issue": f"Slow WebSocket operation ({time_taken:.2f}s)",
                    "recommendation": "Consider implementing message batching or compression"
                })
            elif "contract" in method.lower():
                recommendations.append({
                    "component": method,
                    "issue": f"Slow contract interaction ({time_taken:.2f}s)",
                    "recommendation": "Optimize gas usage or implement transaction caching"
                })
            elif "monitoring" in method.lower():
                recommendations.append({
                    "component": method,
                    "issue": f"Slow monitoring data processing ({time_taken:.2f}s)",
                    "recommendation": "Implement data caching or reduce polling frequency"
                })
            else:
                recommendations.append({
                    "component": method,
                    "issue": f"Slow operation ({time_taken:.2f}s)",
                    "recommendation": "Profile method to identify specific bottlenecks"
                })
        
        # Check for high memory usage
        for op in self.metrics["bottlenecks"]["high_memory_operations"]:
            component = op["component"]
            method = op["method"]
            memory_used = op["memory_mb"]
            
            recommendations.append({
                "component": f"{component}.{method}",
                "issue": f"High memory usage ({memory_used:.2f} MB)",
                "recommendation": "Implement data streaming or pagination to reduce memory footprint"
            })
        
        # General recommendations
        recommendations.append({
            "component": "All Sentinels",
            "issue": "Potential resource contention",
            "recommendation": "Implement rate limiting and backoff strategies"
        })
        
        recommendations.append({
            "component": "WebSocket Broadcaster",
            "issue": "Connection stability",
            "recommendation": "Enhance reconnection logic with exponential backoff"
        })
        
        recommendations.append({
            "component": "Contract Manager",
            "issue": "Transaction reliability",
            "recommendation": "Implement transaction receipt verification and retry mechanism"
        })
        
        # Record recommendations
        self.metrics["recommendations"] = recommendations
        
        # Log recommendations
        logger.info(f"Generated {len(recommendations)} optimization recommendations")
        for i, rec in enumerate(recommendations, 1):
            logger.info(f"Recommendation {i}:")
            logger.info(f"  Component: {rec['component']}")
            logger.info(f"  Issue: {rec['issue']}")
            logger.info(f"  Recommendation: {rec['recommendation']}")
    
    def run_full_optimization_analysis(self):
        """Run complete optimization analysis"""
        logger.info("Running full optimization analysis")
        
        # Run all analysis components
        self.analyze_websocket_performance()
        self.analyze_contract_interaction_performance()
        self.analyze_monitoring_bridge_performance()
        self.analyze_sentinel_performance()
        
        # Identify issues and generate recommendations
        self.identify_bottlenecks()
        self.generate_recommendations()
        
        # Save results
        self.save_results()
        
        return self.metrics
    
    def save_results(self):
        """Save optimization results to file"""
        logger.info("Saving optimization results")
        
        with open("sentinel_optimization_results.json", "w") as f:
            json.dump(self.metrics, f, indent=2)
        
        # Generate human-readable report
        with open("sentinel_optimization_report.md", "w") as f:
            f.write("# Sentinel System Optimization Report\n\n")
            
            f.write("## Performance Bottlenecks\n\n")
            f.write("### Slow Operations\n\n")
            for op in self.metrics["bottlenecks"]["slow_operations"]:
                f.write(f"- **{op['method']}**: {op['execution_time']:.2f} seconds\n")
            
            f.write("\n### High Memory Operations\n\n")
            for op in self.metrics["bottlenecks"]["high_memory_operations"]:
                f.write(f"- **{op['component']}.{op['method']}**: {op['memory_mb']:.2f} MB\n")
            
            f.write("\n## Optimization Recommendations\n\n")
            for i, rec in enumerate(self.metrics["recommendations"], 1):
                f.write(f"### {i}. {rec['component']}\n\n")
                f.write(f"**Issue**: {rec['issue']}\n\n")
                f.write(f"**Recommendation**: {rec['recommendation']}\n\n")
        
        logger.info("Results saved to sentinel_optimization_results.json")
        logger.info("Report saved to sentinel_optimization_report.md")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Sentinel Performance Optimizer")
    parser.add_argument("--config", default="sentinel_config.yaml", help="Path to sentinel config")
    args = parser.parse_args()
    
    try:
        optimizer = SentinelPerformanceOptimizer(config_path=args.config)
        optimizer.run_full_optimization_analysis()
        logger.info("Optimization analysis completed successfully")
    except Exception as e:
        logger.error(f"Optimization analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()