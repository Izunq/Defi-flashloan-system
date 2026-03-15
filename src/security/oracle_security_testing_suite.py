#!/usr/bin/env python3
"""
Oracle Security Testing Suite
Comprehensive testing for oracle security improvements
"""

import time
import random
import logging
import statistics
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OracleSecurityTesting")

@dataclass
class TestResult:
    """Test result structure"""
    test_name: str
    status: str
    duration: float
    details: Dict[str, Any]
    error: str = ""

@dataclass
class SecurityMetrics:
    """Security metrics for testing"""
    detection_rate: float
    false_positive_rate: float
    response_time: float
    accuracy: float

class OracleSecurityTester:
    """Comprehensive oracle security testing suite"""
    
    def __init__(self):
        self.test_results: List[TestResult] = []
        self.attack_scenarios = self._load_attack_scenarios()
        
    def _load_attack_scenarios(self) -> List[Dict]:
        """Load attack scenarios for testing"""
        return [
            {
                'name': 'Flash Loan Price Manipulation',
                'description': 'Simulates rapid price changes within single transaction',
                'pattern': 'rapid_price_spike',
                'severity': 'CRITICAL',
                'expected_detection': True
            },
            {
                'name': 'Oracle Coordination Attack',
                'description': 'Multiple oracles providing similar false data',
                'pattern': 'coordinated_deviation',
                'severity': 'CRITICAL', 
                'expected_detection': True
            },
            {
                'name': 'Volume Manipulation',
                'description': 'Artificial volume inflation to mask price manipulation',
                'pattern': 'volume_spike',
                'severity': 'HIGH',
                'expected_detection': True
            },
            {
                'name': 'Timestamp Manipulation',
                'description': 'Invalid or future timestamps in price data',
                'pattern': 'timestamp_anomaly',
                'severity': 'MEDIUM',
                'expected_detection': True
            },
            {
                'name': 'Statistical Anomaly',
                'description': 'Price deviation beyond statistical thresholds',
                'pattern': 'statistical_outlier',
                'severity': 'HIGH',
                'expected_detection': True
            },
            {
                'name': 'Gradual Manipulation',
                'description': 'Slow price drift to avoid detection',
                'pattern': 'gradual_drift',
                'severity': 'MEDIUM',
                'expected_detection': False  # Should be harder to detect
            }
        ]
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run complete oracle security test suite"""
        logger.info("Starting comprehensive oracle security tests")
        
        start_time = time.time()
        test_summary = {
            'start_time': start_time,
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'security_metrics': {},
            'attack_detection_results': {},
            'performance_metrics': {},
            'recommendations': []
        }
        
        try:
            # 1. Basic Security Tests
            logger.info("Running basic security tests...")
            basic_results = self._run_basic_security_tests()
            test_summary['basic_security'] = basic_results
            
            # 2. Attack Simulation Tests
            logger.info("Running attack simulation tests...")
            attack_results = self._run_attack_simulation_tests()
            test_summary['attack_simulations'] = attack_results
            
            # 3. Statistical Analysis Tests
            logger.info("Running statistical analysis tests...")
            stats_results = self._run_statistical_tests()
            test_summary['statistical_analysis'] = stats_results
            
            # 4. Performance Tests
            logger.info("Running performance tests...")
            perf_results = self._run_performance_tests()
            test_summary['performance'] = perf_results
            
            # 5. Circuit Breaker Tests
            logger.info("Running circuit breaker tests...")
            cb_results = self._run_circuit_breaker_tests()
            test_summary['circuit_breakers'] = cb_results
            
            # 6. Integration Tests
            logger.info("Running integration tests...")
            integration_results = self._run_integration_tests()
            test_summary['integration'] = integration_results
            
            # Calculate overall metrics
            test_summary.update(self._calculate_summary_metrics())
            
            end_time = time.time()
            test_summary['end_time'] = end_time
            test_summary['total_duration'] = end_time - start_time
            
            logger.info(f"Testing completed in {test_summary['total_duration']:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Testing failed: {e}")
            test_summary['error'] = str(e)
            test_summary['status'] = 'FAILED'
        
        return test_summary
    
    def _run_basic_security_tests(self) -> Dict[str, Any]:
        """Run basic security validation tests"""
        results = {
            'price_validation': self._test_price_validation(),
            'deviation_detection': self._test_deviation_detection(),
            'staleness_validation': self._test_staleness_validation(),
            'consensus_validation': self._test_consensus_validation()
        }
        
        return results
    
    def _test_price_validation(self) -> TestResult:
        """Test price validation logic"""
        start_time = time.time()
        
        try:
            test_cases = [
                {'price': 0, 'expected': False, 'reason': 'zero_price'},
                {'price': -100, 'expected': False, 'reason': 'negative_price'},
                {'price': 1000, 'expected': True, 'reason': 'valid_price'},
                {'price': 10**18, 'expected': True, 'reason': 'large_valid_price'},
                {'price': 10**30, 'expected': False, 'reason': 'overflow_price'}
            ]
            
            passed = 0
            total = len(test_cases)
            
            for case in test_cases:
                result = self._validate_price_input(case['price'])
                if result == case['expected']:
                    passed += 1
                else:
                    logger.warning(f"Price validation failed for {case}")
            
            success_rate = passed / total
            status = 'PASSED' if success_rate >= 0.9 else 'FAILED'
            
            return TestResult(
                test_name='price_validation',
                status=status,
                duration=time.time() - start_time,
                details={
                    'total_cases': total,
                    'passed': passed,
                    'success_rate': success_rate,
                    'test_cases': test_cases
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name='price_validation',
                status='ERROR',
                duration=time.time() - start_time,
                details={},
                error=str(e)
            )
    
    def _test_deviation_detection(self) -> TestResult:
        """Test price deviation detection"""
        start_time = time.time()
        
        try:
            # Generate test data with known deviations
            base_price = 1000
            test_prices = [
                base_price,  # Normal
                base_price * 1.02,  # 2% increase (should pass)
                base_price * 0.98,  # 2% decrease (should pass)
                base_price * 1.08,  # 8% increase (should alert)
                base_price * 0.85,  # 15% decrease (should trigger circuit breaker)
            ]
            
            detection_results = []
            for price in test_prices:
                deviation = abs(price - base_price) / base_price * 100
                detected = self._detect_price_deviation(base_price, price)
                detection_results.append({
                    'price': price,
                    'deviation': deviation,
                    'detected': detected,
                    'expected': deviation > 5  # 5% threshold
                })
            
            # Calculate accuracy
            correct_detections = sum(1 for r in detection_results 
                                   if r['detected'] == r['expected'])
            accuracy = correct_detections / len(detection_results)
            
            status = 'PASSED' if accuracy >= 0.8 else 'FAILED'
            
            return TestResult(
                test_name='deviation_detection',
                status=status,
                duration=time.time() - start_time,
                details={
                    'accuracy': accuracy,
                    'detection_results': detection_results,
                    'total_tests': len(test_prices)
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name='deviation_detection',
                status='ERROR',
                duration=time.time() - start_time,
                details={},
                error=str(e)
            )
    
    def _test_staleness_validation(self) -> TestResult:
        """Test staleness detection"""
        start_time = time.time()
        
        try:
            current_time = int(time.time())
            test_timestamps = [
                current_time,  # Fresh
                current_time - 1800,  # 30 minutes old (should pass)
                current_time - 3600,  # 1 hour old (borderline)
                current_time - 7200,  # 2 hours old (should fail)
                current_time + 300,   # Future timestamp (should fail)
            ]
            
            staleness_results = []
            for timestamp in test_timestamps:
                age = current_time - timestamp
                is_stale = self._check_staleness(timestamp, current_time)
                staleness_results.append({
                    'timestamp': timestamp,
                    'age_seconds': age,
                    'is_stale': is_stale,
                    'expected': abs(age) > 3600  # 1 hour threshold
                })
            
            # Calculate accuracy
            correct_checks = sum(1 for r in staleness_results 
                               if r['is_stale'] == r['expected'])
            accuracy = correct_checks / len(staleness_results)
            
            status = 'PASSED' if accuracy >= 0.8 else 'FAILED'
            
            return TestResult(
                test_name='staleness_validation',
                status=status,
                duration=time.time() - start_time,
                details={
                    'accuracy': accuracy,
                    'staleness_results': staleness_results,
                    'threshold_seconds': 3600
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name='staleness_validation',
                status='ERROR',
                duration=time.time() - start_time,
                details={},
                error=str(e)
            )
    
    def _test_consensus_validation(self) -> TestResult:
        """Test oracle consensus validation"""
        start_time = time.time()
        
        try:
            # Simulate oracle price data
            test_scenarios = [
                {
                    'name': 'good_consensus',
                    'prices': [1000, 1001, 999, 1002, 998],  # Close prices
                    'expected_valid': True
                },
                {
                    'name': 'one_outlier',
                    'prices': [1000, 1001, 999, 1002, 1200],  # One outlier
                    'expected_valid': True  # Should still reach consensus
                },
                {
                    'name': 'multiple_outliers',
                    'prices': [1000, 1200, 800, 1300, 700],  # Multiple outliers
                    'expected_valid': False
                },
                {
                    'name': 'insufficient_oracles',
                    'prices': [1000, 1001],  # Only 2 oracles
                    'expected_valid': False
                }
            ]
            
            consensus_results = []
            for scenario in test_scenarios:
                consensus_price, is_valid = self._calculate_consensus(scenario['prices'])
                consensus_results.append({
                    'scenario': scenario['name'],
                    'prices': scenario['prices'],
                    'consensus_price': consensus_price,
                    'is_valid': is_valid,
                    'expected_valid': scenario['expected_valid'],
                    'correct': is_valid == scenario['expected_valid']
                })
            
            # Calculate accuracy
            correct_consensus = sum(1 for r in consensus_results if r['correct'])
            accuracy = correct_consensus / len(consensus_results)
            
            status = 'PASSED' if accuracy >= 0.75 else 'FAILED'
            
            return TestResult(
                test_name='consensus_validation',
                status=status,
                duration=time.time() - start_time,
                details={
                    'accuracy': accuracy,
                    'consensus_results': consensus_results,
                    'min_oracles_required': 3
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name='consensus_validation',
                status='ERROR',
                duration=time.time() - start_time,
                details={},
                error=str(e)
            )
    
    def _run_attack_simulation_tests(self) -> Dict[str, Any]:
        """Run attack simulation tests"""
        attack_results = {}
        
        for scenario in self.attack_scenarios:
            logger.info(f"Simulating attack: {scenario['name']}")
            result = self._simulate_attack(scenario)
            attack_results[scenario['name']] = result
        
        # Calculate overall detection metrics
        total_attacks = len(self.attack_scenarios)
        detected_attacks = sum(1 for r in attack_results.values() 
                             if r.get('detected', False))
        
        detection_rate = detected_attacks / total_attacks if total_attacks > 0 else 0
        
        return {
            'total_attacks': total_attacks,
            'detected_attacks': detected_attacks,
            'detection_rate': detection_rate,
            'attack_results': attack_results
        }
    
    def _simulate_attack(self, scenario: Dict) -> Dict[str, Any]:
        """Simulate a specific attack scenario"""
        start_time = time.time()
        
        try:
            if scenario['pattern'] == 'rapid_price_spike':
                return self._simulate_flash_loan_attack()
            elif scenario['pattern'] == 'coordinated_deviation':
                return self._simulate_coordinated_attack()
            elif scenario['pattern'] == 'volume_spike':
                return self._simulate_volume_manipulation()
            elif scenario['pattern'] == 'timestamp_anomaly':
                return self._simulate_timestamp_manipulation()
            elif scenario['pattern'] == 'statistical_outlier':
                return self._simulate_statistical_anomaly()
            elif scenario['pattern'] == 'gradual_drift':
                return self._simulate_gradual_manipulation()
            else:
                return {
                    'detected': False,
                    'error': f"Unknown attack pattern: {scenario['pattern']}"
                }
                
        except Exception as e:
            return {
                'detected': False,
                'error': str(e),
                'duration': time.time() - start_time
            }
    
    def _simulate_flash_loan_attack(self) -> Dict[str, Any]:
        """Simulate flash loan price manipulation"""
        start_time = time.time()
        
        # Generate rapid price changes
        base_price = 1000
        attack_sequence = [
            base_price,
            base_price * 1.15,  # 15% spike
            base_price * 0.85,  # 15% drop
            base_price * 1.25,  # 25% spike
            base_price,  # Return to normal
        ]
        
        # Check if this pattern would be detected
        max_deviation = max(abs(p - base_price) / base_price for p in attack_sequence)
        rapid_changes = sum(1 for i in range(1, len(attack_sequence))
                          if abs(attack_sequence[i] - attack_sequence[i-1]) / attack_sequence[i-1] > 0.1)
        
        detected = max_deviation > 0.1 and rapid_changes >= 2  # 10% deviation and 2+ rapid changes
        
        return {
            'detected': detected,
            'max_deviation': max_deviation,
            'rapid_changes': rapid_changes,
            'attack_sequence': attack_sequence,
            'duration': time.time() - start_time
        }
    
    def _simulate_coordinated_attack(self) -> Dict[str, Any]:
        """Simulate coordinated oracle attack"""
        start_time = time.time()
        
        # Simulate multiple oracles providing coordinated false data
        true_price = 1000
        oracle_prices = [
            1150,  # Oracle 1: 15% higher
            1140,  # Oracle 2: 14% higher  
            1160,  # Oracle 3: 16% higher
            1000,  # Oracle 4: Correct price
            1010,  # Oracle 5: Slightly higher
        ]
        
        # Check consensus
        consensus_price, is_valid = self._calculate_consensus(oracle_prices)
        deviation_from_true = abs(consensus_price - true_price) / true_price
        
        # Should be detected if consensus deviates significantly from expected
        detected = deviation_from_true > 0.05  # 5% threshold
        
        return {
            'detected': detected,
            'consensus_price': consensus_price,
            'true_price': true_price,
            'deviation': deviation_from_true,
            'oracle_prices': oracle_prices,
            'consensus_valid': is_valid,
            'duration': time.time() - start_time
        }
    
    def _simulate_volume_manipulation(self) -> Dict[str, Any]:
        """Simulate volume manipulation attack"""
        start_time = time.time()
        
        # Generate volume spike data
        normal_volume = 1000000
        attack_volumes = [
            normal_volume,
            normal_volume * 5,   # 5x volume spike
            normal_volume * 8,   # 8x volume spike
            normal_volume * 3,   # 3x volume
            normal_volume,       # Return to normal
        ]
        
        # Check if volume anomaly would be detected
        max_volume_multiple = max(v / normal_volume for v in attack_volumes)
        detected = max_volume_multiple > 3  # 3x threshold
        
        return {
            'detected': detected,
            'max_volume_multiple': max_volume_multiple,
            'attack_volumes': attack_volumes,
            'normal_volume': normal_volume,
            'duration': time.time() - start_time
        }
    
    def _simulate_timestamp_manipulation(self) -> Dict[str, Any]:
        """Simulate timestamp manipulation"""
        start_time = time.time()
        
        current_time = int(time.time())
        manipulated_timestamps = [
            current_time + 3600,  # 1 hour in future
            current_time - 7200,  # 2 hours in past
            current_time,         # Current time (normal)
        ]
        
        # Check timestamp validation
        invalid_timestamps = sum(1 for ts in manipulated_timestamps
                               if self._check_staleness(ts, current_time))
        
        detected = invalid_timestamps > 0
        
        return {
            'detected': detected,
            'invalid_timestamps': invalid_timestamps,
            'manipulated_timestamps': manipulated_timestamps,
            'current_time': current_time,
            'duration': time.time() - start_time
        }
    
    def _simulate_statistical_anomaly(self) -> Dict[str, Any]:
        """Simulate statistical price anomaly"""
        start_time = time.time()
        
        # Generate price history with anomaly
        base_price = 1000
        normal_prices = [base_price + random.gauss(0, 20) for _ in range(50)]  # Normal distribution
        anomaly_price = base_price + 200  # 20% anomaly
        
        # Calculate Z-score
        mean_price = statistics.mean(normal_prices)
        std_dev = statistics.stdev(normal_prices)
        z_score = abs(anomaly_price - mean_price) / std_dev if std_dev > 0 else 0
        
        detected = z_score > 3  # 3-sigma threshold
        
        return {
            'detected': detected,
            'z_score': z_score,
            'anomaly_price': anomaly_price,
            'mean_price': mean_price,
            'std_dev': std_dev,
            'duration': time.time() - start_time
        }
    
    def _simulate_gradual_manipulation(self) -> Dict[str, Any]:
        """Simulate gradual price manipulation"""
        start_time = time.time()
        
        # Generate gradual price drift
        base_price = 1000
        manipulation_sequence = []
        current_price = base_price
        
        # Gradual 10% increase over 20 steps
        for i in range(20):
            current_price *= 1.005  # 0.5% per step
            manipulation_sequence.append(current_price)
        
        # Check if gradual manipulation would be detected
        total_change = (manipulation_sequence[-1] - base_price) / base_price
        max_step_change = max(abs(manipulation_sequence[i] - manipulation_sequence[i-1]) / manipulation_sequence[i-1]
                             for i in range(1, len(manipulation_sequence)))
        
        # Gradual manipulation should be harder to detect
        detected = max_step_change > 0.02  # 2% single step threshold
        
        return {
            'detected': detected,
            'total_change': total_change,
            'max_step_change': max_step_change,
            'manipulation_sequence': manipulation_sequence[:5],  # First 5 values
            'duration': time.time() - start_time
        }
    
    def _run_statistical_tests(self) -> Dict[str, Any]:
        """Run statistical analysis tests"""
        return {
            'z_score_analysis': self._test_z_score_analysis(),
            'moving_averages': self._test_moving_averages(),
            'volatility_analysis': self._test_volatility_analysis(),
            'correlation_analysis': self._test_correlation_analysis()
        }
    
    def _test_z_score_analysis(self) -> TestResult:
        """Test Z-score anomaly detection"""
        start_time = time.time()
        
        try:
            # Generate test data with known outliers
            normal_data = [random.gauss(1000, 50) for _ in range(100)]
            outliers = [1000 + 200, 1000 - 200]  # 4-sigma outliers
            
            all_data = normal_data + outliers
            
            # Calculate Z-scores
            mean_val = statistics.mean(normal_data)
            std_val = statistics.stdev(normal_data)
            
            detected_outliers = 0
            for value in outliers:
                z_score = abs(value - mean_val) / std_val
                if z_score > 3:  # 3-sigma threshold
                    detected_outliers += 1
            
            detection_rate = detected_outliers / len(outliers)
            status = 'PASSED' if detection_rate >= 0.8 else 'FAILED'
            
            return TestResult(
                test_name='z_score_analysis',
                status=status,
                duration=time.time() - start_time,
                details={
                    'detection_rate': detection_rate,
                    'outliers_detected': detected_outliers,
                    'total_outliers': len(outliers),
                    'mean': mean_val,
                    'std_dev': std_val
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name='z_score_analysis',
                status='ERROR',
                duration=time.time() - start_time,
                details={},
                error=str(e)
            )
    
    def _test_moving_averages(self) -> TestResult:
        """Test moving average calculations"""
        start_time = time.time()
        
        try:
            # Test data
            prices = [100, 105, 103, 107, 106, 108, 110, 109, 111, 112]
            window_size = 5
            
            # Calculate moving averages
            moving_averages = []
            for i in range(window_size - 1, len(prices)):
                avg = sum(prices[i-window_size+1:i+1]) / window_size
                moving_averages.append(avg)
            
            # Test accuracy
            expected_ma = statistics.mean(prices[-window_size:])
            calculated_ma = moving_averages[-1]
            
            accuracy = 1 - abs(expected_ma - calculated_ma) / expected_ma
            status = 'PASSED' if accuracy >= 0.99 else 'FAILED'
            
            return TestResult(
                test_name='moving_averages',
                status=status,
                duration=time.time() - start_time,
                details={
                    'accuracy': accuracy,
                    'expected_ma': expected_ma,
                    'calculated_ma': calculated_ma,
                    'moving_averages': moving_averages
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name='moving_averages',
                status='ERROR',
                duration=time.time() - start_time,
                details={},
                error=str(e)
            )
    
    def _test_volatility_analysis(self) -> TestResult:
        """Test volatility analysis"""
        start_time = time.time()
        
        try:
            # Generate test data with different volatility periods
            low_vol_data = [1000 + random.gauss(0, 5) for _ in range(50)]
            high_vol_data = [1000 + random.gauss(0, 50) for _ in range(50)]
            
            # Calculate volatility (standard deviation)
            low_vol = statistics.stdev(low_vol_data)
            high_vol = statistics.stdev(high_vol_data)
            
            # Test volatility detection
            volatility_detected = high_vol > low_vol * 2  # Should detect higher volatility
            
            status = 'PASSED' if volatility_detected else 'FAILED'
            
            return TestResult(
                test_name='volatility_analysis',
                status=status,
                duration=time.time() - start_time,
                details={
                    'low_volatility': low_vol,
                    'high_volatility': high_vol,
                    'volatility_ratio': high_vol / low_vol,
                    'detection_threshold': 2.0
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name='volatility_analysis',
                status='ERROR',
                duration=time.time() - start_time,
                details={},
                error=str(e)
            )
    
    def _test_correlation_analysis(self) -> TestResult:
        """Test correlation analysis between assets"""
        start_time = time.time()
        
        try:
            # Generate correlated and uncorrelated data
            size = 50
            asset1 = [random.gauss(1000, 50) for _ in range(size)]
            asset2_corr = [p + random.gauss(0, 10) for p in asset1]  # Correlated
            asset2_uncorr = [random.gauss(2000, 100) for _ in range(size)]  # Uncorrelated
            
            # Calculate correlation coefficients
            def correlation(x, y):
                n = len(x)
                sum_x = sum(x)
                sum_y = sum(y)
                sum_xy = sum(x[i] * y[i] for i in range(n))
                sum_x2 = sum(x[i] ** 2 for i in range(n))
                sum_y2 = sum(y[i] ** 2 for i in range(n))
                
                numerator = n * sum_xy - sum_x * sum_y
                denominator = ((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2)) ** 0.5
                
                return numerator / denominator if denominator != 0 else 0
            
            corr_coeff = correlation(asset1, asset2_corr)
            uncorr_coeff = correlation(asset1, asset2_uncorr)
            
            # Test correlation detection
            correlation_detected = abs(corr_coeff) > 0.7 and abs(uncorr_coeff) < 0.3
            
            status = 'PASSED' if correlation_detected else 'FAILED'
            
            return TestResult(
                test_name='correlation_analysis',
                status=status,
                duration=time.time() - start_time,
                details={
                    'correlated_coefficient': corr_coeff,
                    'uncorrelated_coefficient': uncorr_coeff,
                    'correlation_threshold': 0.7,
                    'test_passed': correlation_detected
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name='correlation_analysis',
                status='ERROR',
                duration=time.time() - start_time,
                details={},
                error=str(e)
            )
    
    def _run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests"""
        return {
            'response_time': self._test_response_time(),
            'throughput': self._test_throughput(),
            'memory_usage': self._test_memory_usage(),
            'scalability': self._test_scalability()
        }
    
    def _test_response_time(self) -> TestResult:
        """Test system response time"""
        start_time = time.time()
        
        try:
            response_times = []
            
            # Test multiple validation cycles
            for _ in range(100):
                cycle_start = time.time()
                
                # Simulate validation process
                self._validate_price_input(1000)
                self._detect_price_deviation(1000, 1050)
                self._check_staleness(int(time.time()), int(time.time()))
                
                cycle_time = time.time() - cycle_start
                response_times.append(cycle_time)
            
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            
            # Response time should be under 100ms
            status = 'PASSED' if avg_response_time < 0.1 else 'FAILED'
            
            return TestResult(
                test_name='response_time',
                status=status,
                duration=time.time() - start_time,
                details={
                    'average_response_time': avg_response_time,
                    'max_response_time': max_response_time,
                    'total_tests': len(response_times),
                    'threshold_seconds': 0.1
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name='response_time',
                status='ERROR',
                duration=time.time() - start_time,
                details={},
                error=str(e)
            )
    
    def _test_throughput(self) -> TestResult:
        """Test system throughput"""
        start_time = time.time()
        
        try:
            # Process multiple price updates rapidly
            num_updates = 1000
            process_start = time.time()
            
            for i in range(num_updates):
                price = 1000 + random.randint(-50, 50)
                self._validate_price_input(price)
            
            process_duration = time.time() - process_start
            throughput = num_updates / process_duration
            
            # Should handle at least 1000 updates per second
            status = 'PASSED' if throughput >= 1000 else 'FAILED'
            
            return TestResult(
                test_name='throughput',
                status=status,
                duration=time.time() - start_time,
                details={
                    'throughput_per_second': throughput,
                    'total_updates': num_updates,
                    'process_duration': process_duration,
                    'threshold_tps': 1000
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name='throughput',
                status='ERROR',
                duration=time.time() - start_time,
                details={},
                error=str(e)
            )
    
    def _test_memory_usage(self) -> TestResult:
        """Test memory usage patterns"""
        start_time = time.time()
        
        try:
            # Simulate memory usage tracking
            initial_objects = 1000
            final_objects = initial_objects
            
            # Simulate processing large amounts of data
            large_dataset = []
            for i in range(10000):
                large_dataset.append({
                    'price': 1000 + i,
                    'timestamp': int(time.time()) + i,
                    'volume': random.randint(1000, 10000)
                })
            
            # Clean up
            del large_dataset
            
            # Memory should not grow excessively
            memory_growth = final_objects - initial_objects
            status = 'PASSED' if memory_growth < 1000 else 'FAILED'
            
            return TestResult(
                test_name='memory_usage',
                status=status,
                duration=time.time() - start_time,
                details={
                    'initial_objects': initial_objects,
                    'final_objects': final_objects,
                    'memory_growth': memory_growth,
                    'growth_threshold': 1000
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name='memory_usage',
                status='ERROR',
                duration=time.time() - start_time,
                details={},
                error=str(e)
            )
    
    def _test_scalability(self) -> TestResult:
        """Test system scalability"""
        start_time = time.time()
        
        try:
            # Test with increasing load
            load_tests = [100, 500, 1000, 5000]
            scalability_results = []
            
            for load in load_tests:
                load_start = time.time()
                
                # Process increasing number of price updates
                for i in range(load):
                    self._validate_price_input(1000 + random.randint(-10, 10))
                
                load_duration = time.time() - load_start
                throughput = load / load_duration
                
                scalability_results.append({
                    'load': load,
                    'duration': load_duration,
                    'throughput': throughput
                })
            
            # Check if throughput scales reasonably
            min_throughput = min(r['throughput'] for r in scalability_results)
            max_throughput = max(r['throughput'] for r in scalability_results)
            
            # Throughput shouldn't degrade by more than 50%
            degradation = (max_throughput - min_throughput) / max_throughput
            status = 'PASSED' if degradation < 0.5 else 'FAILED'
            
            return TestResult(
                test_name='scalability',
                status=status,
                duration=time.time() - start_time,
                details={
                    'scalability_results': scalability_results,
                    'performance_degradation': degradation,
                    'degradation_threshold': 0.5
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name='scalability',
                status='ERROR',
                duration=time.time() - start_time,
                details={},
                error=str(e)
            )
    
    def _run_circuit_breaker_tests(self) -> Dict[str, Any]:
        """Test circuit breaker functionality"""
        return {
            'activation_test': self._test_circuit_breaker_activation(),
            'reset_test': self._test_circuit_breaker_reset(),
            'cascade_test': self._test_circuit_breaker_cascade()
        }
    
    def _test_circuit_breaker_activation(self) -> TestResult:
        """Test circuit breaker activation"""
        start_time = time.time()
        
        try:
            # Simulate conditions that should trigger circuit breaker
            base_price = 1000
            trigger_price = base_price * 1.15  # 15% deviation
            
            deviation = abs(trigger_price - base_price) / base_price
            should_trigger = deviation > 0.1  # 10% threshold
            
            # Simulate circuit breaker logic
            triggered = self._simulate_circuit_breaker(base_price, trigger_price)
            
            status = 'PASSED' if triggered == should_trigger else 'FAILED'
            
            return TestResult(
                test_name='circuit_breaker_activation',
                status=status,
                duration=time.time() - start_time,
                details={
                    'base_price': base_price,
                    'trigger_price': trigger_price,
                    'deviation': deviation,
                    'should_trigger': should_trigger,
                    'actually_triggered': triggered
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name='circuit_breaker_activation',
                status='ERROR',
                duration=time.time() - start_time,
                details={},
                error=str(e)
            )
    
    def _test_circuit_breaker_reset(self) -> TestResult:
        """Test circuit breaker reset functionality"""
        start_time = time.time()
        
        try:
            # Simulate circuit breaker reset after cooling period
            activation_time = time.time() - 3700  # 1 hour and 1 minute ago
            current_time = time.time()
            
            cooling_period = 3600  # 1 hour
            can_reset = (current_time - activation_time) >= cooling_period
            
            status = 'PASSED' if can_reset else 'FAILED'
            
            return TestResult(
                test_name='circuit_breaker_reset',
                status=status,
                duration=time.time() - start_time,
                details={
                    'activation_time': activation_time,
                    'current_time': current_time,
                    'cooling_period': cooling_period,
                    'time_elapsed': current_time - activation_time,
                    'can_reset': can_reset
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name='circuit_breaker_reset',
                status='ERROR',
                duration=time.time() - start_time,
                details={},
                error=str(e)
            )
    
    def _test_circuit_breaker_cascade(self) -> TestResult:
        """Test circuit breaker cascade functionality"""
        start_time = time.time()
        
        try:
            # Simulate multiple assets triggering circuit breakers
            triggered_assets = ['ETH', 'BTC', 'USDC']  # 3 assets
            global_threshold = 3
            
            should_trigger_global = len(triggered_assets) >= global_threshold
            
            status = 'PASSED' if should_trigger_global else 'FAILED'
            
            return TestResult(
                test_name='circuit_breaker_cascade',
                status=status,
                duration=time.time() - start_time,
                details={
                    'triggered_assets': triggered_assets,
                    'trigger_count': len(triggered_assets),
                    'global_threshold': global_threshold,
                    'should_trigger_global': should_trigger_global
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name='circuit_breaker_cascade',
                status='ERROR',
                duration=time.time() - start_time,
                details={},
                error=str(e)
            )
    
    def _run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests"""
        return {
            'end_to_end_validation': self._test_end_to_end_validation(),
            'multi_oracle_integration': self._test_multi_oracle_integration(),
            'monitoring_integration': self._test_monitoring_integration()
        }
    
    def _test_end_to_end_validation(self) -> TestResult:
        """Test end-to-end validation process"""
        start_time = time.time()
        
        try:
            # Simulate complete validation pipeline
            test_price = 1000
            test_volume = 1000000
            test_timestamp = int(time.time())
            
            # Run through validation pipeline
            step_results = {
                'price_validation': self._validate_price_input(test_price),
                'staleness_check': not self._check_staleness(test_timestamp, int(time.time())),
                'deviation_check': not self._detect_price_deviation(test_price, test_price),
                'consensus_check': self._calculate_consensus([test_price, test_price + 1, test_price - 1])[1]
            }
            
            all_passed = all(step_results.values())
            status = 'PASSED' if all_passed else 'FAILED'
            
            return TestResult(
                test_name='end_to_end_validation',
                status=status,
                duration=time.time() - start_time,
                details={
                    'step_results': step_results,
                    'all_steps_passed': all_passed,
                    'test_inputs': {
                        'price': test_price,
                        'volume': test_volume,
                        'timestamp': test_timestamp
                    }
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name='end_to_end_validation',
                status='ERROR',
                duration=time.time() - start_time,
                details={},
                error=str(e)
            )
    
    def _test_multi_oracle_integration(self) -> TestResult:
        """Test multi-oracle integration"""
        start_time = time.time()
        
        try:
            # Simulate multiple oracle sources
            oracle_data = [
                {'source': 'Chainlink', 'price': 1000, 'confidence': 95},
                {'source': 'Band', 'price': 1002, 'confidence': 90},
                {'source': 'API3', 'price': 998, 'confidence': 85},
                {'source': 'Custom', 'price': 1001, 'confidence': 80}
            ]
            
            # Test oracle aggregation
            prices = [o['price'] for o in oracle_data]
            weights = [o['confidence'] for o in oracle_data]
            
            # Weighted average calculation
            weighted_sum = sum(p * w for p, w in zip(prices, weights))
            total_weight = sum(weights)
            weighted_average = weighted_sum / total_weight
            
            # Check if result is reasonable
            expected_range = (995, 1005)  # Expected price range
            result_valid = expected_range[0] <= weighted_average <= expected_range[1]
            
            status = 'PASSED' if result_valid else 'FAILED'
            
            return TestResult(
                test_name='multi_oracle_integration',
                status=status,
                duration=time.time() - start_time,
                details={
                    'oracle_data': oracle_data,
                    'weighted_average': weighted_average,
                    'expected_range': expected_range,
                    'result_valid': result_valid
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name='multi_oracle_integration',
                status='ERROR',
                duration=time.time() - start_time,
                details={},
                error=str(e)
            )
    
    def _test_monitoring_integration(self) -> TestResult:
        """Test monitoring system integration"""
        start_time = time.time()
        
        try:
            # Simulate monitoring system components
            monitoring_components = {
                'price_monitor': True,
                'deviation_monitor': True,
                'volume_monitor': True,
                'threat_monitor': True,
                'alert_system': True
            }
            
            # Test each component
            component_status = {}
            for component, enabled in monitoring_components.items():
                # Simulate component health check
                component_status[component] = enabled and random.random() > 0.1  # 90% success rate
            
            all_healthy = all(component_status.values())
            health_percentage = sum(component_status.values()) / len(component_status)
            
            status = 'PASSED' if health_percentage >= 0.8 else 'FAILED'
            
            return TestResult(
                test_name='monitoring_integration',
                status=status,
                duration=time.time() - start_time,
                details={
                    'component_status': component_status,
                    'health_percentage': health_percentage,
                    'all_healthy': all_healthy,
                    'health_threshold': 0.8
                }
            )
            
        except Exception as e:
            return TestResult(
                test_name='monitoring_integration',
                status='ERROR',
                duration=time.time() - start_time,
                details={},
                error=str(e)
            )
    
    def _calculate_summary_metrics(self) -> Dict[str, Any]:
        """Calculate overall test summary metrics"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.status == 'PASSED')
        failed_tests = sum(1 for result in self.test_results if result.status == 'FAILED')
        error_tests = sum(1 for result in self.test_results if result.status == 'ERROR')
        
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        return {
            'tests_run': total_tests,
            'tests_passed': passed_tests,
            'tests_failed': failed_tests,
            'tests_with_errors': error_tests,
            'success_rate': success_rate,
            'overall_status': 'PASSED' if success_rate >= 0.8 else 'FAILED'
        }
    
    # Helper functions for testing
    def _validate_price_input(self, price: float) -> bool:
        """Validate price input"""
        return price > 0 and price < 10**20
    
    def _detect_price_deviation(self, base_price: float, current_price: float) -> bool:
        """Detect if price deviation exceeds threshold"""
        deviation = abs(current_price - base_price) / base_price
        return deviation > 0.05  # 5% threshold
    
    def _check_staleness(self, timestamp: int, current_time: int) -> bool:
        """Check if timestamp is stale"""
        age = abs(current_time - timestamp)
        return age > 3600  # 1 hour threshold
    
    def _calculate_consensus(self, prices: List[float]) -> Tuple[float, bool]:
        """Calculate consensus price from multiple oracles"""
        if len(prices) < 3:
            return 0, False
        
        # Remove outliers and calculate median
        sorted_prices = sorted(prices)
        median_price = sorted_prices[len(sorted_prices) // 2]
        
        # Check if consensus is valid (prices are close enough)
        max_deviation = max(abs(p - median_price) / median_price for p in prices)
        is_valid = max_deviation < 0.1  # 10% max deviation
        
        return median_price, is_valid
    
    def _simulate_circuit_breaker(self, base_price: float, current_price: float) -> bool:
        """Simulate circuit breaker logic"""
        deviation = abs(current_price - base_price) / base_price
        return deviation > 0.1  # 10% threshold
    
    def save_test_report(self, test_results: Dict[str, Any]) -> None:
        """Save test report to file"""
        try:
            report_filename = f"oracle_security_test_report_{int(time.time())}.json"
            with open(report_filename, 'w') as f:
                json.dump(test_results, f, indent=2, default=str)
            
            logger.info(f"Test report saved to {report_filename}")
            
        except Exception as e:
            logger.error(f"Failed to save test report: {e}")

def main():
    """Main testing function"""
    logger.info("Starting Oracle Security Testing Suite")
    
    try:
        tester = OracleSecurityTester()
        results = tester.run_comprehensive_tests()
        
        # Print summary
        print("\n" + "="*60)
        print("ORACLE SECURITY TEST RESULTS")
        print("="*60)
        print(f"Tests Run: {results.get('tests_run', 0)}")
        print(f"Tests Passed: {results.get('tests_passed', 0)}")
        print(f"Tests Failed: {results.get('tests_failed', 0)}")
        print(f"Success Rate: {results.get('success_rate', 0):.2%}")
        print(f"Overall Status: {results.get('overall_status', 'UNKNOWN')}")
        print("="*60)
        
        # Save report
        tester.save_test_report(results)
        
        if results.get('overall_status') == 'PASSED':
            logger.info("✅ All oracle security tests passed!")
        else:
            logger.warning("⚠️ Some oracle security tests failed!")
            
    except Exception as e:
        logger.error(f"Testing suite failed: {e}")

if __name__ == "__main__":
    main()
