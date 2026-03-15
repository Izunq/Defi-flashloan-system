#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hardware-in-the-Loop Testing Framework for Simulink Models

This module provides a framework for testing Simulink models with real hardware.
It enables real-time execution of models on dedicated hardware and provides
interfaces for data acquisition and control.

Author: DeFi Arbitrage System
Date: June 17, 2025
"""

import os
import time
import logging
import numpy as np
import threading
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass

# Import the Simulink bridge
from simulink_bridge import SimulinkBridge, MarketData, TradingSignals

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('hardware_in_the_loop')

@dataclass
class HardwareConfig:
    """Configuration for hardware-in-the-loop testing."""
    device_id: str
    sampling_rate: int  # Hz
    buffer_size: int
    input_channels: List[str]
    output_channels: List[str]
    calibration_factors: Dict[str, float]
    latency_threshold_ms: float


class HardwareInterface:
    """Interface for hardware communication."""
    
    def __init__(self, device_id: str):
        """Initialize the hardware interface.
        
        Args:
            device_id: Identifier for the hardware device
        """
        self.device_id = device_id
        self.is_connected = False
        logger.info(f"Initializing hardware interface for device {device_id}")
    
    def connect(self) -> bool:
        """Connect to the hardware device.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        # Simulate hardware connection
        logger.info(f"Connecting to hardware device {self.device_id}")
        time.sleep(0.5)  # Simulate connection time
        self.is_connected = True
        logger.info(f"Successfully connected to hardware device {self.device_id}")
        return True
    
    def disconnect(self) -> bool:
        """Disconnect from the hardware device.
        
        Returns:
            bool: True if disconnection successful, False otherwise
        """
        if not self.is_connected:
            logger.warning(f"Device {self.device_id} is not connected")
            return False
        
        # Simulate hardware disconnection
        logger.info(f"Disconnecting from hardware device {self.device_id}")
        time.sleep(0.2)  # Simulate disconnection time
        self.is_connected = False
        logger.info(f"Successfully disconnected from hardware device {self.device_id}")
        return True
    
    def read_data(self, channels: List[str]) -> Dict[str, float]:
        """Read data from the hardware device.
        
        Args:
            channels: List of channel names to read from
            
        Returns:
            Dict[str, float]: Dictionary mapping channel names to values
        """
        if not self.is_connected:
            logger.error(f"Cannot read data: Device {self.device_id} is not connected")
            return {}
        
        # Simulate hardware data reading
        data = {}
        for channel in channels:
            # Generate realistic-looking market data
            if 'price' in channel.lower():
                data[channel] = 1000.0 + np.random.normal(0, 5.0)
            elif 'volume' in channel.lower():
                data[channel] = 100000.0 + np.random.normal(0, 10000.0)
            elif 'gas' in channel.lower():
                data[channel] = 50.0 + np.random.normal(0, 5.0)
            else:
                data[channel] = np.random.normal(0, 1.0)
        
        return data
    
    def write_data(self, data: Dict[str, float]) -> bool:
        """Write data to the hardware device.
        
        Args:
            data: Dictionary mapping channel names to values
            
        Returns:
            bool: True if write successful, False otherwise
        """
        if not self.is_connected:
            logger.error(f"Cannot write data: Device {self.device_id} is not connected")
            return False
        
        # Simulate hardware data writing
        logger.debug(f"Writing data to device {self.device_id}: {data}")
        time.sleep(0.001)  # Simulate write time (1ms)
        return True


class HardwareInTheLoop:
    """Hardware-in-the-Loop testing framework for Simulink models."""
    
    def __init__(
        self, 
        simulink_bridge: SimulinkBridge,
        hardware_config: HardwareConfig
    ):
        """Initialize the Hardware-in-the-Loop testing framework.
        
        Args:
            simulink_bridge: Instance of SimulinkBridge for model execution
            hardware_config: Configuration for hardware interface
        """
        self.simulink_bridge = simulink_bridge
        self.config = hardware_config
        self.hardware = HardwareInterface(hardware_config.device_id)
        self.running = False
        self.thread = None
        self.data_buffer = []
        self.performance_metrics = {
            'latency_ms': [],
            'execution_time_ms': [],
            'data_throughput_kbps': []
        }
        logger.info("Hardware-in-the-Loop testing framework initialized")
    
    def connect_hardware(self) -> bool:
        """Connect to the hardware device.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        return self.hardware.connect()
    
    def disconnect_hardware(self) -> bool:
        """Disconnect from the hardware device.
        
        Returns:
            bool: True if disconnection successful, False otherwise
        """
        return self.hardware.disconnect()
    
    def start_real_time_testing(self, model_name: str) -> bool:
        """Start real-time testing of a Simulink model with hardware.
        
        Args:
            model_name: Name of the Simulink model to test
            
        Returns:
            bool: True if testing started successfully, False otherwise
        """
        if self.running:
            logger.warning("Real-time testing is already running")
            return False
        
        # Connect to hardware if not already connected
        if not self.hardware.is_connected:
            if not self.connect_hardware():
                logger.error("Failed to connect to hardware")
                return False
        
        # Load the Simulink model
        if not self.simulink_bridge.load_model(model_name):
            logger.error(f"Failed to load Simulink model {model_name}")
            return False
        
        # Start real-time simulation
        if not self.simulink_bridge.start_real_time_simulation(model_name):
            logger.error(f"Failed to start real-time simulation for model {model_name}")
            return False
        
        # Start the testing thread
        self.running = True
        self.thread = threading.Thread(
            target=self._real_time_testing_loop,
            args=(model_name,)
        )
        self.thread.daemon = True
        self.thread.start()
        
        logger.info(f"Started real-time testing for model {model_name}")
        return True
    
    def stop_real_time_testing(self) -> bool:
        """Stop real-time testing.
        
        Returns:
            bool: True if testing stopped successfully, False otherwise
        """
        if not self.running:
            logger.warning("Real-time testing is not running")
            return False
        
        # Stop the testing thread
        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)
            if self.thread.is_alive():
                logger.warning("Testing thread did not terminate gracefully")
        
        # Stop the real-time simulation
        model_name = self.simulink_bridge.current_model
        if model_name:
            if not self.simulink_bridge.stop_real_time_simulation(model_name):
                logger.error(f"Failed to stop real-time simulation for model {model_name}")
                return False
        
        # Disconnect from hardware
        if self.hardware.is_connected:
            if not self.disconnect_hardware():
                logger.error("Failed to disconnect from hardware")
                return False
        
        logger.info("Stopped real-time testing")
        return True
    
    def _real_time_testing_loop(self, model_name: str):
        """Real-time testing loop.
        
        Args:
            model_name: Name of the Simulink model being tested
        """
        logger.info(f"Starting real-time testing loop for model {model_name}")
        
        # Calculate sleep time based on sampling rate
        sleep_time = 1.0 / self.config.sampling_rate
        
        while self.running:
            loop_start_time = time.time()
            
            try:
                # Read data from hardware
                input_data = self.hardware.read_data(self.config.input_channels)
                
                # Convert to MarketData object
                market_data = MarketData(
                    timestamp=time.time(),
                    prices={k: v for k, v in input_data.items() if 'price' in k.lower()},
                    volumes={k: v for k, v in input_data.items() if 'volume' in k.lower()},
                    gas_prices={k: v for k, v in input_data.items() if 'gas' in k.lower()},
                    additional_data={k: v for k, v in input_data.items() 
                                    if not any(x in k.lower() for x in ['price', 'volume', 'gas'])}
                )
                
                # Process data through Simulink model
                process_start_time = time.time()
                trading_signals = self.simulink_bridge.process_market_data(market_data)
                process_end_time = time.time()
                
                if trading_signals:
                    # Convert trading signals to output data
                    output_data = {
                        'trade_action': 1.0 if trading_signals.execute_trade else 0.0,
                        'position_size': trading_signals.position_size,
                        'target_price': trading_signals.target_price,
                        'stop_loss': trading_signals.stop_loss,
                        'confidence': trading_signals.confidence
                    }
                    
                    # Write output data to hardware
                    self.hardware.write_data(output_data)
                    
                    # Store data for analysis
                    self.data_buffer.append((market_data, trading_signals))
                    if len(self.data_buffer) > self.config.buffer_size:
                        self.data_buffer.pop(0)
                    
                    # Calculate performance metrics
                    latency_ms = (process_end_time - process_start_time) * 1000
                    self.performance_metrics['latency_ms'].append(latency_ms)
                    
                    # Check if latency exceeds threshold
                    if latency_ms > self.config.latency_threshold_ms:
                        logger.warning(f"Latency ({latency_ms:.2f} ms) exceeds threshold "
                                      f"({self.config.latency_threshold_ms:.2f} ms)")
                
                # Calculate execution time
                execution_time = time.time() - loop_start_time
                self.performance_metrics['execution_time_ms'].append(execution_time * 1000)
                
                # Sleep to maintain sampling rate
                sleep_duration = max(0, sleep_time - execution_time)
                if sleep_duration > 0:
                    time.sleep(sleep_duration)
                else:
                    logger.warning(f"Execution time ({execution_time:.4f} s) exceeds "
                                  f"sampling period ({sleep_time:.4f} s)")
            
            except Exception as e:
                logger.error(f"Error in real-time testing loop: {str(e)}")
                # Continue running despite errors
        
        logger.info("Real-time testing loop terminated")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get a report of performance metrics.
        
        Returns:
            Dict[str, Any]: Dictionary of performance metrics
        """
        if not self.performance_metrics['latency_ms']:
            return {"status": "No data available"}
        
        return {
            "latency_ms": {
                "mean": np.mean(self.performance_metrics['latency_ms']),
                "min": np.min(self.performance_metrics['latency_ms']),
                "max": np.max(self.performance_metrics['latency_ms']),
                "std": np.std(self.performance_metrics['latency_ms']),
                "p95": np.percentile(self.performance_metrics['latency_ms'], 95),
                "p99": np.percentile(self.performance_metrics['latency_ms'], 99)
            },
            "execution_time_ms": {
                "mean": np.mean(self.performance_metrics['execution_time_ms']),
                "min": np.min(self.performance_metrics['execution_time_ms']),
                "max": np.max(self.performance_metrics['execution_time_ms']),
                "std": np.std(self.performance_metrics['execution_time_ms']),
                "p95": np.percentile(self.performance_metrics['execution_time_ms'], 95),
                "p99": np.percentile(self.performance_metrics['execution_time_ms'], 99)
            },
            "samples_processed": len(self.performance_metrics['latency_ms']),
            "buffer_utilization": len(self.data_buffer) / self.config.buffer_size,
            "real_time_performance": {
                "target_rate_hz": self.config.sampling_rate,
                "achieved_rate_hz": 1000 / np.mean(self.performance_metrics['execution_time_ms']),
                "missed_deadlines": sum(1 for t in self.performance_metrics['execution_time_ms'] 
                                       if t > (1000 / self.config.sampling_rate))
            }
        }
    
    def run_stress_test(self, model_name: str, duration_seconds: int = 60) -> Dict[str, Any]:
        """Run a stress test on the model.
        
        Args:
            model_name: Name of the Simulink model to test
            duration_seconds: Duration of the stress test in seconds
            
        Returns:
            Dict[str, Any]: Stress test results
        """
        logger.info(f"Starting stress test for model {model_name} ({duration_seconds} seconds)")
        
        # Start real-time testing
        if not self.start_real_time_testing(model_name):
            logger.error("Failed to start real-time testing for stress test")
            return {"status": "Failed to start testing"}
        
        # Run for specified duration
        try:
            time.sleep(duration_seconds)
        except KeyboardInterrupt:
            logger.info("Stress test interrupted by user")
        finally:
            # Stop real-time testing
            self.stop_real_time_testing()
        
        # Get performance report
        report = self.get_performance_report()
        report["stress_test_duration_seconds"] = duration_seconds
        
        logger.info(f"Stress test completed: processed {report['samples_processed']} samples")
        return report


def create_default_hardware_config() -> HardwareConfig:
    """Create a default hardware configuration.
    
    Returns:
        HardwareConfig: Default hardware configuration
    """
    return HardwareConfig(
        device_id="SIM-HIL-01",
        sampling_rate=1000,  # 1 kHz
        buffer_size=10000,
        input_channels=[
            "eth_price", "btc_price", "uni_price", "aave_price",
            "eth_volume", "btc_volume", "uni_volume", "aave_volume",
            "gas_price_fast", "gas_price_standard", "gas_price_slow",
            "network_congestion", "block_time"
        ],
        output_channels=[
            "trade_action", "position_size", "target_price", 
            "stop_loss", "confidence"
        ],
        calibration_factors={
            "eth_price": 1.0,
            "btc_price": 1.0,
            "uni_price": 1.0,
            "aave_price": 1.0
        },
        latency_threshold_ms=5.0  # 5ms latency threshold
    )


def main():
    """Run a demo of the Hardware-in-the-Loop testing framework."""
    from simulink_bridge import SimulinkBridge
    
    # Create Simulink bridge
    bridge = SimulinkBridge()
    
    # Create hardware-in-the-loop framework
    hardware_config = create_default_hardware_config()
    hil = HardwareInTheLoop(bridge, hardware_config)
    
    try:
        # Run a stress test
        model_name = "High_Frequency_Trading_System"
        print(f"Running stress test on {model_name}...")
        results = hil.run_stress_test(model_name, duration_seconds=10)
        
        # Print results
        print("\nStress Test Results:")
        print(f"Samples processed: {results['samples_processed']}")
        print(f"Mean latency: {results['latency_ms']['mean']:.2f} ms")
        print(f"95th percentile latency: {results['latency_ms']['p95']:.2f} ms")
        print(f"Target sampling rate: {results['real_time_performance']['target_rate_hz']} Hz")
        print(f"Achieved sampling rate: {results['real_time_performance']['achieved_rate_hz']:.2f} Hz")
        print(f"Missed deadlines: {results['real_time_performance']['missed_deadlines']}")
        
    except KeyboardInterrupt:
        print("Demo interrupted by user")
    finally:
        # Ensure cleanup
        if hil.running:
            hil.stop_real_time_testing()


if __name__ == "__main__":
    main()