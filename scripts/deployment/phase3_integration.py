"""
Phase 3 Integration Script

This script integrates all components of Phase 3:
- MATLAB-Powered Advanced Trading Strategies
- Cross-Chain Expansion
- Regulatory Compliance Framework

It serves as the main entry point for the Phase 3 implementation.
"""

import os
import sys
import json
import time
import logging
import asyncio
import argparse
from typing import Dict, List, Any, Optional
import signal
import datetime
import traceback

# Import Phase 3 modules
from universal_bridge_protocol import UniversalBridgeProtocol, MessageType, ChainType, SecurityLevel
from cross_chain_mev_protection import CrossChainMEVProtection, ProtectionLevel
from atomic_cross_chain_arbitrage import AtomicCrossChainArbitrage, ArbitrageStatus
from transaction_monitoring import TransactionMonitoring, TransactionRiskLevel, AlertStatus
from regulatory_reporting import RegulatoryReporting, ReportStatus, ReportFrequency
from aml_kyc_integration import AMLKYCIntegration, VerificationStatus, RiskLevel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/phase3_integration.log")
    ]
)
logger = logging.getLogger("phase3_integration")

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)
os.makedirs("configs", exist_ok=True)
os.makedirs("reports", exist_ok=True)
os.makedirs("reports/regulatory", exist_ok=True)

class Phase3Integration:
    """
    Main integration class for Phase 3 components.
    
    This class initializes and manages all Phase 3 components:
    - MATLAB-Powered Advanced Trading Strategies
    - Cross-Chain Expansion
    - Regulatory Compliance Framework
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the Phase 3 integration.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.config = self._load_config(config_path)
        
        # Component instances
        self.bridge_protocol = None
        self.mev_protection = None
        self.atomic_arbitrage = None
        self.transaction_monitoring = None
        self.regulatory_reporting = None
        self.aml_kyc_integration = None
        
        # MATLAB engine
        self.matlab_engine = None
        
        # State
        self.running = False
        self.components_initialized = False
        
        logger.info(f"Phase 3 Integration initialized with config from {config_path}")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Configuration dictionary
        """
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    async def initialize_components(self):
        """Initialize all Phase 3 components"""
        try:
            # Create config directories and files if they don't exist
            self._ensure_config_files()
            
            # Initialize Cross-Chain components
            if self.config["cross_chain"]["enabled"]:
                await self._initialize_cross_chain()
            
            # Initialize Regulatory Compliance components
            if self.config["regulatory_compliance"]["enabled"]:
                await self._initialize_regulatory_compliance()
            
            # Initialize MATLAB integration
            if self.config["matlab_integration"]["enabled"]:
                await self._initialize_matlab()
            
            # Register callbacks between components
            self._register_cross_component_callbacks()
            
            self.components_initialized = True
            logger.info("All Phase 3 components initialized successfully")
        
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            traceback.print_exc()
            raise
    
    def _ensure_config_files(self):
        """Ensure all required config files exist"""
        # Bridge config
        bridge_config_path = self.config["cross_chain"]["bridge_protocol"]["config_path"]
        os.makedirs(os.path.dirname(bridge_config_path), exist_ok=True)
        if not os.path.exists(bridge_config_path):
            with open(bridge_config_path, 'w') as f:
                json.dump({
                    "chains": self.config["cross_chain"]["bridge_protocol"]["chains"],
                    "global_settings": {
                        "default_security_level": "MEDIUM",
                        "message_timeout_seconds": 300,
                        "max_retries": 3,
                        "health_check_interval_seconds": 60,
                        "verification_interval_seconds": 30
                    }
                }, f, indent=2)
        
        # MEV config
        mev_config_path = self.config["cross_chain"]["mev_protection"]["config_path"]
        os.makedirs(os.path.dirname(mev_config_path), exist_ok=True)
        if not os.path.exists(mev_config_path):
            with open(mev_config_path, 'w') as f:
                json.dump({
                    "chains": self.config["cross_chain"]["mev_protection"]["chains"],
                    "global_settings": {
                        "default_protection_level": self.config["cross_chain"]["mev_protection"]["protection_level"],
                        "monitoring_interval_seconds": self.config["cross_chain"]["mev_protection"]["monitoring_interval_seconds"],
                        "stats_update_interval_seconds": self.config["cross_chain"]["mev_protection"]["stats_update_interval_seconds"],
                        "threat_retention_days": 7,
                        "min_threat_severity": 3,
                        "min_threat_confidence": 0.6
                    }
                }, f, indent=2)
        
        # Arbitrage config
        arbitrage_config_path = self.config["cross_chain"]["atomic_arbitrage"]["config_path"]
        os.makedirs(os.path.dirname(arbitrage_config_path), exist_ok=True)
        if not os.path.exists(arbitrage_config_path):
            with open(arbitrage_config_path, 'w') as f:
                json.dump({
                    "tokens": self.config["cross_chain"]["atomic_arbitrage"]["tokens"],
                    "global_settings": {
                        "scan_interval_seconds": self.config["cross_chain"]["atomic_arbitrage"]["scan_interval_seconds"],
                        "execution_interval_seconds": self.config["cross_chain"]["atomic_arbitrage"]["execution_interval_seconds"],
                        "market_data_update_seconds": self.config["cross_chain"]["atomic_arbitrage"]["market_data_update_seconds"],
                        "min_profit_threshold_usd": self.config["cross_chain"]["atomic_arbitrage"]["min_profit_threshold_usd"],
                        "min_profit_percentage": self.config["cross_chain"]["atomic_arbitrage"]["min_profit_percentage"],
                        "max_gas_percentage": self.config["cross_chain"]["atomic_arbitrage"]["max_gas_percentage"],
                        "max_slippage_percentage": self.config["cross_chain"]["atomic_arbitrage"]["max_slippage_percentage"],
                        "default_execution_strategy": self.config["cross_chain"]["atomic_arbitrage"]["default_execution_strategy"],
                        "max_concurrent_executions": self.config["cross_chain"]["atomic_arbitrage"]["max_concurrent_executions"],
                        "opportunity_timeout_seconds": self.config["cross_chain"]["atomic_arbitrage"]["opportunity_timeout_seconds"]
                    }
                }, f, indent=2)
        
        # Transaction monitoring config
        monitoring_config_path = self.config["regulatory_compliance"]["transaction_monitoring"]["config_path"]
        os.makedirs(os.path.dirname(monitoring_config_path), exist_ok=True)
        if not os.path.exists(monitoring_config_path):
            with open(monitoring_config_path, 'w') as f:
                json.dump({
                    "rules": self.config["regulatory_compliance"]["transaction_monitoring"]["rules"],
                    "global_settings": {
                        "backlog_processing_interval_seconds": self.config["regulatory_compliance"]["transaction_monitoring"]["backlog_processing_interval_seconds"],
                        "risk_data_update_interval_seconds": self.config["regulatory_compliance"]["transaction_monitoring"]["risk_data_update_interval_seconds"],
                        "report_generation_interval_seconds": self.config["regulatory_compliance"]["transaction_monitoring"]["report_generation_interval_seconds"],
                        "default_alert_assignment": self.config["regulatory_compliance"]["transaction_monitoring"]["default_alert_assignment"],
                        "transaction_retention_days": self.config["regulatory_compliance"]["transaction_monitoring"]["transaction_retention_days"],
                        "alert_retention_days": self.config["regulatory_compliance"]["transaction_monitoring"]["alert_retention_days"],
                        "report_retention_days": self.config["regulatory_compliance"]["transaction_monitoring"]["report_retention_days"]
                    }
                }, f, indent=2)
        
        # Regulatory reporting config
        reporting_config_path = self.config["regulatory_compliance"]["regulatory_reporting"]["config_path"]
        os.makedirs(os.path.dirname(reporting_config_path), exist_ok=True)
        if not os.path.exists(reporting_config_path):
            with open(reporting_config_path, 'w') as f:
                json.dump({
                    "templates": self.config["regulatory_compliance"]["regulatory_reporting"]["templates"],
                    "global_settings": {
                        "schedule_check_interval_seconds": self.config["regulatory_compliance"]["regulatory_reporting"]["schedule_check_interval_seconds"],
                        "cleanup_interval_seconds": self.config["regulatory_compliance"]["regulatory_reporting"]["cleanup_interval_seconds"],
                        "report_retention_days": self.config["regulatory_compliance"]["regulatory_reporting"]["report_retention_days"],
                        "default_reviewer": self.config["regulatory_compliance"]["regulatory_reporting"]["default_reviewer"],
                        "default_submitter": self.config["regulatory_compliance"]["regulatory_reporting"]["default_submitter"],
                        "notification_enabled": self.config["regulatory_compliance"]["regulatory_reporting"]["notification_enabled"],
                        "default_notification_emails": []
                    }
                }, f, indent=2)
        
        # AML/KYC config
        aml_kyc_config_path = self.config["regulatory_compliance"]["aml_kyc_integration"]["config_path"]
        os.makedirs(os.path.dirname(aml_kyc_config_path), exist_ok=True)
        if not os.path.exists(aml_kyc_config_path):
            with open(aml_kyc_config_path, 'w') as f:
                json.dump({
                    "kyc_providers": self.config["regulatory_compliance"]["aml_kyc_integration"]["kyc_providers"],
                    "aml_providers": self.config["regulatory_compliance"]["aml_kyc_integration"]["aml_providers"],
                    "global_settings": {
                        "verification_check_interval_seconds": self.config["regulatory_compliance"]["aml_kyc_integration"]["verification_check_interval_seconds"],
                        "monitoring_interval_seconds": self.config["regulatory_compliance"]["aml_kyc_integration"]["monitoring_interval_seconds"],
                        "expired_verification_check_interval_seconds": self.config["regulatory_compliance"]["aml_kyc_integration"]["expired_verification_check_interval_seconds"],
                        "verification_expiry_days": self.config["regulatory_compliance"]["aml_kyc_integration"]["verification_expiry_days"],
                        "default_verification_level": self.config["regulatory_compliance"]["aml_kyc_integration"]["default_verification_level"],
                        "default_risk_level": self.config["regulatory_compliance"]["aml_kyc_integration"]["default_risk_level"],
                        "notification_enabled": self.config["regulatory_compliance"]["aml_kyc_integration"]["notification_enabled"],
                        "default_notification_emails": []
                    }
                }, f, indent=2)
    
    async def _initialize_cross_chain(self):
        """Initialize Cross-Chain components"""
        logger.info("Initializing Cross-Chain components...")
        
        # Initialize Universal Bridge Protocol
        bridge_config_path = self.config["cross_chain"]["bridge_protocol"]["config_path"]
        self.bridge_protocol = UniversalBridgeProtocol(bridge_config_path)
        
        # Set security level
        security_level_str = self.config["cross_chain"]["bridge_protocol"]["security_level"]
        self.bridge_protocol.set_security_level(SecurityLevel[security_level_str])
        
        # Initialize MEV Protection
        mev_config_path = self.config["cross_chain"]["mev_protection"]["config_path"]
        self.mev_protection = CrossChainMEVProtection(mev_config_path)
        
        # Set protection level
        protection_level_str = self.config["cross_chain"]["mev_protection"]["protection_level"]
        self.mev_protection.set_protection_level(ProtectionLevel[protection_level_str])
        
        # Initialize Atomic Cross-Chain Arbitrage
        arbitrage_config_path = self.config["cross_chain"]["atomic_arbitrage"]["config_path"]
        self.atomic_arbitrage = AtomicCrossChainArbitrage(arbitrage_config_path)
        
        logger.info("Cross-Chain components initialized successfully")
    
    async def _initialize_regulatory_compliance(self):
        """Initialize Regulatory Compliance components"""
        logger.info("Initializing Regulatory Compliance components...")
        
        # Initialize Transaction Monitoring
        monitoring_config_path = self.config["regulatory_compliance"]["transaction_monitoring"]["config_path"]
        self.transaction_monitoring = TransactionMonitoring(monitoring_config_path)
        
        # Initialize Regulatory Reporting
        reporting_config_path = self.config["regulatory_compliance"]["regulatory_reporting"]["config_path"]
        output_dir = self.config["regulatory_compliance"]["regulatory_reporting"]["output_dir"]
        os.makedirs(output_dir, exist_ok=True)
        self.regulatory_reporting = RegulatoryReporting(reporting_config_path, output_dir)
        
        # Initialize AML/KYC Integration
        aml_kyc_config_path = self.config["regulatory_compliance"]["aml_kyc_integration"]["config_path"]
        self.aml_kyc_integration = AMLKYCIntegration(aml_kyc_config_path)
        
        logger.info("Regulatory Compliance components initialized successfully")
    
    async def _initialize_matlab(self):
        """Initialize MATLAB integration"""
        logger.info("Initializing MATLAB integration...")
        
        try:
            # In a real implementation, this would initialize the MATLAB engine
            # For demonstration, we'll just log that it's initialized
            
            # Create model directory if it doesn't exist
            model_dir = self.config["matlab_integration"]["model_directory"]
            os.makedirs(model_dir, exist_ok=True)
            
            # Create data directory if it doesn't exist
            data_dir = self.config["matlab_integration"]["data_directory"]
            os.makedirs(data_dir, exist_ok=True)
            
            # Create output directory if it doesn't exist
            output_dir = self.config["matlab_integration"]["output_directory"]
            os.makedirs(output_dir, exist_ok=True)
            
            # Create log directory if it doesn't exist
            log_dir = self.config["matlab_integration"]["log_directory"]
            os.makedirs(log_dir, exist_ok=True)
            
            logger.info("MATLAB integration initialized successfully")
        
        except Exception as e:
            logger.error(f"Failed to initialize MATLAB integration: {e}")
            raise
    
    def _register_cross_component_callbacks(self):
        """Register callbacks between components"""
        # Bridge Protocol -> Transaction Monitoring
        self.bridge_protocol.register_callback("message_confirmed", self._handle_bridge_message_confirmed)
        
        # MEV Protection -> Transaction Monitoring
        self.mev_protection.register_callback("threat_detected", self._handle_mev_threat_detected)
        
        # Atomic Arbitrage -> Transaction Monitoring
        self.atomic_arbitrage.register_callback("arbitrage_completed", self._handle_arbitrage_completed)
        
        # Transaction Monitoring -> Regulatory Reporting
        self.transaction_monitoring.register_callback("alert_generated", self._handle_compliance_alert)
        
        # AML/KYC -> Transaction Monitoring
        self.aml_kyc_integration.register_callback("screening_completed", self._handle_screening_completed)
        
        logger.info("Cross-component callbacks registered")
    
    def _handle_bridge_message_confirmed(self, message):
        """Handle confirmed bridge messages"""
        # In a real implementation, this would create a transaction record
        # for the bridge message and process it through transaction monitoring
        
        if self.transaction_monitoring:
            asyncio.create_task(self._process_bridge_transaction(message))
    
    async def _process_bridge_transaction(self, message):
        """Process a bridge transaction through transaction monitoring"""
        # Create a transaction record for the bridge message
        transaction = {
            "transaction_id": str(message.message_id),
            "blockchain": f"chain_{message.destination_chain_id}",
            "tx_hash": message.transaction_hash or f"tx_{message.message_id}",
            "from_address": f"bridge_{message.source_chain_id}",
            "to_address": message.payload.get("recipient", f"unknown_{message.destination_chain_id}"),
            "token": message.payload.get("asset", "UNKNOWN"),
            "amount": float(message.payload.get("amount", 0)),
            "amount_usd": 0,  # Would be calculated in a real implementation
            "timestamp": int(time.time()),
            "block_number": 0,  # Would be set in a real implementation
            "gas_used": 0,      # Would be set in a real implementation
            "gas_price": 0,     # Would be set in a real implementation
            "status": "confirmed",
            "metadata": {
                "source_chain_id": message.source_chain_id,
                "destination_chain_id": message.destination_chain_id,
                "message_type": message.message_type.value,
                "bridge_message_id": message.message_id
            }
        }
        
        logger.info(f"Processing bridge transaction: {transaction['transaction_id']}")
        
        # Process through transaction monitoring
        await self.transaction_monitoring.process_transaction(transaction)
    
    def _handle_mev_threat_detected(self, threat):
        """Handle detected MEV threats"""
        # In a real implementation, this would create a compliance alert
        # for the MEV threat
        
        if self.transaction_monitoring:
            # Create a compliance alert for the MEV threat
            alert = {
                "alert_id": str(threat.threat_id),
                "transaction_id": None,  # No specific transaction
                "rule_triggered": "mev_threat",
                "risk_level": "high" if threat.severity >= 7 else "medium",
                "description": f"MEV threat detected: {threat.description}",
                "timestamp": int(time.time()),
                "status": "new",
                "assigned_to": "security_team",
                "resolution_notes": None,
                "resolution_timestamp": None,
                "related_alerts": []
            }
            
            logger.info(f"MEV threat alert generated: {alert['alert_id']}")
            
            # Trigger alert callback
            self._handle_compliance_alert(alert)
    
    def _handle_arbitrage_completed(self, result):
        """Handle completed arbitrage operations"""
        # In a real implementation, this would create transaction records
        # for the arbitrage operation and process them through transaction monitoring
        
        if self.transaction_monitoring:
            asyncio.create_task(self._process_arbitrage_transaction(result))
    
    async def _process_arbitrage_transaction(self, result):
        """Process an arbitrage transaction through transaction monitoring"""
        # Create a transaction record for the arbitrage operation
        transaction = {
            "transaction_id": str(result.opportunity_id),
            "blockchain": "multi_chain",  # Arbitrage spans multiple chains
            "tx_hash": next(iter(result.transaction_hashes.values())) if result.transaction_hashes else f"arb_{result.opportunity_id}",
            "from_address": "arbitrage_engine",
            "to_address": "arbitrage_engine",
            "token": "MULTI",  # Multiple tokens involved
            "amount": 0,       # Would be set in a real implementation
            "amount_usd": result.actual_profit_usd,
            "timestamp": int(time.time()),
            "block_number": 0,  # Would be set in a real implementation
            "gas_used": 0,      # Would be set in a real implementation
            "gas_price": 0,     # Would be set in a real implementation
            "status": "confirmed" if result.status == ArbitrageStatus.COMPLETED else "failed",
            "metadata": {
                "opportunity_id": result.opportunity_id,
                "profit_percentage": result.actual_profit_percentage,
                "gas_used_usd": result.gas_used_usd,
                "execution_time_ms": result.execution_time_ms,
                "transaction_hashes": result.transaction_hashes
            }
        }
        
        logger.info(f"Processing arbitrage transaction: {transaction['transaction_id']}")
        
        # Process through transaction monitoring
        await self.transaction_monitoring.process_transaction(transaction)
    
    def _handle_compliance_alert(self, alert):
        """Handle compliance alerts"""
        # In a real implementation, this would trigger regulatory reporting
        # for high-risk alerts
        
        if self.regulatory_reporting:
            # Check if alert is high risk
            if alert.risk_level in [TransactionRiskLevel.HIGH, TransactionRiskLevel.CRITICAL]:
                asyncio.create_task(self._generate_regulatory_report(alert))
    
    async def _generate_regulatory_report(self, alert):
        """Generate a regulatory report for a high-risk alert"""
        # Determine report type based on alert
        if "sanctioned" in alert.rule_triggered.value:
            template_id = "sar_template"
        elif "amount_threshold" in alert.rule_triggered.value:
            template_id = "ctr_template"
        else:
            template_id = "sar_template"  # Default to SAR
        
        # Generate report parameters
        parameters = {
            "generated_by": "system",
            "alert_id": alert.alert_id,
            "transaction_id": alert.transaction_id,
            "risk_level": alert.risk_level.value,
            "date_range": {
                "start_date": datetime.datetime.fromtimestamp(alert.timestamp).strftime("%Y-%m-%d"),
                "end_date": datetime.datetime.now().strftime("%Y-%m-%d")
            },
            "notification_emails": ["compliance@example.com"]
        }
        
        logger.info(f"Generating regulatory report for alert: {alert.alert_id}")
        
        # Generate report
        report_id = await self.regulatory_reporting.generate_on_demand_report(template_id, parameters)
        
        if report_id:
            logger.info(f"Regulatory report generated: {report_id}")
    
    def _handle_screening_completed(self, screening):
        """Handle completed AML screenings"""
        # In a real implementation, this would create compliance alerts
        # for high-risk screening results
        
        if self.transaction_monitoring and screening.result.value in ["match", "possible_match"]:
            # Create a compliance alert for the screening result
            alert = {
                "alert_id": str(screening.screening_id),
                "transaction_id": None,  # No specific transaction
                "rule_triggered": "aml_screening",
                "risk_level": "high" if screening.result.value == "match" else "medium",
                "description": f"AML screening alert: {screening.result.value} found in {screening.screening_type} screening",
                "timestamp": int(time.time()),
                "status": "new",
                "assigned_to": "compliance_team",
                "resolution_notes": None,
                "resolution_timestamp": None,
                "related_alerts": []
            }
            
            logger.info(f"AML screening alert generated: {alert['alert_id']}")
            
            # Trigger alert callback
            self._handle_compliance_alert(alert)
    
    async def start(self):
        """Start the Phase 3 integration"""
        if self.running:
            logger.warning("Phase 3 integration is already running")
            return
        
        logger.info("Starting Phase 3 integration...")
        
        # Initialize components if not already initialized
        if not self.components_initialized:
            await self.initialize_components()
        
        self.running = True
        
        logger.info("Phase 3 integration started successfully")
    
    async def stop(self):
        """Stop the Phase 3 integration"""
        if not self.running:
            logger.warning("Phase 3 integration is not running")
            return
        
        logger.info("Stopping Phase 3 integration...")
        
        # Stop components
        tasks = []
        
        if self.bridge_protocol:
            tasks.append(self.bridge_protocol.shutdown())
        
        if self.mev_protection:
            tasks.append(self.mev_protection.shutdown())
        
        if self.atomic_arbitrage:
            tasks.append(self.atomic_arbitrage.shutdown())
        
        if self.transaction_monitoring:
            tasks.append(self.transaction_monitoring.shutdown())
        
        if self.regulatory_reporting:
            tasks.append(self.regulatory_reporting.shutdown())
        
        if self.aml_kyc_integration:
            tasks.append(self.aml_kyc_integration.shutdown())
        
        # Wait for all components to shut down
        await asyncio.gather(*tasks)
        
        self.running = False
        
        logger.info("Phase 3 integration stopped successfully")
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get the status of all Phase 3 components.
        
        Returns:
            Status information for all components
        """
        status = {
            "running": self.running,
            "components_initialized": self.components_initialized,
            "timestamp": int(time.time()),
            "components": {}
        }
        
        # Bridge Protocol status
        if self.bridge_protocol:
            status["components"]["bridge_protocol"] = self.bridge_protocol.get_bridge_status()
        
        # MEV Protection status
        if self.mev_protection:
            status["components"]["mev_protection"] = self.mev_protection.get_protection_status()
        
        # Atomic Arbitrage status
        if self.atomic_arbitrage:
            status["components"]["atomic_arbitrage"] = self.atomic_arbitrage.get_arbitrage_status()
        
        # Transaction Monitoring status
        if self.transaction_monitoring:
            status["components"]["transaction_monitoring"] = self.transaction_monitoring.get_compliance_statistics()
        
        # Regulatory Reporting status
        if self.regulatory_reporting:
            status["components"]["regulatory_reporting"] = self.regulatory_reporting.get_reporting_statistics()
        
        # AML/KYC Integration status
        if self.aml_kyc_integration:
            status["components"]["aml_kyc_integration"] = self.aml_kyc_integration.get_aml_kyc_statistics()
        
        return status


async def main():
    """Main entry point for the Phase 3 integration"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Phase 3 Integration")
    parser.add_argument("--config", default="phase3_config.json", help="Path to configuration file")
    args = parser.parse_args()
    
    # Create Phase 3 integration
    integration = Phase3Integration(args.config)
    
    # Set up signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(integration)))
    
    try:
        # Start integration
        await integration.start()
        
        # Keep running until stopped
        while integration.running:
            await asyncio.sleep(1)
    
    except Exception as e:
        logger.error(f"Error in Phase 3 integration: {e}")
        traceback.print_exc()
    
    finally:
        # Ensure integration is stopped
        if integration.running:
            await integration.stop()


async def shutdown(integration: Phase3Integration):
    """Shutdown the integration gracefully"""
    logger.info("Shutting down Phase 3 integration...")
    await integration.stop()


if __name__ == "__main__":
    asyncio.run(main())