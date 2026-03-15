"""
Transaction Monitoring for Regulatory Compliance

This module implements advanced transaction monitoring capabilities for
regulatory compliance, including AML/KYC checks, suspicious activity detection,
and regulatory reporting.

Features:
- Real-time transaction monitoring
- Risk scoring and assessment
- Suspicious activity detection
- Regulatory reporting automation
- Compliance audit trails
"""

import json
import time
import hashlib
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Union, Callable, Set
from enum import Enum
from dataclasses import dataclass
import uuid
import random
import datetime
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("transaction_monitoring")

class TransactionRiskLevel(Enum):
    """Risk levels for transactions"""
    NEGLIGIBLE = "negligible"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Status of compliance alerts"""
    NEW = "new"
    INVESTIGATING = "investigating"
    ESCALATED = "escalated"
    REPORTED = "reported"
    CLOSED_FALSE_POSITIVE = "closed_false_positive"
    CLOSED_RESOLVED = "closed_resolved"


class ReportType(Enum):
    """Types of regulatory reports"""
    SAR = "suspicious_activity_report"
    CTR = "currency_transaction_report"
    STR = "suspicious_transaction_report"
    FINCEN = "fincen_report"
    FATF = "fatf_report"
    CUSTOM = "custom_report"


class MonitoringRule(Enum):
    """Transaction monitoring rule types"""
    VELOCITY = "velocity"
    AMOUNT_THRESHOLD = "amount_threshold"
    JURISDICTION = "jurisdiction"
    PATTERN = "pattern"
    COUNTERPARTY = "counterparty"
    SANCTIONED_ENTITY = "sanctioned_entity"
    STRUCTURING = "structuring"
    UNUSUAL_BEHAVIOR = "unusual_behavior"
    HIGH_RISK_CATEGORY = "high_risk_category"


@dataclass
class Transaction:
    """Transaction data structure"""
    transaction_id: str
    blockchain: str
    tx_hash: str
    from_address: str
    to_address: str
    token: str
    amount: float
    amount_usd: float
    timestamp: int
    block_number: int
    gas_used: int
    gas_price: int
    status: str
    metadata: Dict[str, Any]


@dataclass
class ComplianceAlert:
    """Compliance alert data structure"""
    alert_id: str
    transaction_id: str
    rule_triggered: MonitoringRule
    risk_level: TransactionRiskLevel
    description: str
    timestamp: int
    status: AlertStatus
    assigned_to: Optional[str]
    resolution_notes: Optional[str]
    resolution_timestamp: Optional[int]
    related_alerts: List[str]


@dataclass
class RegulatoryReport:
    """Regulatory report data structure"""
    report_id: str
    report_type: ReportType
    reference_number: Optional[str]
    alert_ids: List[str]
    transaction_ids: List[str]
    submission_timestamp: Optional[int]
    due_date: int
    status: str
    submitted_by: Optional[str]
    regulatory_body: str
    report_data: Dict[str, Any]


class TransactionMonitoring:
    """
    Transaction Monitoring system for regulatory compliance.
    
    This class provides advanced transaction monitoring capabilities for
    regulatory compliance, including AML/KYC checks, suspicious activity detection,
    and regulatory reporting.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the Transaction Monitoring system.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_config(config_path)
        self.monitoring_rules: Dict[str, Dict[str, Any]] = {}
        self.transactions: Dict[str, Transaction] = {}
        self.alerts: Dict[str, ComplianceAlert] = {}
        self.reports: Dict[str, RegulatoryReport] = {}
        self.address_risk_scores: Dict[str, Dict[str, Any]] = {}
        self.sanctioned_addresses: Set[str] = set()
        self.high_risk_jurisdictions: Set[str] = set()
        
        self.callbacks: Dict[str, List[Callable]] = {
            "transaction_processed": [],
            "alert_generated": [],
            "alert_updated": [],
            "report_created": [],
            "report_submitted": []
        }
        
        # Initialize configurations
        self._initialize_configs()
        
        # Start background tasks
        self.running = True
        self.background_tasks = [
            asyncio.create_task(self._process_transaction_backlog()),
            asyncio.create_task(self._update_risk_data()),
            asyncio.create_task(self._generate_periodic_reports())
        ]
        
        logger.info(f"Transaction Monitoring initialized with {len(self.monitoring_rules)} rules")
    
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
            # Use default configuration as fallback
            return {
                "rules": [],
                "sanctioned_entities": [],
                "high_risk_jurisdictions": [],
                "global_settings": {
                    "backlog_processing_interval_seconds": 60,
                    "risk_data_update_interval_seconds": 3600,
                    "report_generation_interval_seconds": 86400,
                    "default_alert_assignment": "compliance_team",
                    "transaction_retention_days": 90,
                    "alert_retention_days": 365,
                    "report_retention_days": 1825  # 5 years
                }
            }
    
    def _initialize_configs(self):
        """Initialize configurations from the loaded config"""
        # Initialize monitoring rules
        for rule_config in self.config.get("rules", []):
            try:
                rule_id = rule_config["id"]
                self.monitoring_rules[rule_id] = rule_config
                logger.info(f"Initialized monitoring rule: {rule_id} ({rule_config['name']})")
            except Exception as e:
                logger.error(f"Failed to initialize monitoring rule: {e}")
        
        # Initialize sanctioned addresses
        for entity in self.config.get("sanctioned_entities", []):
            try:
                if "addresses" in entity:
                    for address in entity["addresses"]:
                        self.sanctioned_addresses.add(address.lower())
                logger.info(f"Added sanctioned entity: {entity.get('name', 'Unknown')}")
            except Exception as e:
                logger.error(f"Failed to add sanctioned entity: {e}")
        
        # Initialize high-risk jurisdictions
        for jurisdiction in self.config.get("high_risk_jurisdictions", []):
            try:
                self.high_risk_jurisdictions.add(jurisdiction["code"])
                logger.info(f"Added high-risk jurisdiction: {jurisdiction['name']} ({jurisdiction['code']})")
            except Exception as e:
                logger.error(f"Failed to add high-risk jurisdiction: {e}")
    
    async def _process_transaction_backlog(self):
        """Background task to process transaction backlog"""
        interval = self.config["global_settings"]["backlog_processing_interval_seconds"]
        while self.running:
            try:
                # In a real implementation, this would fetch unprocessed transactions
                # from a database or message queue. For demonstration, we'll simulate
                # processing by generating random transactions.
                
                # Generate a random number of transactions (0-5)
                num_transactions = random.randint(0, 5)
                
                for _ in range(num_transactions):
                    # Generate a random transaction
                    transaction = self._generate_random_transaction()
                    
                    # Process the transaction
                    await self.process_transaction(transaction)
                
                # Clean up old data
                self._clean_old_data()
            
            except Exception as e:
                logger.error(f"Error processing transaction backlog: {e}")
            
            await asyncio.sleep(interval)
    
    def _generate_random_transaction(self) -> Transaction:
        """
        Generate a random transaction for demonstration purposes.
        
        Returns:
            Random transaction
        """
        # Generate random blockchain
        blockchains = ["ethereum", "binance", "polygon", "arbitrum", "optimism"]
        blockchain = random.choice(blockchains)
        
        # Generate random addresses
        from_address = f"0x{hashlib.sha256(f'from{random.randint(1, 1000)}'.encode()).hexdigest()[:40]}"
        to_address = f"0x{hashlib.sha256(f'to{random.randint(1, 1000)}'.encode()).hexdigest()[:40]}"
        
        # Occasionally use a sanctioned address
        if random.random() < 0.05 and self.sanctioned_addresses:  # 5% chance
            if random.random() < 0.5:
                from_address = random.choice(list(self.sanctioned_addresses))
            else:
                to_address = random.choice(list(self.sanctioned_addresses))
        
        # Generate random token
        tokens = ["ETH", "USDC", "USDT", "DAI", "WBTC", "LINK", "UNI", "AAVE"]
        token = random.choice(tokens)
        
        # Generate random amount
        if token in ["ETH", "WBTC"]:
            amount = random.uniform(0.01, 10)
        else:
            amount = random.uniform(10, 10000)
        
        # Generate USD value
        token_prices = {
            "ETH": 3000,
            "WBTC": 50000,
            "USDC": 1,
            "USDT": 1,
            "DAI": 1,
            "LINK": 20,
            "UNI": 10,
            "AAVE": 100
        }
        amount_usd = amount * token_prices.get(token, 1)
        
        # Generate transaction metadata
        metadata = {
            "gas_limit": random.randint(21000, 300000),
            "nonce": random.randint(0, 1000),
            "input_data": f"0x{hashlib.sha256(f'data{random.randint(1, 1000)}'.encode()).hexdigest()}" if random.random() < 0.7 else "0x",
            "contract_interaction": random.random() < 0.6,  # 60% chance of contract interaction
            "transaction_type": random.choice(["transfer", "swap", "liquidity", "stake", "unstake", "borrow", "repay"])
        }
        
        # Generate transaction
        return Transaction(
            transaction_id=str(uuid.uuid4()),
            blockchain=blockchain,
            tx_hash=f"0x{hashlib.sha256(f'tx{time.time()}{random.random()}'.encode()).hexdigest()}",
            from_address=from_address,
            to_address=to_address,
            token=token,
            amount=amount,
            amount_usd=amount_usd,
            timestamp=int(time.time()),
            block_number=random.randint(10000000, 20000000),
            gas_used=random.randint(21000, 250000),
            gas_price=random.randint(1, 100) * 10**9,  # 1-100 gwei
            status="confirmed",
            metadata=metadata
        )
    
    async def process_transaction(self, transaction: Transaction) -> List[ComplianceAlert]:
        """
        Process a transaction for compliance monitoring.
        
        Args:
            transaction: Transaction to process
            
        Returns:
            List of generated compliance alerts
        """
        # Store transaction
        self.transactions[transaction.transaction_id] = transaction
        
        # Apply monitoring rules
        alerts = self._apply_monitoring_rules(transaction)
        
        # Store generated alerts
        for alert in alerts:
            self.alerts[alert.alert_id] = alert
        
        # Trigger callbacks
        self._trigger_callbacks("transaction_processed", transaction)
        for alert in alerts:
            self._trigger_callbacks("alert_generated", alert)
        
        if alerts:
            logger.warning(
                f"Transaction {transaction.transaction_id} generated {len(alerts)} compliance alerts"
            )
        else:
            logger.info(f"Transaction {transaction.transaction_id} processed with no alerts")
        
        return alerts
    
    def _apply_monitoring_rules(self, transaction: Transaction) -> List[ComplianceAlert]:
        """
        Apply monitoring rules to a transaction.
        
        Args:
            transaction: Transaction to check
            
        Returns:
            List of generated compliance alerts
        """
        alerts = []
        
        # Apply each rule
        for rule_id, rule in self.monitoring_rules.items():
            try:
                # Skip disabled rules
                if not rule.get("enabled", True):
                    continue
                
                # Get rule type
                rule_type = MonitoringRule(rule.get("type", "amount_threshold"))
                
                # Apply rule based on type
                if rule_type == MonitoringRule.AMOUNT_THRESHOLD:
                    if self._check_amount_threshold(transaction, rule):
                        alerts.append(self._create_alert(transaction, rule, rule_type))
                
                elif rule_type == MonitoringRule.SANCTIONED_ENTITY:
                    if self._check_sanctioned_entity(transaction):
                        alerts.append(self._create_alert(transaction, rule, rule_type))
                
                elif rule_type == MonitoringRule.JURISDICTION:
                    if self._check_jurisdiction(transaction, rule):
                        alerts.append(self._create_alert(transaction, rule, rule_type))
                
                elif rule_type == MonitoringRule.VELOCITY:
                    if self._check_velocity(transaction, rule):
                        alerts.append(self._create_alert(transaction, rule, rule_type))
                
                elif rule_type == MonitoringRule.PATTERN:
                    if self._check_pattern(transaction, rule):
                        alerts.append(self._create_alert(transaction, rule, rule_type))
                
                elif rule_type == MonitoringRule.STRUCTURING:
                    if self._check_structuring(transaction, rule):
                        alerts.append(self._create_alert(transaction, rule, rule_type))
                
                elif rule_type == MonitoringRule.UNUSUAL_BEHAVIOR:
                    if self._check_unusual_behavior(transaction, rule):
                        alerts.append(self._create_alert(transaction, rule, rule_type))
                
                elif rule_type == MonitoringRule.HIGH_RISK_CATEGORY:
                    if self._check_high_risk_category(transaction, rule):
                        alerts.append(self._create_alert(transaction, rule, rule_type))
            
            except Exception as e:
                logger.error(f"Error applying rule {rule_id} to transaction {transaction.transaction_id}: {e}")
        
        return alerts
    
    def _check_amount_threshold(self, transaction: Transaction, rule: Dict[str, Any]) -> bool:
        """
        Check if transaction amount exceeds threshold.
        
        Args:
            transaction: Transaction to check
            rule: Rule configuration
            
        Returns:
            True if rule is triggered, False otherwise
        """
        threshold = rule.get("threshold_usd", 10000)
        return transaction.amount_usd >= threshold
    
    def _check_sanctioned_entity(self, transaction: Transaction) -> bool:
        """
        Check if transaction involves a sanctioned entity.
        
        Args:
            transaction: Transaction to check
            
        Returns:
            True if rule is triggered, False otherwise
        """
        from_address = transaction.from_address.lower()
        to_address = transaction.to_address.lower()
        
        return from_address in self.sanctioned_addresses or to_address in self.sanctioned_addresses
    
    def _check_jurisdiction(self, transaction: Transaction, rule: Dict[str, Any]) -> bool:
        """
        Check if transaction involves a high-risk jurisdiction.
        
        Args:
            transaction: Transaction to check
            rule: Rule configuration
            
        Returns:
            True if rule is triggered, False otherwise
        """
        # In a real implementation, this would check the jurisdiction of the addresses
        # For demonstration, we'll randomly determine if a transaction involves a high-risk jurisdiction
        
        # 10% chance of triggering for demonstration
        return random.random() < 0.1
    
    def _check_velocity(self, transaction: Transaction, rule: Dict[str, Any]) -> bool:
        """
        Check if transaction velocity exceeds threshold.
        
        Args:
            transaction: Transaction to check
            rule: Rule configuration
            
        Returns:
            True if rule is triggered, False otherwise
        """
        # In a real implementation, this would check the transaction velocity for an address
        # For demonstration, we'll randomly determine if velocity is exceeded
        
        # 5% chance of triggering for demonstration
        return random.random() < 0.05
    
    def _check_pattern(self, transaction: Transaction, rule: Dict[str, Any]) -> bool:
        """
        Check if transaction matches a suspicious pattern.
        
        Args:
            transaction: Transaction to check
            rule: Rule configuration
            
        Returns:
            True if rule is triggered, False otherwise
        """
        # In a real implementation, this would check for specific transaction patterns
        # For demonstration, we'll randomly determine if a pattern is matched
        
        # 8% chance of triggering for demonstration
        return random.random() < 0.08
    
    def _check_structuring(self, transaction: Transaction, rule: Dict[str, Any]) -> bool:
        """
        Check if transaction is part of a structuring pattern.
        
        Args:
            transaction: Transaction to check
            rule: Rule configuration
            
        Returns:
            True if rule is triggered, False otherwise
        """
        # In a real implementation, this would check for transaction structuring
        # For demonstration, we'll randomly determine if structuring is detected
        
        # 3% chance of triggering for demonstration
        return random.random() < 0.03
    
    def _check_unusual_behavior(self, transaction: Transaction, rule: Dict[str, Any]) -> bool:
        """
        Check if transaction represents unusual behavior.
        
        Args:
            transaction: Transaction to check
            rule: Rule configuration
            
        Returns:
            True if rule is triggered, False otherwise
        """
        # In a real implementation, this would check for unusual behavior based on historical patterns
        # For demonstration, we'll randomly determine if unusual behavior is detected
        
        # 7% chance of triggering for demonstration
        return random.random() < 0.07
    
    def _check_high_risk_category(self, transaction: Transaction, rule: Dict[str, Any]) -> bool:
        """
        Check if transaction falls into a high-risk category.
        
        Args:
            transaction: Transaction to check
            rule: Rule configuration
            
        Returns:
            True if rule is triggered, False otherwise
        """
        # Check if transaction involves privacy coins, mixing services, etc.
        high_risk_tokens = rule.get("high_risk_tokens", ["ZEC", "XMR", "DASH", "GRIN"])
        high_risk_services = rule.get("high_risk_services", ["tornado", "mixer", "wasabi", "samurai"])
        
        # Check token
        if transaction.token in high_risk_tokens:
            return True
        
        # Check if transaction involves a high-risk service
        if "input_data" in transaction.metadata:
            input_data = transaction.metadata["input_data"].lower()
            for service in high_risk_services:
                if service in input_data:
                    return True
        
        return False
    
    def _create_alert(self, transaction: Transaction, rule: Dict[str, Any], rule_type: MonitoringRule) -> ComplianceAlert:
        """
        Create a compliance alert for a triggered rule.
        
        Args:
            transaction: Transaction that triggered the rule
            rule: Rule configuration
            rule_type: Type of rule triggered
            
        Returns:
            Compliance alert
        """
        # Get risk level from rule or default to MEDIUM
        risk_level_str = rule.get("risk_level", "MEDIUM")
        try:
            risk_level = TransactionRiskLevel(risk_level_str.lower())
        except ValueError:
            risk_level = TransactionRiskLevel.MEDIUM
        
        # Create alert description
        description = rule.get("description", f"Transaction triggered {rule_type.value} rule")
        
        # Add transaction details to description
        description += f"\nTransaction: {transaction.tx_hash}"
        description += f"\nAmount: {transaction.amount} {transaction.token} (${transaction.amount_usd:.2f})"
        description += f"\nFrom: {transaction.from_address}"
        description += f"\nTo: {transaction.to_address}"
        
        # Create alert
        alert = ComplianceAlert(
            alert_id=str(uuid.uuid4()),
            transaction_id=transaction.transaction_id,
            rule_triggered=rule_type,
            risk_level=risk_level,
            description=description,
            timestamp=int(time.time()),
            status=AlertStatus.NEW,
            assigned_to=self.config["global_settings"]["default_alert_assignment"],
            resolution_notes=None,
            resolution_timestamp=None,
            related_alerts=[]
        )
        
        return alert
    
    async def _update_risk_data(self):
        """Background task to update risk data"""
        interval = self.config["global_settings"]["risk_data_update_interval_seconds"]
        while self.running:
            try:
                logger.info("Updating risk data")
                
                # In a real implementation, this would fetch updated sanctions lists,
                # high-risk jurisdictions, and other risk data from external sources.
                # For demonstration, we'll simulate updating by adding random addresses.
                
                # Simulate updating sanctioned addresses
                if random.random() < 0.3:  # 30% chance of update
                    num_new_addresses = random.randint(1, 5)
                    for _ in range(num_new_addresses):
                        new_address = f"0x{hashlib.sha256(f'sanctioned{time.time()}{random.random()}'.encode()).hexdigest()[:40]}"
                        self.sanctioned_addresses.add(new_address)
                    
                    logger.info(f"Added {num_new_addresses} new sanctioned addresses")
                
                # Simulate updating high-risk jurisdictions
                if random.random() < 0.2:  # 20% chance of update
                    country_codes = ["KP", "IR", "CU", "SY", "VE", "MM", "BY", "ZW", "NI", "RU"]
                    new_jurisdiction = random.choice([code for code in country_codes if code not in self.high_risk_jurisdictions])
                    self.high_risk_jurisdictions.add(new_jurisdiction)
                    
                    logger.info(f"Added new high-risk jurisdiction: {new_jurisdiction}")
            
            except Exception as e:
                logger.error(f"Error updating risk data: {e}")
            
            await asyncio.sleep(interval)
    
    async def _generate_periodic_reports(self):
        """Background task to generate periodic regulatory reports"""
        interval = self.config["global_settings"]["report_generation_interval_seconds"]
        while self.running:
            try:
                # Generate reports for alerts that need reporting
                await self._generate_required_reports()
                
                # In a real implementation, this would also generate scheduled reports
                # such as monthly/quarterly compliance summaries.
            
            except Exception as e:
                logger.error(f"Error generating periodic reports: {e}")
            
            await asyncio.sleep(interval)
    
    async def _generate_required_reports(self):
        """Generate required regulatory reports for outstanding alerts"""
        # Find alerts that need reporting
        reportable_alerts = []
        for alert_id, alert in self.alerts.items():
            # Check if alert is high risk and not already reported
            if (alert.risk_level in [TransactionRiskLevel.HIGH, TransactionRiskLevel.CRITICAL] and
                alert.status not in [AlertStatus.REPORTED, AlertStatus.CLOSED_FALSE_POSITIVE]):
                reportable_alerts.append(alert)
        
        if not reportable_alerts:
            return
        
        logger.info(f"Generating reports for {len(reportable_alerts)} reportable alerts")
        
        # Group alerts by type for reporting
        sar_alerts = []
        ctr_alerts = []
        
        for alert in reportable_alerts:
            if alert.rule_triggered in [MonitoringRule.SANCTIONED_ENTITY, MonitoringRule.UNUSUAL_BEHAVIOR, 
                                       MonitoringRule.PATTERN, MonitoringRule.STRUCTURING]:
                sar_alerts.append(alert)
            elif alert.rule_triggered == MonitoringRule.AMOUNT_THRESHOLD:
                ctr_alerts.append(alert)
            else:
                # Default to SAR for other alert types
                sar_alerts.append(alert)
        
        # Generate SAR if needed
        if sar_alerts:
            await self.create_regulatory_report(ReportType.SAR, sar_alerts)
        
        # Generate CTR if needed
        if ctr_alerts:
            await self.create_regulatory_report(ReportType.CTR, ctr_alerts)
    
    async def create_regulatory_report(self, report_type: ReportType, alerts: List[ComplianceAlert]) -> RegulatoryReport:
        """
        Create a regulatory report for a set of alerts.
        
        Args:
            report_type: Type of report to create
            alerts: Alerts to include in the report
            
        Returns:
            Created regulatory report
        """
        # Get transaction IDs from alerts
        transaction_ids = [alert.transaction_id for alert in alerts]
        alert_ids = [alert.alert_id for alert in alerts]
        
        # Get transactions
        transactions = [self.transactions.get(tx_id) for tx_id in transaction_ids if tx_id in self.transactions]
        
        # Generate report data
        report_data = self._generate_report_data(report_type, alerts, transactions)
        
        # Determine regulatory body based on report type
        regulatory_bodies = {
            ReportType.SAR: "FinCEN",
            ReportType.CTR: "FinCEN",
            ReportType.STR: "FATF",
            ReportType.FINCEN: "FinCEN",
            ReportType.FATF: "FATF",
            ReportType.CUSTOM: "Internal"
        }
        
        regulatory_body = regulatory_bodies.get(report_type, "Unknown")
        
        # Calculate due date (30 days from now for SARs, 15 days for CTRs, etc.)
        due_days = {
            ReportType.SAR: 30,
            ReportType.CTR: 15,
            ReportType.STR: 30,
            ReportType.FINCEN: 30,
            ReportType.FATF: 45,
            ReportType.CUSTOM: 60
        }
        
        due_date = int(time.time()) + (due_days.get(report_type, 30) * 86400)
        
        # Create report
        report = RegulatoryReport(
            report_id=str(uuid.uuid4()),
            report_type=report_type,
            reference_number=None,  # Will be assigned when submitted
            alert_ids=alert_ids,
            transaction_ids=transaction_ids,
            submission_timestamp=None,  # Will be set when submitted
            due_date=due_date,
            status="draft",
            submitted_by=None,  # Will be set when submitted
            regulatory_body=regulatory_body,
            report_data=report_data
        )
        
        # Store report
        self.reports[report.report_id] = report
        
        # Update alert statuses
        for alert_id in alert_ids:
            if alert_id in self.alerts:
                self.alerts[alert_id].status = AlertStatus.ESCALATED
                self._trigger_callbacks("alert_updated", self.alerts[alert_id])
        
        # Trigger callback
        self._trigger_callbacks("report_created", report)
        
        logger.info(
            f"Created {report_type.value} report {report.report_id} for {len(alerts)} alerts, "
            f"due on {datetime.datetime.fromtimestamp(due_date).strftime('%Y-%m-%d')}"
        )
        
        return report
    
    def _generate_report_data(self, report_type: ReportType, alerts: List[ComplianceAlert], 
                             transactions: List[Transaction]) -> Dict[str, Any]:
        """
        Generate data for a regulatory report.
        
        Args:
            report_type: Type of report
            alerts: Alerts to include in the report
            transactions: Transactions to include in the report
            
        Returns:
            Report data
        """
        # In a real implementation, this would format the data according to the
        # specific requirements of each report type. For demonstration, we'll
        # create a simplified structure.
        
        # Calculate total value
        total_value_usd = sum(tx.amount_usd for tx in transactions if tx)
        
        # Get unique addresses
        from_addresses = set(tx.from_address for tx in transactions if tx)
        to_addresses = set(tx.to_address for tx in transactions if tx)
        
        # Get risk levels
        risk_levels = [alert.risk_level.value for alert in alerts]
        
        # Generate report data
        report_data = {
            "summary": {
                "total_transactions": len(transactions),
                "total_value_usd": total_value_usd,
                "unique_from_addresses": len(from_addresses),
                "unique_to_addresses": len(to_addresses),
                "highest_risk_level": max(risk_levels, key=lambda x: ["negligible", "low", "medium", "high", "critical"].index(x)),
                "alert_types": list(set(alert.rule_triggered.value for alert in alerts))
            },
            "transactions": [
                {
                    "tx_hash": tx.tx_hash,
                    "blockchain": tx.blockchain,
                    "from_address": tx.from_address,
                    "to_address": tx.to_address,
                    "token": tx.token,
                    "amount": tx.amount,
                    "amount_usd": tx.amount_usd,
                    "timestamp": tx.timestamp,
                    "block_number": tx.block_number
                }
                for tx in transactions if tx
            ],
            "alerts": [
                {
                    "alert_id": alert.alert_id,
                    "rule_triggered": alert.rule_triggered.value,
                    "risk_level": alert.risk_level.value,
                    "description": alert.description,
                    "timestamp": alert.timestamp
                }
                for alert in alerts
            ],
            "narrative": self._generate_report_narrative(report_type, alerts, transactions)
        }
        
        # Add report-specific fields
        if report_type == ReportType.SAR:
            report_data["sar_fields"] = {
                "suspicious_activity_type": self._determine_suspicious_activity_type(alerts),
                "suspicious_activity_date_range": self._determine_date_range(transactions),
                "financial_institution_id": "FI123456789",
                "is_continuing_activity": self._is_continuing_activity(alerts),
                "law_enforcement_contacted": False
            }
        
        elif report_type == ReportType.CTR:
            report_data["ctr_fields"] = {
                "currency_transaction_type": "exchange",
                "transaction_date": datetime.datetime.fromtimestamp(
                    max(tx.timestamp for tx in transactions if tx)
                ).strftime("%Y-%m-%d"),
                "financial_institution_id": "FI123456789",
                "transaction_location": "ONLINE"
            }
        
        return report_data
    
    def _determine_suspicious_activity_type(self, alerts: List[ComplianceAlert]) -> str:
        """Determine the type of suspicious activity based on alerts"""
        # Map rule types to suspicious activity types
        activity_types = {
            MonitoringRule.SANCTIONED_ENTITY: "Sanctions Violation",
            MonitoringRule.STRUCTURING: "Structuring",
            MonitoringRule.UNUSUAL_BEHAVIOR: "Unusual Activity",
            MonitoringRule.PATTERN: "Suspicious Pattern",
            MonitoringRule.HIGH_RISK_CATEGORY: "High-Risk Activity"
        }
        
        # Count occurrences of each activity type
        type_counts = {}
        for alert in alerts:
            activity_type = activity_types.get(alert.rule_triggered, "Other Suspicious Activity")
            type_counts[activity_type] = type_counts.get(activity_type, 0) + 1
        
        # Return the most common activity type
        if type_counts:
            return max(type_counts.items(), key=lambda x: x[1])[0]
        else:
            return "Other Suspicious Activity"
    
    def _determine_date_range(self, transactions: List[Transaction]) -> Dict[str, str]:
        """Determine the date range of suspicious activity"""
        if not transactions:
            return {"start_date": "Unknown", "end_date": "Unknown"}
        
        timestamps = [tx.timestamp for tx in transactions if tx]
        start_date = datetime.datetime.fromtimestamp(min(timestamps)).strftime("%Y-%m-%d")
        end_date = datetime.datetime.fromtimestamp(max(timestamps)).strftime("%Y-%m-%d")
        
        return {"start_date": start_date, "end_date": end_date}
    
    def _is_continuing_activity(self, alerts: List[ComplianceAlert]) -> bool:
        """Determine if this is continuing suspicious activity"""
        # In a real implementation, this would check if there are previous reports
        # for the same addresses or patterns. For demonstration, we'll randomly determine.
        return random.random() < 0.3  # 30% chance of continuing activity
    
    def _generate_report_narrative(self, report_type: ReportType, alerts: List[ComplianceAlert], 
                                  transactions: List[Transaction]) -> str:
        """Generate a narrative for the regulatory report"""
        # In a real implementation, this would generate a detailed narrative
        # based on the specific alerts and transactions. For demonstration,
        # we'll create a simplified narrative.
        
        if not transactions:
            return "No transaction data available for narrative."
        
        # Get basic information
        num_transactions = len(transactions)
        total_value_usd = sum(tx.amount_usd for tx in transactions if tx)
        date_range = self._determine_date_range(transactions)
        activity_type = self._determine_suspicious_activity_type(alerts)
        
        # Generate narrative based on report type
        if report_type == ReportType.SAR:
            narrative = f"SUSPICIOUS ACTIVITY REPORT\n\n"
            narrative += f"This report details suspicious activity observed between {date_range['start_date']} and {date_range['end_date']}. "
            narrative += f"The activity involves {num_transactions} transactions with a total value of ${total_value_usd:.2f}. "
            narrative += f"The primary suspicious activity type is classified as '{activity_type}'.\n\n"
            
            # Add details about each alert
            narrative += "ALERT DETAILS:\n"
            for i, alert in enumerate(alerts, 1):
                narrative += f"{i}. {alert.description}\n\n"
            
            # Add conclusion
            narrative += "CONCLUSION:\n"
            narrative += f"Based on the observed activity, there is reason to believe these transactions may represent "
            narrative += f"an attempt to {activity_type.lower()}. This activity has been flagged for regulatory review "
            narrative += f"in accordance with our compliance procedures."
        
        elif report_type == ReportType.CTR:
            narrative = f"CURRENCY TRANSACTION REPORT\n\n"
            narrative += f"This report details currency transactions exceeding the reporting threshold "
            narrative += f"that occurred on {date_range['end_date']}. "
            narrative += f"The activity involves {num_transactions} transactions with a total value of ${total_value_usd:.2f}.\n\n"
            
            # Add transaction details
            narrative += "TRANSACTION DETAILS:\n"
            for i, tx in enumerate(transactions, 1):
                if tx:
                    narrative += f"{i}. Transaction {tx.tx_hash} on {tx.blockchain}: "
                    narrative += f"{tx.amount} {tx.token} (${tx.amount_usd:.2f}) "
                    narrative += f"from {tx.from_address} to {tx.to_address}\n"
        
        else:
            narrative = f"REGULATORY REPORT\n\n"
            narrative += f"This report details activity observed between {date_range['start_date']} and {date_range['end_date']}. "
            narrative += f"The activity involves {num_transactions} transactions with a total value of ${total_value_usd:.2f}."
        
        return narrative
    
    async def submit_regulatory_report(self, report_id: str, submitted_by: str) -> bool:
        """
        Submit a regulatory report to the appropriate authority.
        
        Args:
            report_id: ID of the report to submit
            submitted_by: Name or ID of the person submitting the report
            
        Returns:
            True if submission was successful, False otherwise
        """
        if report_id not in self.reports:
            logger.error(f"Report {report_id} not found")
            return False
        
        report = self.reports[report_id]
        
        # In a real implementation, this would submit the report to the
        # appropriate regulatory authority via API or file upload.
        # For demonstration, we'll simulate submission.
        
        try:
            # Simulate submission delay
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # Generate reference number
            reference_number = f"{report.report_type.value[:3].upper()}-{int(time.time())}-{random.randint(1000, 9999)}"
            
            # Update report
            report.reference_number = reference_number
            report.submission_timestamp = int(time.time())
            report.status = "submitted"
            report.submitted_by = submitted_by
            
            # Update alert statuses
            for alert_id in report.alert_ids:
                if alert_id in self.alerts:
                    self.alerts[alert_id].status = AlertStatus.REPORTED
                    self._trigger_callbacks("alert_updated", self.alerts[alert_id])
            
            # Trigger callback
            self._trigger_callbacks("report_submitted", report)
            
            logger.info(
                f"Submitted {report.report_type.value} report {report.report_id} "
                f"with reference number {reference_number}"
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error submitting report {report_id}: {e}")
            return False
    
    def update_alert_status(self, alert_id: str, status: AlertStatus, notes: Optional[str] = None) -> bool:
        """
        Update the status of a compliance alert.
        
        Args:
            alert_id: ID of the alert to update
            status: New status
            notes: Optional resolution notes
            
        Returns:
            True if update was successful, False otherwise
        """
        if alert_id not in self.alerts:
            logger.error(f"Alert {alert_id} not found")
            return False
        
        alert = self.alerts[alert_id]
        old_status = alert.status
        
        # Update alert
        alert.status = status
        
        # Add resolution notes and timestamp if status is closed
        if status in [AlertStatus.CLOSED_FALSE_POSITIVE, AlertStatus.CLOSED_RESOLVED]:
            alert.resolution_notes = notes
            alert.resolution_timestamp = int(time.time())
        
        # Trigger callback
        self._trigger_callbacks("alert_updated", alert)
        
        logger.info(f"Updated alert {alert_id} status from {old_status.value} to {status.value}")
        
        return True
    
    def assign_alert(self, alert_id: str, assigned_to: str) -> bool:
        """
        Assign a compliance alert to a user or team.
        
        Args:
            alert_id: ID of the alert to assign
            assigned_to: User or team to assign the alert to
            
        Returns:
            True if assignment was successful, False otherwise
        """
        if alert_id not in self.alerts:
            logger.error(f"Alert {alert_id} not found")
            return False
        
        alert = self.alerts[alert_id]
        old_assignment = alert.assigned_to
        
        # Update alert
        alert.assigned_to = assigned_to
        
        # Update status if needed
        if alert.status == AlertStatus.NEW:
            alert.status = AlertStatus.INVESTIGATING
        
        # Trigger callback
        self._trigger_callbacks("alert_updated", alert)
        
        logger.info(f"Assigned alert {alert_id} from {old_assignment} to {assigned_to}")
        
        return True
    
    def _clean_old_data(self):
        """Clean up old transactions, alerts, and reports"""
        current_time = time.time()
        
        # Get retention periods in seconds
        transaction_retention = self.config["global_settings"]["transaction_retention_days"] * 86400
        alert_retention = self.config["global_settings"]["alert_retention_days"] * 86400
        report_retention = self.config["global_settings"]["report_retention_days"] * 86400
        
        # Clean old transactions
        old_transactions = [
            tx_id for tx_id, tx in self.transactions.items()
            if current_time - tx.timestamp > transaction_retention
        ]
        
        for tx_id in old_transactions:
            del self.transactions[tx_id]
        
        # Clean old alerts (only if closed)
        old_alerts = [
            alert_id for alert_id, alert in self.alerts.items()
            if (current_time - alert.timestamp > alert_retention and
                alert.status in [AlertStatus.CLOSED_FALSE_POSITIVE, AlertStatus.CLOSED_RESOLVED])
        ]
        
        for alert_id in old_alerts:
            del self.alerts[alert_id]
        
        # Clean old reports (only if submitted)
        old_reports = [
            report_id for report_id, report in self.reports.items()
            if (report.submission_timestamp and
                current_time - report.submission_timestamp > report_retention)
        ]
        
        for report_id in old_reports:
            del self.reports[report_id]
        
        if old_transactions or old_alerts or old_reports:
            logger.info(
                f"Cleaned up {len(old_transactions)} old transactions, "
                f"{len(old_alerts)} old alerts, and {len(old_reports)} old reports"
            )
    
    def _trigger_callbacks(self, event_type: str, data: Any):
        """
        Trigger registered callbacks for an event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        for callback in self.callbacks.get(event_type, []):
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in {event_type} callback: {e}")
    
    def register_callback(self, event_type: str, callback: Callable):
        """
        Register a callback for a specific event type.
        
        Args:
            event_type: Type of event to register for
            callback: Callback function
        """
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
            logger.info(f"Registered callback for event type '{event_type}'")
        else:
            logger.error(f"Unknown event type: {event_type}")
    
    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """
        Get a transaction by ID.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Transaction if found, None otherwise
        """
        return self.transactions.get(transaction_id)
    
    def get_alert(self, alert_id: str) -> Optional[ComplianceAlert]:
        """
        Get an alert by ID.
        
        Args:
            alert_id: Alert ID
            
        Returns:
            Alert if found, None otherwise
        """
        return self.alerts.get(alert_id)
    
    def get_report(self, report_id: str) -> Optional[RegulatoryReport]:
        """
        Get a report by ID.
        
        Args:
            report_id: Report ID
            
        Returns:
            Report if found, None otherwise
        """
        return self.reports.get(report_id)
    
    def get_alerts_by_status(self, status: AlertStatus) -> List[ComplianceAlert]:
        """
        Get alerts by status.
        
        Args:
            status: Alert status
            
        Returns:
            List of alerts with the specified status
        """
        return [alert for alert in self.alerts.values() if alert.status == status]
    
    def get_alerts_by_risk_level(self, risk_level: TransactionRiskLevel) -> List[ComplianceAlert]:
        """
        Get alerts by risk level.
        
        Args:
            risk_level: Risk level
            
        Returns:
            List of alerts with the specified risk level
        """
        return [alert for alert in self.alerts.values() if alert.risk_level == risk_level]
    
    def get_reports_by_status(self, status: str) -> List[RegulatoryReport]:
        """
        Get reports by status.
        
        Args:
            status: Report status
            
        Returns:
            List of reports with the specified status
        """
        return [report for report in self.reports.values() if report.status == status]
    
    def get_compliance_statistics(self) -> Dict[str, Any]:
        """
        Get compliance statistics.
        
        Returns:
            Compliance statistics
        """
        # Count transactions by blockchain
        blockchain_counts = {}
        for tx in self.transactions.values():
            blockchain_counts[tx.blockchain] = blockchain_counts.get(tx.blockchain, 0) + 1
        
        # Count alerts by risk level
        risk_level_counts = {}
        for alert in self.alerts.values():
            risk_level_counts[alert.risk_level.value] = risk_level_counts.get(alert.risk_level.value, 0) + 1
        
        # Count alerts by status
        status_counts = {}
        for alert in self.alerts.values():
            status_counts[alert.status.value] = status_counts.get(alert.status.value, 0) + 1
        
        # Count reports by type
        report_type_counts = {}
        for report in self.reports.values():
            report_type_counts[report.report_type.value] = report_type_counts.get(report.report_type.value, 0) + 1
        
        # Calculate alert rate
        total_transactions = len(self.transactions)
        total_alerts = len(self.alerts)
        alert_rate = (total_alerts / total_transactions) * 100 if total_transactions > 0 else 0
        
        return {
            "total_transactions": total_transactions,
            "total_alerts": total_alerts,
            "total_reports": len(self.reports),
            "alert_rate_percentage": alert_rate,
            "blockchain_distribution": blockchain_counts,
            "risk_level_distribution": risk_level_counts,
            "alert_status_distribution": status_counts,
            "report_type_distribution": report_type_counts,
            "high_risk_alerts": len(self.get_alerts_by_risk_level(TransactionRiskLevel.HIGH)) + 
                               len(self.get_alerts_by_risk_level(TransactionRiskLevel.CRITICAL)),
            "pending_reports": len(self.get_reports_by_status("draft")),
            "submitted_reports": len(self.get_reports_by_status("submitted"))
        }
    
    async def shutdown(self):
        """Shutdown the transaction monitoring system"""
        logger.info("Shutting down Transaction Monitoring")
        self.running = False
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        logger.info("Transaction Monitoring shutdown complete")


async def main():
    """Example usage of the Transaction Monitoring system"""
    # Create transaction monitoring system
    monitoring = TransactionMonitoring("monitoring_config.json")
    
    # Register callbacks
    monitoring.register_callback("alert_generated", lambda alert: print(f"Alert generated: {alert.description}"))
    
    # Process a transaction
    transaction = Transaction(
        transaction_id=str(uuid.uuid4()),
        blockchain="ethereum",
        tx_hash=f"0x{hashlib.sha256(b'example').hexdigest()}",
        from_address="${CONTRACT_ADDRESS}",
        to_address="${CONTRACT_ADDRESS}",
        token="ETH",
        amount=5.0,
        amount_usd=15000.0,
        timestamp=int(time.time()),
        block_number=15000000,
        gas_used=21000,
        gas_price=50 * 10**9,  # 50 gwei
        status="confirmed",
        metadata={"gas_limit": 21000, "nonce": 42}
    )
    
    alerts = await monitoring.process_transaction(transaction)
    
    # Create a report if alerts were generated
    if alerts:
        report = await monitoring.create_regulatory_report(ReportType.SAR, alerts)
        
        # Submit the report
        success = await monitoring.submit_regulatory_report(report.report_id, "compliance_officer")
        
        if success:
            print(f"Report submitted with reference number: {report.reference_number}")
    
    # Get compliance statistics
    stats = monitoring.get_compliance_statistics()
    print(f"Compliance statistics: {stats}")
    
    # Run for a while to process transactions
    await asyncio.sleep(10)
    
    # Shutdown
    await monitoring.shutdown()


if __name__ == "__main__":
    asyncio.run(main())