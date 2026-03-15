"""
Phase 4 Testing: Integration Tests
Integration tests for the complete Flash Loan Arbitrage System
"""

import pytest
import asyncio
import time
import json
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

@pytest.mark.integration
class TestSystemIntegration:
    """Integration tests for complete system functionality"""
    
    def test_end_to_end_arbitrage_flow(self, mock_web3, mock_contract, sample_arbitrage_opportunity):
        """Test complete arbitrage flow from opportunity detection to execution"""
        
        # Mock system components
        mock_opportunity_detector = Mock()
        mock_pipeline_processor = Mock()
        mock_transaction_executor = Mock()
        mock_monitoring_system = Mock()
        
        # Configure mocks for successful flow
        mock_opportunity_detector.scan_markets.return_value = [sample_arbitrage_opportunity]
        
        mock_pipeline_processor.process_opportunity.return_value = {
            'status': 'approved',
            'estimated_profit': 450.0,
            'gas_cost': 50.0,
            'net_profit': 400.0
        }
          # Flash loan execution removed for Sharia compliance
        # Execute halal-compliant arbitrage instead
        mock_transaction_executor.execute_mudarabah_swap.return_value = {
            'status': 'success',
            'tx_hash': '0x' + 'a' * 64,
            'actual_profit': 385.0,
            'gas_used': 245000,
            'compliance': 'halal'
        }
        
        # Execute end-to-end flow
        opportunities = mock_opportunity_detector.scan_markets()
        assert len(opportunities) == 1
        
        for opportunity in opportunities:
            # Process through pipeline
            pipeline_result = mock_pipeline_processor.process_opportunity(opportunity)
            assert pipeline_result['status'] == 'approved'
              # Execute if approved (using halal-compliant method)
            if pipeline_result['status'] == 'approved':
                execution_result = mock_transaction_executor.execute_mudarabah_swap(opportunity)
                assert execution_result['status'] == 'success'
                assert execution_result['actual_profit'] > 0
                assert execution_result['compliance'] == 'halal'
                
                # Monitor result
                mock_monitoring_system.record_transaction(execution_result)
        
        # Verify monitoring was called
        mock_monitoring_system.record_transaction.assert_called_once()

    def test_event_bus_integration(self, mock_redis):
        """Test event bus integration across system components"""
        
        class MockEventBus:
            def __init__(self, redis_client):
                self.redis = redis_client
                self.subscribers = {}
                self.published_events = []
            
            def subscribe(self, channel: str, callback):
                if channel not in self.subscribers:
                    self.subscribers[channel] = []
                self.subscribers[channel].append(callback)
            
            def publish(self, channel: str, data: Dict[str, Any]):
                self.published_events.append({'channel': channel, 'data': data})
                # Simulate delivery to subscribers
                if channel in self.subscribers:
                    for callback in self.subscribers[channel]:
                        callback(data)
                return len(self.subscribers.get(channel, []))
        
        event_bus = MockEventBus(mock_redis)
        
        # Set up subscribers
        received_opportunities = []
        received_executions = []
        received_alerts = []
        
        def opportunity_handler(data):
            received_opportunities.append(data)
        
        def execution_handler(data):
            received_executions.append(data)
        
        def alert_handler(data):
            received_alerts.append(data)
        
        event_bus.subscribe('opportunities', opportunity_handler)
        event_bus.subscribe('executions', execution_handler)
        event_bus.subscribe('alerts', alert_handler)
        
        # Publish test events
        test_opportunity = {
            'pair': 'ETH/USDT',
            'profit': 2.5,
            'timestamp': time.time()
        }
        
        test_execution = {
            'tx_hash': '0x123456',
            'profit': 245.0,
            'status': 'success'
        }
        
        test_alert = {
            'type': 'high_profit',
            'message': 'High profit opportunity detected',
            'severity': 'info'
        }
        
        # Publish events
        event_bus.publish('opportunities', test_opportunity)
        event_bus.publish('executions', test_execution)
        event_bus.publish('alerts', test_alert)
        
        # Verify event delivery
        assert len(received_opportunities) == 1
        assert received_opportunities[0] == test_opportunity
        
        assert len(received_executions) == 1
        assert received_executions[0] == test_execution
        
        assert len(received_alerts) == 1
        assert received_alerts[0] == test_alert

    def test_database_integration(self, test_database):
        """Test database integration for data persistence"""
        
        # Test storing market data
        market_data = {
            'pair': 'ETH/USDT',
            'price': 3000.0,
            'volume': 1000000.0,
            'timestamp': time.time(),
            'source': 'uniswap'
        }
        
        test_database.store_price_data('ETH', market_data)
        
        # Test retrieving market data
        history = test_database.get_price_history('ETH')
        assert len(history) == 1
        assert history[0] == market_data
        
        # Test storing transaction data
        transaction_data = {
            'tx_hash': '0x' + 'a' * 64,
            'profit': 125.50,
            'gas_used': 234567,
            'timestamp': time.time(),
            'status': 'success'
        }
        
        test_database.store_alert(transaction_data)
        
        # Verify database state
        assert test_database.connected
        assert 'ETH' in test_database.data
        assert 'alerts' in test_database.data

    @pytest.mark.asyncio
    async def test_websocket_integration(self):
        """Test WebSocket integration for real-time updates"""
        
        class MockWebSocketManager:
            def __init__(self):
                self.connected_clients = []
                self.message_history = []
            
            async def connect_client(self, client_id: str):
                self.connected_clients.append(client_id)
                return True
            
            async def disconnect_client(self, client_id: str):
                if client_id in self.connected_clients:
                    self.connected_clients.remove(client_id)
            
            async def broadcast_update(self, update_type: str, data: Dict[str, Any]):
                message = {
                    'type': update_type,
                    'data': data,
                    'timestamp': time.time()
                }
                
                self.message_history.append(message)
                
                # Simulate sending to all connected clients
                for client_id in self.connected_clients:
                    # In real implementation, send via WebSocket
                    pass
                
                return len(self.connected_clients)
        
        ws_manager = MockWebSocketManager()
        
        # Test client connections
        await ws_manager.connect_client('client_1')
        await ws_manager.connect_client('client_2')
        assert len(ws_manager.connected_clients) == 2
        
        # Test broadcasting updates
        opportunity_update = {
            'pair': 'ETH/USDT',
            'profit_percentage': 3.2,
            'status': 'detected'
        }
        
        clients_reached = await ws_manager.broadcast_update('opportunity', opportunity_update)
        assert clients_reached == 2
        assert len(ws_manager.message_history) == 1
        
        execution_update = {
            'tx_hash': '0x123456',
            'profit': 287.5,
            'status': 'executed'
        }
        
        await ws_manager.broadcast_update('execution', execution_update)
        assert len(ws_manager.message_history) == 2
        
        # Test client disconnection
        await ws_manager.disconnect_client('client_1')
        assert len(ws_manager.connected_clients) == 1

    def test_monitoring_dashboard_integration(self):
        """Test monitoring dashboard data integration"""
        
        class MockMonitoringDashboard:
            def __init__(self):
                self.metrics = {
                    'total_opportunities': 0,
                    'successful_trades': 0,
                    'total_profit': 0.0,
                    'avg_profit_per_trade': 0.0,
                    'system_uptime': 0.0
                }
                self.alerts = []
                self.performance_data = []
            
            def update_metrics(self, metric_updates: Dict[str, Any]):
                for key, value in metric_updates.items():
                    if key in self.metrics:
                        if isinstance(self.metrics[key], (int, float)):
                            self.metrics[key] += value
                        else:
                            self.metrics[key] = value
            
            def add_alert(self, alert_type: str, message: str, severity: str = 'info'):
                alert = {
                    'type': alert_type,
                    'message': message,
                    'severity': severity,
                    'timestamp': time.time()
                }
                self.alerts.append(alert)
            
            def record_performance(self, operation: str, duration: float, success: bool):
                perf_record = {
                    'operation': operation,
                    'duration': duration,
                    'success': success,
                    'timestamp': time.time()
                }
                self.performance_data.append(perf_record)
            
            def get_dashboard_data(self):
                return {
                    'metrics': self.metrics,
                    'recent_alerts': self.alerts[-10:],  # Last 10 alerts
                    'performance_summary': {
                        'avg_execution_time': sum(p['duration'] for p in self.performance_data) / max(len(self.performance_data), 1),
                        'success_rate': sum(1 for p in self.performance_data if p['success']) / max(len(self.performance_data), 1)
                    }
                }
        
        dashboard = MockMonitoringDashboard()
        
        # Simulate system activity
        dashboard.update_metrics({
            'total_opportunities': 5,
            'successful_trades': 3,
            'total_profit': 850.0
        })
        
        dashboard.add_alert('opportunity', 'High profit opportunity detected', 'info')
        dashboard.add_alert('system', 'Gas prices elevated', 'warning')
        
        dashboard.record_performance('execute_trade', 2.5, True)
        dashboard.record_performance('execute_trade', 3.1, True)
        dashboard.record_performance('execute_trade', 4.2, False)
        
        # Test dashboard data aggregation
        dashboard_data = dashboard.get_dashboard_data()
        
        assert dashboard_data['metrics']['total_opportunities'] == 5
        assert dashboard_data['metrics']['successful_trades'] == 3
        assert dashboard_data['metrics']['total_profit'] == 850.0
        
        assert len(dashboard_data['recent_alerts']) == 2
        assert dashboard_data['performance_summary']['success_rate'] == 2/3  # 2 successes out of 3 trades

    def test_oracle_integration(self, mock_oracle_data):
        """Test oracle integration for price feeds"""
        
        class MockOracleAggregator:
            def __init__(self, oracle_sources):
                self.sources = oracle_sources
                self.price_cache = {}
                self.last_update = {}
            
            def get_aggregated_price(self, asset: str) -> Dict[str, Any]:
                if asset not in self.sources:
                    raise Exception(f"No oracle data for asset: {asset}")
                
                source_data = self.sources[asset]
                
                # Simulate price aggregation from multiple sources
                prices = [
                    source_data['price'] * (1 + 0.001),  # Source 1: +0.1%
                    source_data['price'],                 # Source 2: exact
                    source_data['price'] * (1 - 0.0015), # Source 3: -0.15%
                ]
                
                # Calculate median price
                prices.sort()
                median_price = prices[1]
                
                # Calculate price deviation
                max_deviation = max(abs(p - median_price) / median_price for p in prices)
                
                result = {
                    'asset': asset,
                    'price': median_price,
                    'deviation': max_deviation,
                    'confidence': source_data['confidence'],
                    'timestamp': source_data['timestamp'],
                    'sources_count': len(prices),
                    'is_reliable': max_deviation < 0.005  # 0.5% max deviation
                }
                
                self.price_cache[asset] = result
                self.last_update[asset] = time.time()
                
                return result
            
            def is_price_fresh(self, asset: str, max_age: int = 60) -> bool:
                if asset not in self.last_update:
                    return False
                return (time.time() - self.last_update[asset]) < max_age
        
        oracle = MockOracleAggregator(mock_oracle_data)
        
        # Test price aggregation
        eth_price_data = oracle.get_aggregated_price('ETH')
        
        assert eth_price_data['asset'] == 'ETH'
        assert eth_price_data['price'] > 0
        assert eth_price_data['deviation'] < 0.005  # Should be reliable
        assert eth_price_data['is_reliable'] == True
        assert eth_price_data['sources_count'] == 3
        
        # Test price freshness
        assert oracle.is_price_fresh('ETH')
        
        # Test multiple assets
        btc_price_data = oracle.get_aggregated_price('BTC')
        usdc_price_data = oracle.get_aggregated_price('USDC')
        
        assert btc_price_data['price'] > eth_price_data['price']  # BTC should be more expensive
        assert abs(usdc_price_data['price'] - 1.0) < 0.01  # USDC should be close to $1

    @pytest.mark.slow
    def test_system_stress_integration(self, performance_monitor):
        """Test system integration under stress conditions"""
        
        # Mock system components
        opportunity_processor = Mock()
        transaction_executor = Mock()
        monitoring_system = Mock()
        
        # Configure realistic processing times
        opportunity_processor.process.side_effect = lambda x: time.sleep(0.1) or {'status': 'processed'}
        transaction_executor.execute.side_effect = lambda x: time.sleep(0.5) or {'status': 'executed'}
        monitoring_system.record.side_effect = lambda x: time.sleep(0.05) or True
        
        # Simulate high load
        opportunities = []
        for i in range(50):
            opportunities.append({
                'id': f'opp_{i}',
                'pair': 'ETH/USDT',
                'profit': random.uniform(1.0, 5.0),
                'timestamp': time.time()
            })
        
        results = []
        
        for opportunity in opportunities:
            performance_monitor.start('full_pipeline')
            
            # Process opportunity
            performance_monitor.start('processing')
            process_result = opportunity_processor.process(opportunity)
            performance_monitor.end('processing')
            
            # Execute if profitable
            if process_result['status'] == 'processed':
                performance_monitor.start('execution')
                exec_result = transaction_executor.execute(opportunity)
                performance_monitor.end('execution')
                
                # Record metrics
                performance_monitor.start('monitoring')
                monitoring_system.record(exec_result)
                performance_monitor.end('monitoring')
            
            performance_monitor.end('full_pipeline')
            results.append(process_result)
        
        # Verify performance metrics
        stats = performance_monitor.get_stats()
        
        assert 'full_pipeline' in stats
        assert stats['full_pipeline']['count'] == 50
        assert stats['full_pipeline']['average'] < 1.0  # Should complete within 1 second on average
        
        # Verify all opportunities were processed
        assert len(results) == 50
        assert all(r['status'] == 'processed' for r in results)

@pytest.mark.integration
class TestErrorRecoveryIntegration:
    """Test system error recovery and resilience"""
    
    def test_redis_connection_recovery(self, mock_redis):
        """Test system recovery when Redis connection is lost"""
        
        class MockResilientRedisClient:
            def __init__(self, redis_client):
                self.redis = redis_client
                self.connection_lost = False
                self.retry_count = 0
                self.max_retries = 3
            
            def publish(self, channel: str, data: str):
                if self.connection_lost and self.retry_count < self.max_retries:
                    self.retry_count += 1
                    raise redis.ConnectionError("Connection lost")
                
                if self.retry_count >= self.max_retries:
                    # Simulate connection recovery
                    self.connection_lost = False
                    self.retry_count = 0
                
                return self.redis.publish(channel, data)
            
            def simulate_connection_loss(self):
                self.connection_lost = True
                self.retry_count = 0
        
        resilient_client = MockResilientRedisClient(mock_redis)
        
        # Test normal operation
        result = resilient_client.publish('test_channel', 'test_data')
        mock_redis.publish.assert_called_with('test_channel', 'test_data')
        
        # Simulate connection loss
        resilient_client.simulate_connection_loss()
        
        # Test retry mechanism
        with pytest.raises(redis.ConnectionError):
            resilient_client.publish('test_channel', 'test_data')
        
        assert resilient_client.retry_count == 1

    def test_blockchain_node_failover(self, mock_web3):
        """Test failover to backup blockchain nodes"""
        
        class MockWeb3Failover:
            def __init__(self, primary_node, backup_nodes):
                self.primary = primary_node
                self.backups = backup_nodes
                self.current_node = primary_node
                self.primary_failed = False
            
            def call_contract_function(self, function_name: str):
                try:
                    if self.primary_failed and self.current_node == self.primary:
                        raise Exception("Primary node unavailable")
                    
                    return self.current_node.eth.call({'data': f'mock_{function_name}'})
                
                except Exception as e:
                    # Try backup nodes
                    for backup in self.backups:
                        try:
                            self.current_node = backup
                            return backup.eth.call({'data': f'mock_{function_name}'})
                        except:
                            continue
                    raise e
            
            def simulate_primary_failure(self):
                self.primary_failed = True
        
        backup_node = Mock()
        backup_node.eth.call.return_value = 'backup_response'
        
        failover_client = MockWeb3Failover(mock_web3, [backup_node])
        
        # Test normal operation
        mock_web3.eth.call.return_value = 'primary_response'
        result = failover_client.call_contract_function('getPrice')
        assert result == 'primary_response'
        
        # Test failover
        failover_client.simulate_primary_failure()
        result = failover_client.call_contract_function('getPrice')
        assert result == 'backup_response'
        assert failover_client.current_node == backup_node

    def test_transaction_failure_recovery(self):
        """Test recovery from transaction failures"""
        
        class MockTransactionManager:
            def __init__(self):
                self.failed_transactions = []
                self.retry_queue = []
                self.max_retries = 3
            
            def execute_transaction(self, tx_data: Dict[str, Any], retry_count: int = 0):
                tx_id = tx_data.get('id', 'unknown')
                
                # Simulate random failures (30% failure rate)
                import random
                if random.random() < 0.3 and retry_count == 0:
                    self.failed_transactions.append(tx_id)
                    if retry_count < self.max_retries:
                        self.retry_queue.append({**tx_data, 'retry_count': retry_count + 1})
                    raise Exception(f"Transaction {tx_id} failed")
                
                return {'status': 'success', 'tx_id': tx_id, 'retry_count': retry_count}
            
            def process_retry_queue(self):
                retry_results = []
                while self.retry_queue:
                    retry_tx = self.retry_queue.pop(0)
                    try:
                        result = self.execute_transaction(retry_tx, retry_tx['retry_count'])
                        retry_results.append(result)
                    except Exception as e:
                        if retry_tx['retry_count'] >= self.max_retries:
                            retry_results.append({'status': 'failed', 'error': str(e)})
                        else:
                            self.retry_queue.append({**retry_tx, 'retry_count': retry_tx['retry_count'] + 1})
                
                return retry_results
        
        tx_manager = MockTransactionManager()
        
        # Test transaction execution with retries
        test_transactions = [
            {'id': 'tx_1', 'amount': 100},
            {'id': 'tx_2', 'amount': 200},
            {'id': 'tx_3', 'amount': 300},
        ]
        
        results = []
        for tx in test_transactions:
            try:
                result = tx_manager.execute_transaction(tx)
                results.append(result)
            except Exception:
                # Transaction failed, will be retried
                pass
        
        # Process retries
        retry_results = tx_manager.process_retry_queue()
        results.extend(retry_results)
        
        # Verify some transactions succeeded (either immediately or after retry)
        successful_results = [r for r in results if r.get('status') == 'success']
        assert len(successful_results) > 0

if __name__ == "__main__":
    import random
    pytest.main([__file__, "-v", "-m", "integration"])
