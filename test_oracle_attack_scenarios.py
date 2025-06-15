#!/usr/bin/env python3
"""
Oracle Attack Scenario Simulator

This module provides comprehensive simulation of various oracle attack scenarios
to test the resilience and detection capabilities of the oracle security system.
"""

import asyncio
import json
import time
import logging
import os
import yaml
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from web3 import Web3
from web3.exceptions import ContractLogicError
from unittest.mock import Mock, patch, MagicMock, AsyncMock

# Import the system under test
try:
    from enhanced_oracle_security_monitor import (
        EnhancedOracleSecurityMonitor,
        PriceData,
        SecurityAlert,
        OracleMetrics
    )
    MONITOR_CLASS = EnhancedOracleSecurityMonitor
except ImportError:
    try:
        from production_oracle_security_monitor import (
            ProductionOracleSecurityMonitor,
            PriceDataPoint as PriceData,
            SecurityIncident as SecurityAlert,
            OracleHealthMetrics as OracleMetrics
        )
        MONITOR_CLASS = ProductionOracleSecurityMonitor
    except ImportError:
        # Create mock classes for testing
        @dataclass
        class PriceData:
            asset: str
            price: float
            timestamp: int
            source: str
            confidence: float
            volume: float = 0.0
            deviation: float = 0.0

        @dataclass
        class SecurityAlert:
            alert_id: str
            alert_type: str
            severity: str
            asset: str
            price: float
            expected_price: float
            deviation: float
            timestamp: int
            description: str
            resolved: bool = False

        @dataclass
        class OracleMetrics:
            oracle_address: str
            total_updates: int
            successful_updates: int
            failed_updates: int
            average_deviation: float
            last_update: int
            reputation_score: float
            is_active: bool

        class MockOracleSecurityMonitor:
            def __init__(self, config_path: str = "test_oracle_config.yaml"):
                self.config = self._load_config(config_path)
                self.price_history = {}
                self.circuit_breaker_threshold = 1000
                
            def _load_config(self, config_path: str) -> Dict:
                return {
                    'security': {'max_price_deviation': 500},
                    'tracked_assets': ['ETH', 'BTC']
                }
                
            async def _detect_price_anomalies(self, data: PriceData) -> List[SecurityAlert]:
                # Simple anomaly detection for testing
                if data.deviation > 10.0:  # 10% threshold
                    return [SecurityAlert(
                        alert_id=f"anomaly_{int(time.time())}",
                        alert_type="PRICE_ANOMALY",
                        severity="HIGH",
                        asset=data.asset,
                        price=data.price,
                        expected_price=data.price / (1 + data.deviation / 100),
                        deviation=data.deviation,
                        timestamp=data.timestamp,
                        description=f"Price anomaly detected for {data.asset}",
                        resolved=False
                    )]
                return []
                
            async def _detect_manipulation_patterns(self, data: PriceData) -> List[SecurityAlert]:
                # Simple manipulation detection for testing
                if data.deviation > 15.0:  # 15% threshold for manipulation
                    return [SecurityAlert(
                        alert_id=f"manipulation_{int(time.time())}",
                        alert_type="PRICE_MANIPULATION",
                        severity="CRITICAL",
                        asset=data.asset,
                        price=data.price,
                        expected_price=data.price / (1 + data.deviation / 100),
                        deviation=data.deviation,
                        timestamp=data.timestamp,
                        description=f"Price manipulation detected for {data.asset}",
                        resolved=False
                    )]
                return []

        MONITOR_CLASS = MockOracleSecurityMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("oracle_attack_simulation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("OracleAttackSimulator")

class OracleAttackSimulator:
    """Simulates various oracle attack scenarios to test security systems"""
    
    def __init__(self, config_path: str = "test_oracle_config.yaml"):
        """Initialize the attack simulator"""
        self.config = self._load_config(config_path)
        self.monitor = self._setup_monitor(config_path)
        self.results = {}
        self.attack_scenarios = self._load_attack_scenarios()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'web3': {
                'provider_url': 'http://localhost:8545',
                'gas_limit': 3000000
            },
            'contracts': {
                'secure_multi_oracle': '0x1234567890123456789012345678901234567890',
                'oracle_security_wrapper': '0x2345678901234567890123456789012345678901',
                'oracle_manipulation_monitor': '0x3456789012345678901234567890123456789012'
            },
            'security': {
                'max_price_deviation': 500,  # 5%
                'circuit_breaker_threshold': 1000,  # 10%
                'min_oracle_consensus': 3,
                'staleness_threshold': 3600,  # 1 hour
                'monitoring_interval': 30,  # 30 seconds
                'anomaly_detection_window': 100  # 100 data points
            },
            'tracked_assets': ['ETH', 'BTC', 'USDC', 'USDT', 'DAI'],
            'alerts': {
                'email_notifications': False,
                'webhook_url': '',
                'telegram_bot_token': '',
                'telegram_chat_id': ''
            }
        }
    
    def _setup_monitor(self, config_path: str) -> EnhancedOracleSecurityMonitor:
        """Set up a monitor instance with mocked dependencies"""
        # Create test config if it doesn't exist
        if not os.path.exists(config_path):
            with open(config_path, 'w') as f:
                yaml.dump(self._get_default_config(), f)
        
        # Initialize the monitor
        monitor = EnhancedOracleSecurityMonitor(config_path=config_path)
        
        # Mock Web3 and contracts
        mock_w3 = MagicMock()
        mock_w3.is_connected.return_value = True
        mock_w3.to_checksum_address = lambda addr: addr
        mock_w3.keccak = lambda text: Web3.keccak(text=text)
        
        # Mock contract functions
        mock_secure_multi_oracle = MagicMock()
        mock_oracle_security_wrapper = MagicMock()
        mock_oracle_manipulation_monitor = MagicMock()
        
        # Setup contract function returns
        mock_secure_multi_oracle.functions.getPrice.return_value.call.return_value = (
            100 * 10**18,  # price in wei
            int(time.time()),  # timestamp
            100,  # deviation (1%)
            True  # is_valid
        )
        
        # Mock contracts dictionary
        mock_contracts = {
            'secure_multi_oracle': mock_secure_multi_oracle,
            'oracle_security_wrapper': mock_oracle_security_wrapper,
            'oracle_manipulation_monitor': mock_oracle_manipulation_monitor
        }
        
        # Replace real instances with mocks
        monitor.w3 = mock_w3
        monitor.contracts = mock_contracts
        
        return monitor
    
    def _load_attack_scenarios(self) -> List[Dict]:
        """Load predefined attack scenarios"""
        return [
            {
                "name": "Flash Loan Attack",
                "description": "Sudden price spike followed by return to normal",
                "asset": "ETH",
                "base_price": 1500.0,
                "attack_pattern": "flash_spike",
                "magnitude": 20.0,  # 20% spike
                "duration": 2,  # 2 time units
                "volume_increase": 5.0  # 5x normal volume
            },
            {
                "name": "Gradual Manipulation",
                "description": "Slow, consistent price manipulation over time",
                "asset": "ETH",
                "base_price": 1500.0,
                "attack_pattern": "gradual",
                "magnitude": 15.0,  # 15% total change
                "duration": 20,  # 20 time units
                "volume_increase": 1.2  # 1.2x normal volume
            },
            {
                "name": "Oscillating Manipulation",
                "description": "Price oscillation to create uncertainty",
                "asset": "BTC",
                "base_price": 30000.0,
                "attack_pattern": "oscillation",
                "magnitude": 8.0,  # 8% oscillation
                "duration": 15,  # 15 time units
                "frequency": 3  # 3 oscillations
            },
            {
                "name": "Coordinated Multi-Oracle Attack",
                "description": "Multiple oracles reporting manipulated prices",
                "asset": "USDC",
                "base_price": 1.0,
                "attack_pattern": "coordinated",
                "magnitude": 5.0,  # 5% deviation
                "duration": 10,  # 10 time units
                "affected_oracles": 0.6  # 60% of oracles affected
            },
            {
                "name": "Time-Delayed Attack",
                "description": "Manipulation with time delays to avoid detection",
                "asset": "DAI",
                "base_price": 1.0,
                "attack_pattern": "time_delayed",
                "magnitude": 12.0,  # 12% total change
                "duration": 25,  # 25 time units
                "delay_pattern": [2, 5, 3, 7, 4]  # Irregular delays
            },
            {
                "name": "Volume-Based Manipulation",
                "description": "Price manipulation with abnormal trading volumes",
                "asset": "ETH",
                "base_price": 1500.0,
                "attack_pattern": "volume_based",
                "magnitude": 10.0,  # 10% price change
                "duration": 12,  # 12 time units
                "volume_pattern": [3, 8, 15, 10, 5, 2]  # Volume multipliers
            },
            {
                "name": "Statistical Anomaly Evasion",
                "description": "Attack designed to evade statistical detection",
                "asset": "BTC",
                "base_price": 30000.0,
                "attack_pattern": "statistical_evasion",
                "magnitude": 18.0,  # 18% total change
                "duration": 30,  # 30 time units
                "evasion_technique": "adaptive"  # Adapts to detection thresholds
            }
        ]
    
    async def run_all_attack_simulations(self) -> Dict[str, Any]:
        """Run all attack simulations and collect results"""
        results = {}
        
        for scenario in self.attack_scenarios:
            logger.info(f"Running attack simulation: {scenario['name']}")
            result = await self.simulate_attack(scenario)
            results[scenario['name']] = result
            
            # Reset monitor state between scenarios
            self.monitor = self._setup_monitor("test_oracle_config.yaml")
        
        self.results = results
        return results
    
    async def simulate_attack(self, scenario: Dict) -> Dict[str, Any]:
        """Simulate a specific attack scenario"""
        asset = scenario['asset']
        base_price = scenario['base_price']
        attack_pattern = scenario['attack_pattern']
        
        # Generate normal price history first
        await self._generate_normal_price_history(asset, base_price)
        
        # Generate attack price data
        attack_data = self._generate_attack_data(scenario)
        
        # Process the attack data and collect alerts
        alerts = []
        circuit_breaker_triggered = False
        detection_time = None
        
        for i, data in enumerate(attack_data):
            # Process through the monitor
            anomaly_alerts = await self.monitor._detect_price_anomalies(data)
            manipulation_alerts = await self.monitor._detect_manipulation_patterns(data)
            
            # Collect all alerts
            all_alerts = anomaly_alerts + manipulation_alerts
            alerts.extend(all_alerts)
            
            # Check if this is the first detection
            if all_alerts and detection_time is None:
                detection_time = i
            
            # Update monitor state
            if asset not in self.monitor.price_history:
                self.monitor.price_history[asset] = []
            self.monitor.price_history[asset].append(data)
            
            # Check if circuit breaker would be triggered
            if not circuit_breaker_triggered:
                for alert in all_alerts:
                    if alert.severity == "CRITICAL" or (alert.severity == "HIGH" and alert.deviation > self.monitor.circuit_breaker_threshold / 100):
                        circuit_breaker_triggered = True
                        break
        
        # Calculate detection metrics
        detection_rate = len(alerts) / len(attack_data) if attack_data else 0
        false_positives = sum(1 for alert in alerts if alert.deviation < scenario['magnitude'] / 2)
        
        # Prepare result
        result = {
            "scenario": scenario['name'],
            "description": scenario['description'],
            "asset": asset,
            "total_data_points": len(attack_data),
            "alerts_generated": len(alerts),
            "detection_rate": detection_rate,
            "false_positives": false_positives,
            "circuit_breaker_triggered": circuit_breaker_triggered,
            "detection_time": detection_time,
            "detection_delay": detection_time if detection_time is not None else "Not detected",
            "alerts": [asdict(alert) for alert in alerts[:5]]  # Include first 5 alerts for reference
        }
        
        return result
    
    async def _generate_normal_price_history(self, asset: str, base_price: float, history_length: int = 50):
        """Generate normal price history data"""
        # Generate slightly varying but normal price history
        normal_data = []
        
        for i in range(history_length):
            # Add small random variations (±1%)
            random_factor = 1 + (np.random.random() - 0.5) * 0.02
            price = base_price * random_factor
            
            data = PriceData(
                asset=asset,
                price=price,
                timestamp=int(time.time()) - (history_length - i) * 300,  # Every 5 minutes
                source="SecureMultiOracle",
                confidence=95.0,
                volume=1000000.0,
                deviation=abs(random_factor - 1) * 100
            )
            normal_data.append(data)
        
        # Initialize price history in the monitor
        self.monitor.price_history[asset] = normal_data
    
    def _generate_attack_data(self, scenario: Dict) -> List[PriceData]:
        """Generate price data for a specific attack pattern"""
        asset = scenario['asset']
        base_price = scenario['base_price']
        attack_pattern = scenario['attack_pattern']
        magnitude = scenario['magnitude'] / 100  # Convert percentage to factor
        duration = scenario['duration']
        
        attack_data = []
        
        if attack_pattern == "flash_spike":
            # Flash loan attack - sudden spike and return
            volume_increase = scenario.get('volume_increase', 5.0)
            
            # Spike phase
            spike_price = base_price * (1 + magnitude)
            attack_data.append(PriceData(
                asset=asset,
                price=spike_price,
                timestamp=int(time.time()),
                source="SecureMultiOracle",
                confidence=95.0,
                volume=1000000.0 * volume_increase,
                deviation=magnitude * 100
            ))
            
            # Return phase
            for i in range(1, duration):
                recovery_factor = 1 + magnitude * (1 - i/duration)
                attack_data.append(PriceData(
                    asset=asset,
                    price=base_price * recovery_factor,
                    timestamp=int(time.time()) + i * 60,  # Every minute
                    source="SecureMultiOracle",
                    confidence=95.0,
                    volume=1000000.0 * (volume_increase - (volume_increase-1) * i/duration),
                    deviation=magnitude * (1 - i/duration) * 100
                ))
        
        elif attack_pattern == "gradual":
            # Gradual manipulation - slow consistent change
            for i in range(duration):
                change_factor = 1 + (magnitude * i / duration)
                attack_data.append(PriceData(
                    asset=asset,
                    price=base_price * change_factor,
                    timestamp=int(time.time()) + i * 3600,  # Every hour
                    source="SecureMultiOracle",
                    confidence=95.0,
                    volume=1000000.0 * scenario.get('volume_increase', 1.0),
                    deviation=(magnitude * i / duration) * 100
                ))
        
        elif attack_pattern == "oscillation":
            # Oscillating manipulation
            frequency = scenario.get('frequency', 3)
            for i in range(duration):
                # Sine wave oscillation
                oscillation = magnitude * np.sin(2 * np.pi * frequency * i / duration)
                attack_data.append(PriceData(
                    asset=asset,
                    price=base_price * (1 + oscillation),
                    timestamp=int(time.time()) + i * 1800,  # Every 30 minutes
                    source="SecureMultiOracle",
                    confidence=95.0,
                    volume=1000000.0,
                    deviation=abs(oscillation) * 100
                ))
        
        elif attack_pattern == "coordinated":
            # Coordinated multi-oracle attack
            affected_oracles = scenario.get('affected_oracles', 0.6)
            
            for i in range(duration):
                change_factor = 1 + (magnitude * i / duration)
                
                # Create multiple oracle entries with similar manipulated prices
                for j in range(5):  # Simulate 5 oracles
                    is_manipulated = j < (5 * affected_oracles)
                    oracle_price = base_price * (change_factor if is_manipulated else 1)
                    
                    # Add small variations between oracles
                    oracle_variation = 1 + (np.random.random() - 0.5) * 0.01
                    
                    attack_data.append(PriceData(
                        asset=asset,
                        price=oracle_price * oracle_variation,
                        timestamp=int(time.time()) + i * 1200,  # Every 20 minutes
                        source=f"Oracle{j+1}",
                        confidence=95.0,
                        volume=1000000.0,
                        deviation=abs(change_factor - 1) * 100 if is_manipulated else 0.5
                    ))
        
        elif attack_pattern == "time_delayed":
            # Time-delayed attack
            delay_pattern = scenario.get('delay_pattern', [2, 5, 3, 7, 4])
            current_time = int(time.time())
            total_change = 0
            
            for i in range(duration):
                # Apply irregular time delays
                delay = delay_pattern[i % len(delay_pattern)]
                current_time += delay * 3600  # Hours
                
                # Calculate incremental change
                step_change = magnitude / duration
                total_change += step_change
                
                attack_data.append(PriceData(
                    asset=asset,
                    price=base_price * (1 + total_change),
                    timestamp=current_time,
                    source="SecureMultiOracle",
                    confidence=95.0,
                    volume=1000000.0,
                    deviation=total_change * 100
                ))
        
        elif attack_pattern == "volume_based":
            # Volume-based manipulation
            volume_pattern = scenario.get('volume_pattern', [3, 8, 15, 10, 5, 2])
            
            for i in range(duration):
                # Calculate price change
                change_factor = 1 + (magnitude * i / duration)
                
                # Get volume multiplier
                volume_multiplier = volume_pattern[i % len(volume_pattern)]
                
                attack_data.append(PriceData(
                    asset=asset,
                    price=base_price * change_factor,
                    timestamp=int(time.time()) + i * 1800,  # Every 30 minutes
                    source="SecureMultiOracle",
                    confidence=95.0,
                    volume=1000000.0 * volume_multiplier,
                    deviation=(magnitude * i / duration) * 100
                ))
        
        elif attack_pattern == "statistical_evasion":
            # Statistical anomaly evasion
            evasion_technique = scenario.get('evasion_technique', 'adaptive')
            
            if evasion_technique == 'adaptive':
                # Create a pattern that tries to stay under statistical detection thresholds
                # by making changes that adapt to the moving average
                total_change = 0
                
                for i in range(duration):
                    # Calculate how much we can change without triggering detection
                    # This is a simplified model - in reality would be more complex
                    safe_change = min(0.02, magnitude / duration * 1.5)  # Max 2% per step
                    
                    # Apply the change
                    total_change += safe_change
                    if total_change > magnitude:
                        total_change = magnitude  # Cap at target magnitude
                    
                    # Add some randomness to evade pattern detection
                    random_factor = 1 + (np.random.random() - 0.5) * 0.005
                    
                    attack_data.append(PriceData(
                        asset=asset,
                        price=base_price * (1 + total_change) * random_factor,
                        timestamp=int(time.time()) + i * 2400,  # Every 40 minutes
                        source="SecureMultiOracle",
                        confidence=95.0,
                        volume=1000000.0 * (1 + i % 3 * 0.5),  # Slightly varying volume
                        deviation=total_change * 100
                    ))
        
        else:
            # Default pattern if none specified
            for i in range(duration):
                attack_data.append(PriceData(
                    asset=asset,
                    price=base_price * (1 + magnitude * i / duration),
                    timestamp=int(time.time()) + i * 3600,
                    source="SecureMultiOracle",
                    confidence=95.0,
                    volume=1000000.0,
                    deviation=(magnitude * i / duration) * 100
                ))
        
        return attack_data
    
    def generate_report(self, output_file: str = "oracle_attack_simulation_report.json") -> None:
        """Generate a detailed report of all attack simulations"""
        if not self.results:
            logger.warning("No simulation results to report")
            return
        
        # Calculate overall statistics
        total_scenarios = len(self.results)
        detected_scenarios = sum(1 for name, result in self.results.items() 
                               if result['alerts_generated'] > 0)
        circuit_breaker_activations = sum(1 for name, result in self.results.items() 
                                        if result['circuit_breaker_triggered'])
        
        avg_detection_rate = sum(result['detection_rate'] for result in self.results.values()) / total_scenarios
        avg_false_positives = sum(result['false_positives'] for result in self.results.values()) / total_scenarios
        
        # Prepare report
        report = {
            "summary": {
                "total_attack_scenarios": total_scenarios,
                "detected_scenarios": detected_scenarios,
                "detection_percentage": (detected_scenarios / total_scenarios) * 100,
                "circuit_breaker_activations": circuit_breaker_activations,
                "average_detection_rate": avg_detection_rate,
                "average_false_positives": avg_false_positives
            },
            "scenario_results": self.results,
            "timestamp": datetime.now().isoformat(),
            "system_info": {
                "max_price_deviation": self.monitor.max_price_deviation / 100,
                "circuit_breaker_threshold": self.monitor.circuit_breaker_threshold / 100,
                "min_oracle_consensus": self.monitor.min_oracle_consensus
            }
        }
        
        # Save report to file
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Attack simulation report saved to {output_file}")
        
        # Print summary to console
        print("\n===== ORACLE ATTACK SIMULATION SUMMARY =====")
        print(f"Total attack scenarios: {total_scenarios}")
        print(f"Detected scenarios: {detected_scenarios} ({(detected_scenarios / total_scenarios) * 100:.1f}%)")
        print(f"Circuit breaker activations: {circuit_breaker_activations}")
        print(f"Average detection rate: {avg_detection_rate:.2f}")
        print(f"Average false positives: {avg_false_positives:.2f}")
        print("===========================================\n")
    
    def visualize_results(self, output_dir: str = "./attack_visualizations") -> None:
        """Generate visualizations of attack patterns and detection results"""
        if not self.results:
            logger.warning("No simulation results to visualize")
            return
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create summary bar chart
        plt.figure(figsize=(12, 8))
        
        scenario_names = list(self.results.keys())
        detection_rates = [result['detection_rate'] * 100 for result in self.results.values()]
        detection_times = []
        
        for result in self.results.values():
            if result['detection_time'] is not None:
                detection_times.append(result['detection_time'])
            else:
                detection_times.append(0)
        
        # Plot detection rates
        plt.subplot(2, 1, 1)
        plt.bar(scenario_names, detection_rates, color='blue', alpha=0.7)
        plt.ylabel('Detection Rate (%)')
        plt.title('Attack Detection Performance by Scenario')
        plt.xticks(rotation=45, ha='right')
        plt.ylim(0, 100)
        
        # Plot detection times
        plt.subplot(2, 1, 2)
        plt.bar(scenario_names, detection_times, color='orange', alpha=0.7)
        plt.ylabel('Detection Time (steps)')
        plt.title('Attack Detection Time by Scenario')
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/attack_detection_summary.png")
        plt.close()
        
        # Create individual attack pattern visualizations
        for scenario_name, result in self.results.items():
            # Recreate the attack data for visualization
            scenario = next((s for s in self.attack_scenarios if s['name'] == scenario_name), None)
            if not scenario:
                continue
                
            # Generate attack data again
            attack_data = self._generate_attack_data(scenario)
            
            # Extract prices and timestamps
            prices = [data.price for data in attack_data]
            timestamps = [data.timestamp for data in attack_data]
            
            # Normalize timestamps for x-axis
            timestamps = [(t - timestamps[0]) / 60 for t in timestamps]  # Minutes from start
            
            plt.figure(figsize=(10, 6))
            plt.plot(timestamps, prices, 'b-', label='Price')
            
            # Mark detection point if available
            if result['detection_time'] is not None:
                detection_idx = result['detection_time']
                if detection_idx < len(timestamps) and detection_idx < len(prices):
                    plt.axvline(x=timestamps[detection_idx], color='r', linestyle='--', 
                               label=f'Detection at step {detection_idx}')
                    plt.plot(timestamps[detection_idx], prices[detection_idx], 'ro')
            
            # Add baseline price
            plt.axhline(y=scenario['base_price'], color='g', linestyle=':', label='Baseline Price')
            
            plt.title(f"Attack Pattern: {scenario_name}")
            plt.xlabel('Time (minutes from start)')
            plt.ylabel('Price')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            plt.savefig(f"{output_dir}/{scenario_name.replace(' ', '_').lower()}.png")
            plt.close()
        
        logger.info(f"Attack visualizations saved to {output_dir}")

async def main():
    """Run the oracle attack simulator"""
    # Create simulator
    simulator = OracleAttackSimulator()
    
    # Run all attack simulations
    await simulator.run_all_attack_simulations()
    
    # Generate report and visualizations
    simulator.generate_report()
    simulator.visualize_results()

if __name__ == "__main__":
    asyncio.run(main())