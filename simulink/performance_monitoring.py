#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance Monitoring for Simulink Models

This module provides a framework for monitoring the performance of Simulink models
in real-time. It tracks execution time, memory usage, accuracy, and other metrics
to ensure models are performing optimally.

Author: DeFi Arbitrage System
Date: June 17, 2025
"""

import os
import time
import json
import logging
import threading
import numpy as np
import pandas as pd
import psutil
import matplotlib.pyplot as plt
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque

# Import the Simulink bridge
from simulink_bridge import SimulinkBridge, MarketData, TradingSignals

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('performance_monitoring')


@dataclass
class PerformanceMetric:
    """Performance metric for a model."""
    name: str
    value: float
    timestamp: float
    unit: str = ""
    threshold_min: float = float('-inf')
    threshold_max: float = float('inf')
    is_critical: bool = False


@dataclass
class PerformanceAlert:
    """Alert for a performance issue."""
    metric_name: str
    value: float
    threshold: float
    timestamp: float
    message: str
    severity: str  # "info", "warning", "critical"
    is_resolved: bool = False
    resolution_time: float = 0.0
    resolution_message: str = ""


@dataclass
class MonitoringConfig:
    """Configuration for performance monitoring."""
    model_name: str
    metrics: List[str]
    sampling_interval: float = 1.0  # seconds
    window_size: int = 60  # samples
    alert_thresholds: Dict[str, Dict[str, float]] = field(default_factory=dict)
    output_dir: str = "monitoring_results"
    save_interval: int = 60  # seconds
    visualization_enabled: bool = True
    notification_endpoints: List[str] = field(default_factory=list)
    log_level: str = "INFO"


class PerformanceMonitor:
    """Framework for monitoring the performance of Simulink models."""
    
    def __init__(self, simulink_bridge: SimulinkBridge, config: MonitoringConfig):
        """Initialize the performance monitor.
        
        Args:
            simulink_bridge: Instance of SimulinkBridge for model execution
            config: Monitoring configuration
        """
        self.simulink_bridge = simulink_bridge
        self.config = config
        self.metrics = {metric: deque(maxlen=config.window_size) for metric in config.metrics}
        self.alerts = []
        self.running = False
        self.monitoring_thread = None
        self.last_save_time = 0
        self.process = psutil.Process(os.getpid())
        
        # Create output directory if it doesn't exist
        os.makedirs(config.output_dir, exist_ok=True)
        
        # Set log level
        numeric_level = getattr(logging, config.log_level.upper(), None)
        if isinstance(numeric_level, int):
            logger.setLevel(numeric_level)
        
        logger.info(f"Initialized performance monitor for {config.model_name}")
    
    def start(self) -> bool:
        """Start monitoring.
        
        Returns:
            bool: True if monitoring started successfully, False otherwise
        """
        if self.running:
            logger.warning("Monitoring is already running")
            return False
        
        # Start monitoring thread
        self.running = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        logger.info(f"Started performance monitoring for {self.config.model_name}")
        return True
    
    def stop(self) -> bool:
        """Stop monitoring.
        
        Returns:
            bool: True if monitoring stopped successfully, False otherwise
        """
        if not self.running:
            logger.warning("Monitoring is not running")
            return False
        
        # Stop monitoring thread
        self.running = False
        
        # Wait for monitoring thread to terminate
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5.0)
            if self.monitoring_thread.is_alive():
                logger.warning("Monitoring thread did not terminate gracefully")
        
        self.monitoring_thread = None
        
        # Save final results
        self._save_results()
        
        logger.info(f"Stopped performance monitoring for {self.config.model_name}")
        return True
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        logger.info(f"Starting monitoring loop for {self.config.model_name}")
        
        while self.running:
            loop_start_time = time.time()
            
            try:
                # Collect metrics
                self._collect_metrics()
                
                # Check for alerts
                self._check_alerts()
                
                # Save results periodically
                if time.time() - self.last_save_time > self.config.save_interval:
                    self._save_results()
                    self.last_save_time = time.time()
                
                # Sleep to maintain sampling interval
                execution_time = time.time() - loop_start_time
                sleep_duration = max(0, self.config.sampling_interval - execution_time)
                if sleep_duration > 0:
                    time.sleep(sleep_duration)
                else:
                    logger.warning(f"Monitoring execution time ({execution_time:.4f} s) exceeds "
                                  f"sampling interval ({self.config.sampling_interval:.4f} s)")
            
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(1.0)  # Sleep on error
        
        logger.info("Monitoring loop terminated")
    
    def _collect_metrics(self):
        """Collect performance metrics."""
        timestamp = time.time()
        
        # Collect CPU usage
        if "cpu_usage" in self.metrics:
            cpu_percent = self.process.cpu_percent()
            self.metrics["cpu_usage"].append(PerformanceMetric(
                name="cpu_usage",
                value=cpu_percent,
                timestamp=timestamp,
                unit="%",
                threshold_max=self.config.alert_thresholds.get("cpu_usage", {}).get("max", 90.0),
                is_critical=True
            ))
        
        # Collect memory usage
        if "memory_usage" in self.metrics:
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)  # Convert to MB
            self.metrics["memory_usage"].append(PerformanceMetric(
                name="memory_usage",
                value=memory_mb,
                timestamp=timestamp,
                unit="MB",
                threshold_max=self.config.alert_thresholds.get("memory_usage", {}).get("max", 1000.0),
                is_critical=True
            ))
        
        # Collect model execution time
        if "execution_time" in self.metrics and hasattr(self.simulink_bridge, "last_execution_time"):
            execution_time = getattr(self.simulink_bridge, "last_execution_time", 0.0) * 1000  # Convert to ms
            self.metrics["execution_time"].append(PerformanceMetric(
                name="execution_time",
                value=execution_time,
                timestamp=timestamp,
                unit="ms",
                threshold_max=self.config.alert_thresholds.get("execution_time", {}).get("max", 50.0),
                is_critical=True
            ))
        
        # Collect model accuracy
        if "accuracy" in self.metrics and hasattr(self.simulink_bridge, "last_accuracy"):
            accuracy = getattr(self.simulink_bridge, "last_accuracy", 0.0)
            self.metrics["accuracy"].append(PerformanceMetric(
                name="accuracy",
                value=accuracy,
                timestamp=timestamp,
                unit="%",
                threshold_min=self.config.alert_thresholds.get("accuracy", {}).get("min", 90.0),
                is_critical=True
            ))
        
        # Collect model latency
        if "latency" in self.metrics and hasattr(self.simulink_bridge, "last_latency"):
            latency = getattr(self.simulink_bridge, "last_latency", 0.0) * 1000  # Convert to ms
            self.metrics["latency"].append(PerformanceMetric(
                name="latency",
                value=latency,
                timestamp=timestamp,
                unit="ms",
                threshold_max=self.config.alert_thresholds.get("latency", {}).get("max", 100.0),
                is_critical=True
            ))
        
        # Collect model throughput
        if "throughput" in self.metrics and hasattr(self.simulink_bridge, "last_throughput"):
            throughput = getattr(self.simulink_bridge, "last_throughput", 0.0)
            self.metrics["throughput"].append(PerformanceMetric(
                name="throughput",
                value=throughput,
                timestamp=timestamp,
                unit="samples/s",
                threshold_min=self.config.alert_thresholds.get("throughput", {}).get("min", 10.0),
                is_critical=False
            ))
        
        # Collect model error rate
        if "error_rate" in self.metrics and hasattr(self.simulink_bridge, "last_error_rate"):
            error_rate = getattr(self.simulink_bridge, "last_error_rate", 0.0)
            self.metrics["error_rate"].append(PerformanceMetric(
                name="error_rate",
                value=error_rate,
                timestamp=timestamp,
                unit="%",
                threshold_max=self.config.alert_thresholds.get("error_rate", {}).get("max", 5.0),
                is_critical=True
            ))
        
        # Collect model prediction error
        if "prediction_error" in self.metrics and hasattr(self.simulink_bridge, "last_prediction_error"):
            prediction_error = getattr(self.simulink_bridge, "last_prediction_error", 0.0)
            self.metrics["prediction_error"].append(PerformanceMetric(
                name="prediction_error",
                value=prediction_error,
                timestamp=timestamp,
                unit="",
                threshold_max=self.config.alert_thresholds.get("prediction_error", {}).get("max", 0.1),
                is_critical=False
            ))
        
        # Collect model profit
        if "profit" in self.metrics and hasattr(self.simulink_bridge, "last_profit"):
            profit = getattr(self.simulink_bridge, "last_profit", 0.0)
            self.metrics["profit"].append(PerformanceMetric(
                name="profit",
                value=profit,
                timestamp=timestamp,
                unit="$",
                threshold_min=self.config.alert_thresholds.get("profit", {}).get("min", 0.0),
                is_critical=False
            ))
    
    def _check_alerts(self):
        """Check for performance alerts."""
        for metric_name, metrics in self.metrics.items():
            if not metrics:
                continue
            
            # Get the latest metric
            latest_metric = metrics[-1]
            
            # Check if metric is outside thresholds
            if latest_metric.value < latest_metric.threshold_min:
                # Create alert for below minimum threshold
                alert = PerformanceAlert(
                    metric_name=metric_name,
                    value=latest_metric.value,
                    threshold=latest_metric.threshold_min,
                    timestamp=latest_metric.timestamp,
                    message=f"{metric_name} is below minimum threshold: {latest_metric.value:.2f} {latest_metric.unit} (min: {latest_metric.threshold_min:.2f} {latest_metric.unit})",
                    severity="critical" if latest_metric.is_critical else "warning"
                )
                self._handle_alert(alert)
            
            elif latest_metric.value > latest_metric.threshold_max:
                # Create alert for above maximum threshold
                alert = PerformanceAlert(
                    metric_name=metric_name,
                    value=latest_metric.value,
                    threshold=latest_metric.threshold_max,
                    timestamp=latest_metric.timestamp,
                    message=f"{metric_name} is above maximum threshold: {latest_metric.value:.2f} {latest_metric.unit} (max: {latest_metric.threshold_max:.2f} {latest_metric.unit})",
                    severity="critical" if latest_metric.is_critical else "warning"
                )
                self._handle_alert(alert)
            
            # Check if any existing alerts for this metric can be resolved
            for alert in self.alerts:
                if alert.metric_name == metric_name and not alert.is_resolved:
                    if (alert.threshold == latest_metric.threshold_min and latest_metric.value >= latest_metric.threshold_min) or \
                       (alert.threshold == latest_metric.threshold_max and latest_metric.value <= latest_metric.threshold_max):
                        # Resolve the alert
                        alert.is_resolved = True
                        alert.resolution_time = time.time()
                        alert.resolution_message = f"{metric_name} is back within thresholds: {latest_metric.value:.2f} {latest_metric.unit}"
                        
                        # Log resolution
                        log_method = logger.info
                        if alert.severity == "warning":
                            log_method = logger.warning
                        elif alert.severity == "critical":
                            log_method = logger.error
                        
                        log_method(f"Alert resolved: {alert.resolution_message}")
    
    def _handle_alert(self, alert: PerformanceAlert):
        """Handle a performance alert.
        
        Args:
            alert: Performance alert to handle
        """
        # Check if this is a duplicate of an existing unresolved alert
        for existing_alert in self.alerts:
            if existing_alert.metric_name == alert.metric_name and not existing_alert.is_resolved:
                # Don't create duplicate alerts
                return
        
        # Add to alerts list
        self.alerts.append(alert)
        
        # Log the alert
        log_method = logger.info
        if alert.severity == "warning":
            log_method = logger.warning
        elif alert.severity == "critical":
            log_method = logger.error
        
        log_method(f"Alert: {alert.message}")
        
        # Send notifications if configured
        self._send_alert_notification(alert)
    
    def _send_alert_notification(self, alert: PerformanceAlert):
        """Send a notification for an alert.
        
        Args:
            alert: Alert to send notification for
        """
        # TODO: Implement notification sending
        # This would typically involve sending emails, Slack messages, etc.
        pass
    
    def _save_results(self):
        """Save monitoring results to file."""
        # Create output directory if it doesn't exist
        os.makedirs(self.config.output_dir, exist_ok=True)
        
        # Create timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save metrics to CSV
        metrics_data = []
        for metric_name, metrics in self.metrics.items():
            for metric in metrics:
                metrics_data.append({
                    "metric_name": metric.name,
                    "value": metric.value,
                    "timestamp": metric.timestamp,
                    "unit": metric.unit
                })
        
        if metrics_data:
            metrics_df = pd.DataFrame(metrics_data)
            metrics_file = os.path.join(self.config.output_dir, f"{self.config.model_name}_metrics_{timestamp}.csv")
            metrics_df.to_csv(metrics_file, index=False)
            logger.info(f"Saved metrics to {metrics_file}")
        
        # Save alerts to JSON
        alerts_data = []
        for alert in self.alerts:
            alerts_data.append({
                "metric_name": alert.metric_name,
                "value": alert.value,
                "threshold": alert.threshold,
                "timestamp": alert.timestamp,
                "message": alert.message,
                "severity": alert.severity,
                "is_resolved": alert.is_resolved,
                "resolution_time": alert.resolution_time,
                "resolution_message": alert.resolution_message
            })
        
        if alerts_data:
            alerts_file = os.path.join(self.config.output_dir, f"{self.config.model_name}_alerts_{timestamp}.json")
            with open(alerts_file, 'w') as f:
                json.dump(alerts_data, f, indent=2)
            logger.info(f"Saved alerts to {alerts_file}")
        
        # Generate visualizations if enabled
        if self.config.visualization_enabled:
            self._generate_visualizations(timestamp)
    
    def _generate_visualizations(self, timestamp: str):
        """Generate visualizations of monitoring data.
        
        Args:
            timestamp: Timestamp for filenames
        """
        # Create output directory if it doesn't exist
        viz_dir = os.path.join(self.config.output_dir, "visualizations")
        os.makedirs(viz_dir, exist_ok=True)
        
        # Generate time series plots for each metric
        for metric_name, metrics in self.metrics.items():
            if not metrics:
                continue
            
            # Extract data
            values = [m.value for m in metrics]
            timestamps = [datetime.fromtimestamp(m.timestamp) for m in metrics]
            
            if not values or not timestamps:
                continue
            
            # Create figure
            plt.figure(figsize=(10, 6))
            plt.plot(timestamps, values, marker='o', linestyle='-', markersize=3)
            
            # Add threshold lines if applicable
            if metrics[0].threshold_min > float('-inf'):
                plt.axhline(y=metrics[0].threshold_min, color='r', linestyle='--', label=f'Min Threshold ({metrics[0].threshold_min})')
            
            if metrics[0].threshold_max < float('inf'):
                plt.axhline(y=metrics[0].threshold_max, color='r', linestyle='--', label=f'Max Threshold ({metrics[0].threshold_max})')
            
            # Add labels and title
            plt.title(f"{metric_name.replace('_', ' ').title()} - {self.config.model_name}")
            plt.xlabel("Time")
            plt.ylabel(f"{metric_name.replace('_', ' ').title()} ({metrics[0].unit})")
            plt.grid(True, alpha=0.3)
            
            # Add legend if thresholds are shown
            if metrics[0].threshold_min > float('-inf') or metrics[0].threshold_max < float('inf'):
                plt.legend()
            
            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45)
            
            # Tight layout
            plt.tight_layout()
            
            # Save figure
            filename = f"{self.config.model_name}_{metric_name}_{timestamp}.png"
            filepath = os.path.join(viz_dir, filename)
            plt.savefig(filepath)
            plt.close()
            
            logger.debug(f"Saved visualization to {filepath}")
        
        # Generate summary dashboard
        self._generate_dashboard(timestamp, viz_dir)
    
    def _generate_dashboard(self, timestamp: str, viz_dir: str):
        """Generate a summary dashboard of all metrics.
        
        Args:
            timestamp: Timestamp for filenames
            viz_dir: Directory to save visualizations
        """
        # Only generate dashboard if we have metrics
        if not any(metrics for metrics in self.metrics.values()):
            return
        
        # Create figure with subplots
        n_metrics = len(self.metrics)
        if n_metrics == 0:
            return
        
        # Calculate grid dimensions
        n_cols = min(3, n_metrics)
        n_rows = (n_metrics + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 4 * n_rows))
        
        # Flatten axes array for easier indexing
        if n_rows == 1 and n_cols == 1:
            axes = np.array([axes])
        elif n_rows == 1 or n_cols == 1:
            axes = axes.flatten()
        
        # Plot each metric
        for i, (metric_name, metrics) in enumerate(self.metrics.items()):
            if not metrics:
                continue
            
            # Get axis for this metric
            if i < len(axes):
                ax = axes[i]
            else:
                continue
            
            # Extract data
            values = [m.value for m in metrics]
            timestamps = [datetime.fromtimestamp(m.timestamp) for m in metrics]
            
            if not values or not timestamps:
                continue
            
            # Plot data
            ax.plot(timestamps, values, marker='o', linestyle='-', markersize=3)
            
            # Add threshold lines if applicable
            if metrics[0].threshold_min > float('-inf'):
                ax.axhline(y=metrics[0].threshold_min, color='r', linestyle='--', label=f'Min ({metrics[0].threshold_min})')
            
            if metrics[0].threshold_max < float('inf'):
                ax.axhline(y=metrics[0].threshold_max, color='r', linestyle='--', label=f'Max ({metrics[0].threshold_max})')
            
            # Add labels
            ax.set_title(f"{metric_name.replace('_', ' ').title()}")
            ax.set_xlabel("Time")
            ax.set_ylabel(f"{metrics[0].unit}")
            ax.grid(True, alpha=0.3)
            
            # Add legend if thresholds are shown
            if metrics[0].threshold_min > float('-inf') or metrics[0].threshold_max < float('inf'):
                ax.legend(loc='best', fontsize='small')
            
            # Rotate x-axis labels for better readability
            ax.tick_params(axis='x', rotation=45)
        
        # Hide unused subplots
        for i in range(len(self.metrics), len(axes)):
            if i < len(axes):
                axes[i].axis('off')
        
        # Add overall title
        fig.suptitle(f"{self.config.model_name} - Performance Dashboard - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", fontsize=16)
        
        # Tight layout
        fig.tight_layout(rect=[0, 0, 1, 0.97])  # Leave room for suptitle
        
        # Save figure
        filename = f"{self.config.model_name}_dashboard_{timestamp}.png"
        filepath = os.path.join(viz_dir, filename)
        plt.savefig(filepath)
        plt.close()
        
        logger.info(f"Saved dashboard to {filepath}")
    
    def get_metrics(self, metric_name: str = None) -> Dict[str, List[PerformanceMetric]]:
        """Get collected metrics.
        
        Args:
            metric_name: Name of the metric to get (None for all metrics)
            
        Returns:
            Dict[str, List[PerformanceMetric]]: Collected metrics
        """
        if metric_name:
            if metric_name in self.metrics:
                return {metric_name: list(self.metrics[metric_name])}
            else:
                return {}
        else:
            return {name: list(metrics) for name, metrics in self.metrics.items()}
    
    def get_alerts(self, resolved: bool = None) -> List[PerformanceAlert]:
        """Get performance alerts.
        
        Args:
            resolved: Filter by resolution status (None for all alerts)
            
        Returns:
            List[PerformanceAlert]: Performance alerts
        """
        if resolved is None:
            return self.alerts
        else:
            return [alert for alert in self.alerts if alert.is_resolved == resolved]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of monitoring results.
        
        Returns:
            Dict[str, Any]: Monitoring summary
        """
        summary = {
            "model_name": self.config.model_name,
            "monitoring_start_time": self.last_save_time - self.config.save_interval if self.last_save_time > 0 else time.time(),
            "current_time": time.time(),
            "metrics_summary": {},
            "alerts_summary": {
                "total": len(self.alerts),
                "active": len([a for a in self.alerts if not a.is_resolved]),
                "resolved": len([a for a in self.alerts if a.is_resolved]),
                "critical": len([a for a in self.alerts if a.severity == "critical"]),
                "warning": len([a for a in self.alerts if a.severity == "warning"]),
                "info": len([a for a in self.alerts if a.severity == "info"])
            }
        }
        
        # Calculate summary statistics for each metric
        for metric_name, metrics in self.metrics.items():
            if not metrics:
                continue
            
            values = [m.value for m in metrics]
            
            summary["metrics_summary"][metric_name] = {
                "current": values[-1] if values else None,
                "min": min(values) if values else None,
                "max": max(values) if values else None,
                "mean": np.mean(values) if values else None,
                "median": np.median(values) if values else None,
                "std": np.std(values) if values else None,
                "unit": metrics[0].unit if metrics else "",
                "samples": len(values)
            }
        
        return summary


def create_default_monitoring_config(model_name: str) -> MonitoringConfig:
    """Create a default monitoring configuration.
    
    Args:
        model_name: Name of the model to monitor
        
    Returns:
        MonitoringConfig: Default monitoring configuration
    """
    # Create output directory
    output_dir = os.path.join("simulink", "monitoring_results", model_name)
    os.makedirs(output_dir, exist_ok=True)
    
    return MonitoringConfig(
        model_name=model_name,
        metrics=[
            "cpu_usage",
            "memory_usage",
            "execution_time",
            "latency",
            "throughput",
            "error_rate",
            "accuracy",
            "profit"
        ],
        sampling_interval=1.0,
        window_size=60,
        alert_thresholds={
            "cpu_usage": {"max": 90.0},
            "memory_usage": {"max": 1000.0},
            "execution_time": {"max": 50.0},
            "latency": {"max": 100.0},
            "throughput": {"min": 10.0},
            "error_rate": {"max": 5.0},
            "accuracy": {"min": 90.0},
            "profit": {"min": 0.0}
        },
        output_dir=output_dir,
        save_interval=60,
        visualization_enabled=True,
        notification_endpoints=[],
        log_level="INFO"
    )


def main():
    """Run a demo of the performance monitoring framework."""
    from simulink_bridge import SimulinkBridge
    
    # Create Simulink bridge
    bridge = SimulinkBridge()
    
    # Add mock performance data to bridge for demo purposes
    bridge.last_execution_time = 0.02  # 20 ms
    bridge.last_latency = 0.05  # 50 ms
    bridge.last_throughput = 20.0  # 20 samples/s
    bridge.last_error_rate = 2.0  # 2%
    bridge.last_accuracy = 95.0  # 95%
    bridge.last_profit = 0.05  # $0.05
    bridge.last_prediction_error = 0.08  # 0.08
    
    # Create monitoring configuration
    config = create_default_monitoring_config("Arbitrage_Strategy_Model")
    
    # Create performance monitor
    monitor = PerformanceMonitor(bridge, config)
    
    try:
        # Start monitoring
        print("Starting performance monitoring...")
        monitor.start()
        
        # Simulate changing metrics for demo
        for i in range(30):
            # Update mock performance data with some variation
            bridge.last_execution_time = 0.02 + 0.01 * np.sin(i * 0.2)  # 20-30 ms
            bridge.last_latency = 0.05 + 0.02 * np.sin(i * 0.3)  # 50-70 ms
            bridge.last_throughput = 20.0 + 5.0 * np.sin(i * 0.1)  # 15-25 samples/s
            bridge.last_error_rate = 2.0 + 1.0 * np.sin(i * 0.4)  # 1-3%
            bridge.last_accuracy = 95.0 + 2.0 * np.sin(i * 0.2)  # 93-97%
            bridge.last_profit = 0.05 + 0.02 * np.sin(i * 0.5)  # $0.03-0.07
            
            # Simulate a spike in execution time around iteration 15
            if i == 15:
                bridge.last_execution_time = 0.08  # 80 ms - should trigger alert
                bridge.last_error_rate = 6.0  # 6% - should trigger alert
            
            # Print current status
            summary = monitor.get_summary()
            metrics = summary["metrics_summary"]
            
            print(f"\rIteration {i+1}/30 | "
                  f"CPU: {metrics.get('cpu_usage', {}).get('current', 0):.1f}% | "
                  f"Memory: {metrics.get('memory_usage', {}).get('current', 0):.1f} MB | "
                  f"Execution: {metrics.get('execution_time', {}).get('current', 0):.1f} ms | "
                  f"Alerts: {summary['alerts_summary']['active']} active", end="")
            
            time.sleep(1.0)
        
        print("\n\nMonitoring complete!")
        
        # Get final summary
        summary = monitor.get_summary()
        
        print("\nPerformance Summary:")
        for metric_name, metric_summary in summary["metrics_summary"].items():
            print(f"  {metric_name.replace('_', ' ').title()}: "
                  f"Current={metric_summary['current']:.2f} {metric_summary['unit']}, "
                  f"Min={metric_summary['min']:.2f}, "
                  f"Max={metric_summary['max']:.2f}, "
                  f"Mean={metric_summary['mean']:.2f}")
        
        print("\nAlerts Summary:")
        print(f"  Total: {summary['alerts_summary']['total']}")
        print(f"  Active: {summary['alerts_summary']['active']}")
        print(f"  Resolved: {summary['alerts_summary']['resolved']}")
        print(f"  Critical: {summary['alerts_summary']['critical']}")
        print(f"  Warning: {summary['alerts_summary']['warning']}")
        
        # Print active alerts
        active_alerts = monitor.get_alerts(resolved=False)
        if active_alerts:
            print("\nActive Alerts:")
            for alert in active_alerts:
                print(f"  [{alert.severity.upper()}] {alert.message}")
        
    except KeyboardInterrupt:
        print("\nMonitoring interrupted by user")
    finally:
        # Stop monitoring
        monitor.stop()


if __name__ == "__main__":
    main()