"""
Regulatory Reporting Module

This module implements automated regulatory reporting capabilities for
compliance with various financial regulations across different jurisdictions.

Features:
- Automated report generation
- Multi-jurisdiction support
- Report scheduling and submission
- Audit trail and record keeping
- Data validation and verification
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
import csv
import io
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("regulatory_reporting")

class ReportFormat(Enum):
    """Supported report formats"""
    JSON = "json"
    CSV = "csv"
    XML = "xml"
    PDF = "pdf"
    EXCEL = "excel"
    CUSTOM = "custom"


class ReportFrequency(Enum):
    """Report generation frequencies"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"
    ON_DEMAND = "on_demand"
    EVENT_TRIGGERED = "event_triggered"


class ReportStatus(Enum):
    """Status of regulatory reports"""
    SCHEDULED = "scheduled"
    GENERATING = "generating"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    SUBMITTED = "submitted"
    REJECTED = "rejected"
    FAILED = "failed"
    ARCHIVED = "archived"


class RegulatoryBody(Enum):
    """Supported regulatory bodies"""
    FINCEN = "fincen"  # Financial Crimes Enforcement Network (US)
    SEC = "sec"        # Securities and Exchange Commission (US)
    CFTC = "cftc"      # Commodity Futures Trading Commission (US)
    FINRA = "finra"    # Financial Industry Regulatory Authority (US)
    FCA = "fca"        # Financial Conduct Authority (UK)
    ESMA = "esma"      # European Securities and Markets Authority (EU)
    MAS = "mas"        # Monetary Authority of Singapore
    FATF = "fatf"      # Financial Action Task Force (International)
    AUSTRAC = "austrac"  # Australian Transaction Reports and Analysis Centre
    FINTRAC = "fintrac"  # Financial Transactions and Reports Analysis Centre (Canada)
    CUSTOM = "custom"  # Custom regulatory body


@dataclass
class ReportTemplate:
    """Report template configuration"""
    template_id: str
    name: str
    description: str
    regulatory_body: RegulatoryBody
    report_format: ReportFormat
    schema: Dict[str, Any]
    version: str
    created_at: int
    updated_at: int
    fields: List[Dict[str, Any]]
    validations: List[Dict[str, Any]]
    sample_data: Optional[Dict[str, Any]]


@dataclass
class ReportSchedule:
    """Report scheduling configuration"""
    schedule_id: str
    template_id: str
    frequency: ReportFrequency
    next_run_time: int
    last_run_time: Optional[int]
    parameters: Dict[str, Any]
    enabled: bool
    created_at: int
    updated_at: int
    owner: str
    notification_emails: List[str]


@dataclass
class RegulatoryReport:
    """Regulatory report data"""
    report_id: str
    template_id: str
    schedule_id: Optional[str]
    report_data: Dict[str, Any]
    metadata: Dict[str, Any]
    status: ReportStatus
    created_at: int
    updated_at: int
    submitted_at: Optional[int]
    submission_reference: Optional[str]
    reviewer: Optional[str]
    submitter: Optional[str]
    validation_results: List[Dict[str, Any]]
    file_path: Optional[str]


class RegulatoryReporting:
    """
    Regulatory Reporting system.
    
    This class provides automated regulatory reporting capabilities for
    compliance with various financial regulations across different jurisdictions.
    """
    
    def __init__(self, config_path: str, output_dir: str):
        """
        Initialize the Regulatory Reporting system.
        
        Args:
            config_path: Path to the configuration file
            output_dir: Directory to store generated reports
        """
        self.config = self._load_config(config_path)
        self.output_dir = output_dir
        self.templates: Dict[str, ReportTemplate] = {}
        self.schedules: Dict[str, ReportSchedule] = {}
        self.reports: Dict[str, RegulatoryReport] = {}
        
        self.callbacks: Dict[str, List[Callable]] = {
            "report_scheduled": [],
            "report_generating": [],
            "report_generated": [],
            "report_reviewed": [],
            "report_submitted": [],
            "report_failed": []
        }
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize configurations
        self._initialize_configs()
        
        # Start background tasks
        self.running = True
        self.background_tasks = [
            asyncio.create_task(self._run_scheduled_reports()),
            asyncio.create_task(self._clean_old_reports())
        ]
        
        logger.info(f"Regulatory Reporting initialized with {len(self.templates)} templates")
    
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
                "templates": [],
                "schedules": [],
                "global_settings": {
                    "schedule_check_interval_seconds": 60,
                    "cleanup_interval_seconds": 86400,
                    "report_retention_days": 1825,  # 5 years
                    "default_reviewer": "compliance_officer",
                    "default_submitter": "compliance_manager",
                    "notification_enabled": True,
                    "default_notification_emails": []
                }
            }
    
    def _initialize_configs(self):
        """Initialize configurations from the loaded config"""
        # Initialize report templates
        for template_config in self.config.get("templates", []):
            try:
                template_id = template_config["template_id"]
                
                # Create template object
                template = ReportTemplate(
                    template_id=template_id,
                    name=template_config["name"],
                    description=template_config.get("description", ""),
                    regulatory_body=RegulatoryBody(template_config.get("regulatory_body", "custom")),
                    report_format=ReportFormat(template_config.get("report_format", "json")),
                    schema=template_config.get("schema", {}),
                    version=template_config.get("version", "1.0"),
                    created_at=template_config.get("created_at", int(time.time())),
                    updated_at=template_config.get("updated_at", int(time.time())),
                    fields=template_config.get("fields", []),
                    validations=template_config.get("validations", []),
                    sample_data=template_config.get("sample_data")
                )
                
                self.templates[template_id] = template
                logger.info(f"Initialized report template: {template.name} (ID: {template_id})")
            except Exception as e:
                logger.error(f"Failed to initialize report template: {e}")
        
        # Initialize report schedules
        for schedule_config in self.config.get("schedules", []):
            try:
                schedule_id = schedule_config["schedule_id"]
                
                # Create schedule object
                schedule = ReportSchedule(
                    schedule_id=schedule_id,
                    template_id=schedule_config["template_id"],
                    frequency=ReportFrequency(schedule_config["frequency"]),
                    next_run_time=self._calculate_next_run_time(
                        schedule_config["frequency"],
                        schedule_config.get("parameters", {})
                    ),
                    last_run_time=schedule_config.get("last_run_time"),
                    parameters=schedule_config.get("parameters", {}),
                    enabled=schedule_config.get("enabled", True),
                    created_at=schedule_config.get("created_at", int(time.time())),
                    updated_at=schedule_config.get("updated_at", int(time.time())),
                    owner=schedule_config.get("owner", "system"),
                    notification_emails=schedule_config.get("notification_emails", [])
                )
                
                self.schedules[schedule_id] = schedule
                logger.info(f"Initialized report schedule: {schedule_id} (Template: {schedule.template_id})")
            except Exception as e:
                logger.error(f"Failed to initialize report schedule: {e}")
    
    def _calculate_next_run_time(self, frequency: Union[str, ReportFrequency], parameters: Dict[str, Any]) -> int:
        """
        Calculate the next run time for a report schedule.
        
        Args:
            frequency: Report frequency
            parameters: Schedule parameters
            
        Returns:
            Next run time as Unix timestamp
        """
        if isinstance(frequency, str):
            frequency = ReportFrequency(frequency)
        
        now = datetime.datetime.now()
        
        if frequency == ReportFrequency.DAILY:
            # Get hour and minute from parameters or default to midnight
            hour = parameters.get("hour", 0)
            minute = parameters.get("minute", 0)
            
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += datetime.timedelta(days=1)
        
        elif frequency == ReportFrequency.WEEKLY:
            # Get day of week (0=Monday, 6=Sunday) and time
            day_of_week = parameters.get("day_of_week", 0)  # Default to Monday
            hour = parameters.get("hour", 0)
            minute = parameters.get("minute", 0)
            
            # Calculate days until next occurrence
            days_ahead = day_of_week - now.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + datetime.timedelta(days=days_ahead)
        
        elif frequency == ReportFrequency.MONTHLY:
            # Get day of month and time
            day = parameters.get("day", 1)  # Default to 1st of month
            hour = parameters.get("hour", 0)
            minute = parameters.get("minute", 0)
            
            # Calculate next month
            if day < now.day or (day == now.day and (hour < now.hour or (hour == now.hour and minute <= now.minute))):
                # Target day already happened this month
                if now.month == 12:
                    next_month = 1
                    next_year = now.year + 1
                else:
                    next_month = now.month + 1
                    next_year = now.year
            else:
                next_month = now.month
                next_year = now.year
            
            # Handle month lengths and leap years
            last_day = self._get_last_day_of_month(next_year, next_month)
            day = min(day, last_day)
            
            next_run = datetime.datetime(next_year, next_month, day, hour, minute, 0)
        
        elif frequency == ReportFrequency.QUARTERLY:
            # Get month (1-12), day, and time
            month = parameters.get("month", 1)  # Default to first month of quarter
            day = parameters.get("day", 1)      # Default to 1st of month
            hour = parameters.get("hour", 0)
            minute = parameters.get("minute", 0)
            
            # Calculate current quarter
            current_quarter = (now.month - 1) // 3 + 1
            
            # Calculate target quarter month
            target_quarter_month = (current_quarter - 1) * 3 + month
            if target_quarter_month > 12:
                target_quarter_month -= 12
            
            # Calculate next quarter
            if (target_quarter_month < now.month or 
                (target_quarter_month == now.month and 
                 (day < now.day or (day == now.day and (hour < now.hour or (hour == now.hour and minute <= now.minute)))))):
                # Target already happened this quarter
                target_quarter_month += 3
                if target_quarter_month > 12:
                    target_quarter_month -= 12
                    next_year = now.year + 1
                else:
                    next_year = now.year
            else:
                next_year = now.year
            
            # Handle month lengths and leap years
            last_day = self._get_last_day_of_month(next_year, target_quarter_month)
            day = min(day, last_day)
            
            next_run = datetime.datetime(next_year, target_quarter_month, day, hour, minute, 0)
        
        elif frequency == ReportFrequency.ANNUALLY:
            # Get month, day, and time
            month = parameters.get("month", 1)  # Default to January
            day = parameters.get("day", 1)      # Default to 1st of month
            hour = parameters.get("hour", 0)
            minute = parameters.get("minute", 0)
            
            # Calculate next year
            if (month < now.month or 
                (month == now.month and 
                 (day < now.day or (day == now.day and (hour < now.hour or (hour == now.hour and minute <= now.minute)))))):
                # Target already happened this year
                next_year = now.year + 1
            else:
                next_year = now.year
            
            # Handle month lengths and leap years
            last_day = self._get_last_day_of_month(next_year, month)
            day = min(day, last_day)
            
            next_run = datetime.datetime(next_year, month, day, hour, minute, 0)
        
        elif frequency == ReportFrequency.ON_DEMAND:
            # On-demand reports don't have a next run time
            return 0
        
        elif frequency == ReportFrequency.EVENT_TRIGGERED:
            # Event-triggered reports don't have a next run time
            return 0
        
        else:
            # Default to tomorrow at midnight
            next_run = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
        
        return int(next_run.timestamp())
    
    def _get_last_day_of_month(self, year: int, month: int) -> int:
        """
        Get the last day of a month.
        
        Args:
            year: Year
            month: Month (1-12)
            
        Returns:
            Last day of the month
        """
        if month == 12:
            last_day = 31
        else:
            last_day = (datetime.datetime(year, month + 1, 1) - datetime.timedelta(days=1)).day
        
        return last_day
    
    async def _run_scheduled_reports(self):
        """Background task to run scheduled reports"""
        interval = self.config["global_settings"]["schedule_check_interval_seconds"]
        while self.running:
            try:
                current_time = int(time.time())
                
                # Find schedules that need to run
                for schedule_id, schedule in self.schedules.items():
                    if (schedule.enabled and 
                        schedule.next_run_time > 0 and 
                        current_time >= schedule.next_run_time):
                        
                        # Generate report
                        await self.generate_scheduled_report(schedule_id)
                        
                        # Update schedule
                        schedule.last_run_time = current_time
                        schedule.next_run_time = self._calculate_next_run_time(
                            schedule.frequency,
                            schedule.parameters
                        )
                        schedule.updated_at = current_time
                        
                        logger.info(
                            f"Updated schedule {schedule_id}, next run at "
                            f"{datetime.datetime.fromtimestamp(schedule.next_run_time).strftime('%Y-%m-%d %H:%M:%S')}"
                        )
            
            except Exception as e:
                logger.error(f"Error running scheduled reports: {e}")
            
            await asyncio.sleep(interval)
    
    async def generate_scheduled_report(self, schedule_id: str) -> Optional[str]:
        """
        Generate a report based on a schedule.
        
        Args:
            schedule_id: Schedule ID
            
        Returns:
            Report ID if successful, None otherwise
        """
        if schedule_id not in self.schedules:
            logger.error(f"Schedule {schedule_id} not found")
            return None
        
        schedule = self.schedules[schedule_id]
        
        if schedule.template_id not in self.templates:
            logger.error(f"Template {schedule.template_id} not found for schedule {schedule_id}")
            return None
        
        template = self.templates[schedule.template_id]
        
        logger.info(f"Generating scheduled report for schedule {schedule_id} (Template: {template.name})")
        
        # Trigger callback
        self._trigger_callbacks("report_scheduled", {
            "schedule_id": schedule_id,
            "template_id": template.template_id,
            "template_name": template.name
        })
        
        try:
            # Create report ID
            report_id = str(uuid.uuid4())
            
            # Update status
            self._trigger_callbacks("report_generating", {
                "report_id": report_id,
                "schedule_id": schedule_id,
                "template_id": template.template_id,
                "template_name": template.name
            })
            
            # Gather report data
            report_data = await self._gather_report_data(template, schedule.parameters)
            
            # Generate report file
            file_path = await self._generate_report_file(report_id, template, report_data)
            
            # Validate report data
            validation_results = self._validate_report_data(template, report_data)
            
            # Create report object
            report = RegulatoryReport(
                report_id=report_id,
                template_id=template.template_id,
                schedule_id=schedule_id,
                report_data=report_data,
                metadata={
                    "generated_by": "system",
                    "generation_type": "scheduled",
                    "schedule_frequency": schedule.frequency.value,
                    "template_version": template.version,
                    "regulatory_body": template.regulatory_body.value
                },
                status=ReportStatus.PENDING_REVIEW if validation_results else ReportStatus.APPROVED,
                created_at=int(time.time()),
                updated_at=int(time.time()),
                submitted_at=None,
                submission_reference=None,
                reviewer=None,
                submitter=None,
                validation_results=validation_results,
                file_path=file_path
            )
            
            # Store report
            self.reports[report_id] = report
            
            # Trigger callback
            self._trigger_callbacks("report_generated", report)
            
            logger.info(
                f"Generated report {report_id} for schedule {schedule_id} "
                f"(Status: {report.status.value})"
            )
            
            # Send notifications
            if self.config["global_settings"]["notification_enabled"] and schedule.notification_emails:
                self._send_report_notification(report, schedule.notification_emails)
            
            return report_id
        
        except Exception as e:
            logger.error(f"Error generating report for schedule {schedule_id}: {e}")
            
            # Trigger callback
            self._trigger_callbacks("report_failed", {
                "schedule_id": schedule_id,
                "template_id": template.template_id,
                "error": str(e)
            })
            
            return None
    
    async def generate_on_demand_report(self, template_id: str, parameters: Dict[str, Any]) -> Optional[str]:
        """
        Generate a report on demand.
        
        Args:
            template_id: Template ID
            parameters: Report parameters
            
        Returns:
            Report ID if successful, None otherwise
        """
        if template_id not in self.templates:
            logger.error(f"Template {template_id} not found")
            return None
        
        template = self.templates[template_id]
        
        logger.info(f"Generating on-demand report for template {template.name}")
        
        try:
            # Create report ID
            report_id = str(uuid.uuid4())
            
            # Update status
            self._trigger_callbacks("report_generating", {
                "report_id": report_id,
                "template_id": template.template_id,
                "template_name": template.name
            })
            
            # Gather report data
            report_data = await self._gather_report_data(template, parameters)
            
            # Generate report file
            file_path = await self._generate_report_file(report_id, template, report_data)
            
            # Validate report data
            validation_results = self._validate_report_data(template, report_data)
            
            # Create report object
            report = RegulatoryReport(
                report_id=report_id,
                template_id=template.template_id,
                schedule_id=None,
                report_data=report_data,
                metadata={
                    "generated_by": parameters.get("generated_by", "user"),
                    "generation_type": "on_demand",
                    "template_version": template.version,
                    "regulatory_body": template.regulatory_body.value,
                    "request_parameters": parameters
                },
                status=ReportStatus.PENDING_REVIEW if validation_results else ReportStatus.APPROVED,
                created_at=int(time.time()),
                updated_at=int(time.time()),
                submitted_at=None,
                submission_reference=None,
                reviewer=None,
                submitter=None,
                validation_results=validation_results,
                file_path=file_path
            )
            
            # Store report
            self.reports[report_id] = report
            
            # Trigger callback
            self._trigger_callbacks("report_generated", report)
            
            logger.info(
                f"Generated on-demand report {report_id} for template {template.name} "
                f"(Status: {report.status.value})"
            )
            
            # Send notifications if specified
            if (self.config["global_settings"]["notification_enabled"] and 
                "notification_emails" in parameters and 
                parameters["notification_emails"]):
                self._send_report_notification(report, parameters["notification_emails"])
            
            return report_id
        
        except Exception as e:
            logger.error(f"Error generating on-demand report for template {template_id}: {e}")
            
            # Trigger callback
            self._trigger_callbacks("report_failed", {
                "template_id": template_id,
                "error": str(e)
            })
            
            return None
    
    async def _gather_report_data(self, template: ReportTemplate, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gather data for a report.
        
        Args:
            template: Report template
            parameters: Report parameters
            
        Returns:
            Report data
        """
        # In a real implementation, this would query databases, APIs, etc.
        # to gather the required data based on the template and parameters.
        # For demonstration, we'll generate sample data.
        
        # If template has sample data, use it
        if template.sample_data:
            # Deep copy to avoid modifying the template
            import copy
            report_data = copy.deepcopy(template.sample_data)
            
            # Add timestamp and parameters
            report_data["report_timestamp"] = int(time.time())
            report_data["report_parameters"] = parameters
            
            return report_data
        
        # Generate sample data based on template fields
        report_data = {
            "report_timestamp": int(time.time()),
            "report_parameters": parameters,
            "reporting_entity": {
                "name": "Example Financial Institution",
                "identifier": "EFI123456789",
                "jurisdiction": "US"
            }
        }
        
        # Add data based on regulatory body
        if template.regulatory_body == RegulatoryBody.FINCEN:
            report_data["fincen_specific"] = {
                "filing_type": "initial",
                "bsa_identifier": f"BSA-{hashlib.sha256(str(time.time()).encode()).hexdigest()[:8].upper()}"
            }
        
        elif template.regulatory_body == RegulatoryBody.SEC:
            report_data["sec_specific"] = {
                "cik_number": "0001234567",
                "form_type": "8-K"
            }
        
        # Generate data for each field in the template
        field_data = {}
        for field in template.fields:
            field_name = field["name"]
            field_type = field.get("type", "string")
            
            # Generate value based on field type
            if field_type == "string":
                field_data[field_name] = f"Sample {field_name}"
            elif field_type == "number":
                field_data[field_name] = random.randint(1, 1000)
            elif field_type == "boolean":
                field_data[field_name] = random.choice([True, False])
            elif field_type == "date":
                field_data[field_name] = datetime.datetime.now().strftime("%Y-%m-%d")
            elif field_type == "datetime":
                field_data[field_name] = datetime.datetime.now().isoformat()
            elif field_type == "array":
                field_data[field_name] = [f"Item {i}" for i in range(1, 4)]
            elif field_type == "object":
                field_data[field_name] = {"key": "value"}
            else:
                field_data[field_name] = None
        
        report_data["field_data"] = field_data
        
        # Add some transactions if this is a transaction report
        if "transaction" in template.name.lower():
            report_data["transactions"] = self._generate_sample_transactions(10)
        
        # Add some alerts if this is a suspicious activity report
        if "suspicious" in template.name.lower() or "sar" in template.name.lower():
            report_data["alerts"] = self._generate_sample_alerts(5)
        
        return report_data
    
    def _generate_sample_transactions(self, count: int) -> List[Dict[str, Any]]:
        """Generate sample transactions for reports"""
        transactions = []
        
        for i in range(count):
            tx_time = int(time.time()) - random.randint(0, 86400 * 30)  # Within last 30 days
            
            transaction = {
                "transaction_id": f"TX-{hashlib.sha256(str(i + tx_time).encode()).hexdigest()[:12]}",
                "timestamp": tx_time,
                "date": datetime.datetime.fromtimestamp(tx_time).strftime("%Y-%m-%d"),
                "time": datetime.datetime.fromtimestamp(tx_time).strftime("%H:%M:%S"),
                "amount": round(random.uniform(100, 10000), 2),
                "currency": "USD",
                "type": random.choice(["deposit", "withdrawal", "transfer", "payment"]),
                "status": random.choice(["completed", "pending", "failed"]),
                "source": {
                    "account_id": f"ACCT-{random.randint(10000, 99999)}",
                    "name": f"Customer {random.randint(1, 1000)}",
                    "type": random.choice(["individual", "business"])
                },
                "destination": {
                    "account_id": f"ACCT-{random.randint(10000, 99999)}",
                    "name": f"Recipient {random.randint(1, 1000)}",
                    "type": random.choice(["individual", "business"])
                },
                "reference": f"REF-{random.randint(100000, 999999)}"
            }
            
            transactions.append(transaction)
        
        return transactions
    
    def _generate_sample_alerts(self, count: int) -> List[Dict[str, Any]]:
        """Generate sample alerts for reports"""
        alerts = []
        
        alert_types = [
            "unusual_transaction_volume",
            "large_cash_transaction",
            "structured_transactions",
            "high_risk_jurisdiction",
            "sanctioned_entity",
            "suspicious_pattern"
        ]
        
        for i in range(count):
            alert_time = int(time.time()) - random.randint(0, 86400 * 14)  # Within last 14 days
            alert_type = random.choice(alert_types)
            
            alert = {
                "alert_id": f"ALERT-{hashlib.sha256(str(i + alert_time).encode()).hexdigest()[:12]}",
                "timestamp": alert_time,
                "date": datetime.datetime.fromtimestamp(alert_time).strftime("%Y-%m-%d"),
                "time": datetime.datetime.fromtimestamp(alert_time).strftime("%H:%M:%S"),
                "type": alert_type,
                "severity": random.choice(["low", "medium", "high", "critical"]),
                "status": random.choice(["new", "investigating", "closed"]),
                "description": f"Suspicious activity detected: {alert_type.replace('_', ' ')}",
                "related_transactions": [f"TX-{hashlib.sha256(str(random.randint(1, 1000)).encode()).hexdigest()[:12]}" for _ in range(random.randint(1, 3))],
                "risk_score": random.randint(60, 95)
            }
            
            alerts.append(alert)
        
        return alerts
    
    def _validate_report_data(self, template: ReportTemplate, report_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Validate report data against template validations.
        
        Args:
            template: Report template
            report_data: Report data to validate
            
        Returns:
            List of validation issues (empty if validation passed)
        """
        validation_issues = []
        
        # Apply each validation rule
        for validation in template.validations:
            try:
                validation_type = validation.get("type", "required")
                field_path = validation.get("field", "")
                
                # Skip if no field specified
                if not field_path:
                    continue
                
                # Get field value using path notation (e.g., "reporting_entity.name")
                field_value = self._get_nested_value(report_data, field_path)
                
                # Apply validation based on type
                if validation_type == "required" and (field_value is None or field_value == ""):
                    validation_issues.append({
                        "type": "required",
                        "field": field_path,
                        "message": validation.get("message", f"Field '{field_path}' is required")
                    })
                
                elif validation_type == "type" and field_value is not None:
                    expected_type = validation.get("expected_type", "string")
                    if not self._check_type(field_value, expected_type):
                        validation_issues.append({
                            "type": "type",
                            "field": field_path,
                            "message": validation.get("message", f"Field '{field_path}' must be of type {expected_type}")
                        })
                
                elif validation_type == "pattern" and field_value is not None:
                    pattern = validation.get("pattern", "")
                    if pattern and not re.match(pattern, str(field_value)):
                        validation_issues.append({
                            "type": "pattern",
                            "field": field_path,
                            "message": validation.get("message", f"Field '{field_path}' does not match required pattern")
                        })
                
                elif validation_type == "range" and field_value is not None:
                    min_value = validation.get("min")
                    max_value = validation.get("max")
                    
                    if min_value is not None and field_value < min_value:
                        validation_issues.append({
                            "type": "range",
                            "field": field_path,
                            "message": validation.get("message", f"Field '{field_path}' must be at least {min_value}")
                        })
                    
                    if max_value is not None and field_value > max_value:
                        validation_issues.append({
                            "type": "range",
                            "field": field_path,
                            "message": validation.get("message", f"Field '{field_path}' must be at most {max_value}")
                        })
                
                elif validation_type == "enum" and field_value is not None:
                    allowed_values = validation.get("allowed_values", [])
                    if allowed_values and field_value not in allowed_values:
                        validation_issues.append({
                            "type": "enum",
                            "field": field_path,
                            "message": validation.get("message", f"Field '{field_path}' must be one of: {', '.join(map(str, allowed_values))}")
                        })
                
                elif validation_type == "custom":
                    # Custom validations would be implemented here
                    # For demonstration, we'll just log that a custom validation was encountered
                    logger.debug(f"Custom validation for field '{field_path}' would be applied here")
            
            except Exception as e:
                logger.error(f"Error applying validation rule: {e}")
                validation_issues.append({
                    "type": "error",
                    "field": validation.get("field", "unknown"),
                    "message": f"Validation error: {str(e)}"
                })
        
        return validation_issues
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """
        Get a nested value from a dictionary using dot notation.
        
        Args:
            data: Dictionary to get value from
            path: Path to value using dot notation (e.g., "reporting_entity.name")
            
        Returns:
            Value at the specified path, or None if not found
        """
        if not path:
            return None
        
        parts = path.split(".")
        current = data
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """
        Check if a value is of the expected type.
        
        Args:
            value: Value to check
            expected_type: Expected type
            
        Returns:
            True if value is of the expected type, False otherwise
        """
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "number":
            return isinstance(value, (int, float))
        elif expected_type == "integer":
            return isinstance(value, int)
        elif expected_type == "boolean":
            return isinstance(value, bool)
        elif expected_type == "array":
            return isinstance(value, list)
        elif expected_type == "object":
            return isinstance(value, dict)
        elif expected_type == "null":
            return value is None
        else:
            return True  # Unknown type, assume valid
    
    async def _generate_report_file(self, report_id: str, template: ReportTemplate, report_data: Dict[str, Any]) -> str:
        """
        Generate a report file.
        
        Args:
            report_id: Report ID
            template: Report template
            report_data: Report data
            
        Returns:
            Path to the generated file
        """
        # Create filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{template.name.replace(' ', '_')}_{timestamp}_{report_id}"
        
        # Generate file based on format
        if template.report_format == ReportFormat.JSON:
            file_path = os.path.join(self.output_dir, f"{filename}.json")
            with open(file_path, 'w') as f:
                json.dump(report_data, f, indent=2)
        
        elif template.report_format == ReportFormat.CSV:
            file_path = os.path.join(self.output_dir, f"{filename}.csv")
            
            # Flatten data for CSV
            flattened_data = self._flatten_data(report_data)
            
            # Write CSV
            with open(file_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=flattened_data[0].keys() if flattened_data else [])
                writer.writeheader()
                writer.writerows(flattened_data)
        
        elif template.report_format == ReportFormat.XML:
            # For demonstration, we'll just create a simple XML file
            file_path = os.path.join(self.output_dir, f"{filename}.xml")
            
            # Create simple XML
            xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
            xml_content += f'<report id="{report_id}" template="{template.template_id}" timestamp="{int(time.time())}">\n'
            
            # Add report data as XML
            xml_content += self._dict_to_xml(report_data, indent=2)
            
            xml_content += '</report>'
            
            with open(file_path, 'w') as f:
                f.write(xml_content)
        
        elif template.report_format == ReportFormat.PDF:
            # For demonstration, we'll just create a text file
            # In a real implementation, this would generate a PDF
            file_path = os.path.join(self.output_dir, f"{filename}.txt")
            
            with open(file_path, 'w') as f:
                f.write(f"Report ID: {report_id}\n")
                f.write(f"Template: {template.name}\n")
                f.write(f"Timestamp: {datetime.datetime.now().isoformat()}\n\n")
                f.write("Report Data:\n")
                f.write(json.dumps(report_data, indent=2))
        
        elif template.report_format == ReportFormat.EXCEL:
            # For demonstration, we'll just create a CSV file
            # In a real implementation, this would generate an Excel file
            file_path = os.path.join(self.output_dir, f"{filename}.csv")
            
            # Flatten data for CSV
            flattened_data = self._flatten_data(report_data)
            
            # Write CSV
            with open(file_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=flattened_data[0].keys() if flattened_data else [])
                writer.writeheader()
                writer.writerows(flattened_data)
        
        else:
            # Default to JSON
            file_path = os.path.join(self.output_dir, f"{filename}.json")
            with open(file_path, 'w') as f:
                json.dump(report_data, f, indent=2)
        
        logger.info(f"Generated report file: {file_path}")
        
        return file_path
    
    def _flatten_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Flatten nested data for CSV output.
        
        Args:
            data: Nested data
            
        Returns:
            List of flattened dictionaries
        """
        # Check if data contains a list of records
        for key, value in data.items():
            if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                # Found a list of records, use it as the base
                records = value
                
                # Add top-level metadata to each record
                for record in records:
                    for meta_key, meta_value in data.items():
                        if meta_key != key and not isinstance(meta_value, (dict, list)):
                            record[f"meta_{meta_key}"] = meta_value
                
                return records
        
        # No list of records found, create a single record with flattened data
        flat_record = {}
        
        def flatten_dict(d, prefix=""):
            for k, v in d.items():
                key = f"{prefix}{k}" if prefix else k
                
                if isinstance(v, dict):
                    flatten_dict(v, f"{key}_")
                elif isinstance(v, list):
                    # For lists, join values with commas
                    if all(isinstance(item, (str, int, float, bool)) for item in v):
                        flat_record[key] = ", ".join(str(item) for item in v)
                    else:
                        # For lists of complex objects, just indicate the count
                        flat_record[key] = f"{len(v)} items"
                else:
                    flat_record[key] = v
        
        flatten_dict(data)
        
        return [flat_record]
    
    def _dict_to_xml(self, data: Dict[str, Any], indent: int = 0) -> str:
        """
        Convert a dictionary to XML string.
        
        Args:
            data: Dictionary to convert
            indent: Indentation level
            
        Returns:
            XML string
        """
        xml = ""
        spaces = " " * indent
        
        for key, value in data.items():
            if isinstance(value, dict):
                xml += f"{spaces}<{key}>\n"
                xml += self._dict_to_xml(value, indent + 2)
                xml += f"{spaces}</{key}>\n"
            elif isinstance(value, list):
                if all(isinstance(item, dict) for item in value):
                    xml += f"{spaces}<{key}>\n"
                    for item in value:
                        xml += f"{spaces}  <item>\n"
                        xml += self._dict_to_xml(item, indent + 4)
                        xml += f"{spaces}  </item>\n"
                    xml += f"{spaces}</{key}>\n"
                else:
                    xml += f"{spaces}<{key}>\n"
                    for item in value:
                        xml += f"{spaces}  <item>{self._xml_escape(str(item))}</item>\n"
                    xml += f"{spaces}</{key}>\n"
            else:
                xml += f"{spaces}<{key}>{self._xml_escape(str(value))}</{key}>\n"
        
        return xml
    
    def _xml_escape(self, text: str) -> str:
        """
        Escape special characters for XML.
        
        Args:
            text: Text to escape
            
        Returns:
            Escaped text
        """
        return (text.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace("\"", "&quot;")
                   .replace("'", "&apos;"))
    
    def _send_report_notification(self, report: RegulatoryReport, emails: List[str]):
        """
        Send notification about a generated report.
        
        Args:
            report: Generated report
            emails: List of email addresses to notify
        """
        # In a real implementation, this would send an email notification
        # For demonstration, we'll just log the notification
        
        template_name = self.templates[report.template_id].name if report.template_id in self.templates else "Unknown"
        
        logger.info(
            f"Notification: Report {report.report_id} ({template_name}) generated with status {report.status.value}. "
            f"Would notify: {', '.join(emails)}"
        )
    
    async def review_report(self, report_id: str, approved: bool, reviewer: str, notes: Optional[str] = None) -> bool:
        """
        Review a report.
        
        Args:
            report_id: Report ID
            approved: Whether the report is approved
            reviewer: Name or ID of the reviewer
            notes: Optional review notes
            
        Returns:
            True if review was successful, False otherwise
        """
        if report_id not in self.reports:
            logger.error(f"Report {report_id} not found")
            return False
        
        report = self.reports[report_id]
        
        # Check if report is in a reviewable state
        if report.status != ReportStatus.PENDING_REVIEW:
            logger.error(f"Report {report_id} is not pending review (current status: {report.status.value})")
            return False
        
        # Update report
        report.reviewer = reviewer
        report.updated_at = int(time.time())
        
        if approved:
            report.status = ReportStatus.APPROVED
            logger.info(f"Report {report_id} approved by {reviewer}")
        else:
            report.status = ReportStatus.REJECTED
            logger.info(f"Report {report_id} rejected by {reviewer}")
        
        # Add review notes to metadata
        if notes:
            if "review_notes" not in report.metadata:
                report.metadata["review_notes"] = []
            
            report.metadata["review_notes"].append({
                "reviewer": reviewer,
                "timestamp": int(time.time()),
                "approved": approved,
                "notes": notes
            })
        
        # Trigger callback
        self._trigger_callbacks("report_reviewed", {
            "report_id": report_id,
            "approved": approved,
            "reviewer": reviewer,
            "notes": notes
        })
        
        return True
    
    async def submit_report(self, report_id: str, submitter: str) -> Tuple[bool, Optional[str]]:
        """
        Submit a report to the regulatory authority.
        
        Args:
            report_id: Report ID
            submitter: Name or ID of the submitter
            
        Returns:
            Tuple of (success, submission_reference)
        """
        if report_id not in self.reports:
            logger.error(f"Report {report_id} not found")
            return False, None
        
        report = self.reports[report_id]
        
        # Check if report is in a submittable state
        if report.status != ReportStatus.APPROVED:
            logger.error(f"Report {report_id} is not approved for submission (current status: {report.status.value})")
            return False, None
        
        # In a real implementation, this would submit the report to the
        # appropriate regulatory authority via API or file upload.
        # For demonstration, we'll simulate submission.
        
        try:
            # Get template
            template = self.templates.get(report.template_id)
            if not template:
                logger.error(f"Template {report.template_id} not found for report {report_id}")
                return False, None
            
            # Simulate submission delay
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # Generate submission reference
            regulatory_body = template.regulatory_body.value.upper()
            submission_reference = f"{regulatory_body}-{int(time.time())}-{random.randint(10000, 99999)}"
            
            # Update report
            report.status = ReportStatus.SUBMITTED
            report.submitter = submitter
            report.submitted_at = int(time.time())
            report.submission_reference = submission_reference
            report.updated_at = int(time.time())
            
            # Add submission details to metadata
            report.metadata["submission_details"] = {
                "submitter": submitter,
                "timestamp": report.submitted_at,
                "reference": submission_reference,
                "regulatory_body": regulatory_body
            }
            
            # Trigger callback
            self._trigger_callbacks("report_submitted", {
                "report_id": report_id,
                "submitter": submitter,
                "submission_reference": submission_reference,
                "regulatory_body": regulatory_body
            })
            
            logger.info(
                f"Report {report_id} submitted by {submitter} with reference {submission_reference}"
            )
            
            return True, submission_reference
        
        except Exception as e:
            logger.error(f"Error submitting report {report_id}: {e}")
            
            # Update report status to failed
            report.status = ReportStatus.FAILED
            report.updated_at = int(time.time())
            
            # Add error to metadata
            report.metadata["submission_error"] = {
                "timestamp": int(time.time()),
                "error": str(e)
            }
            
            # Trigger callback
            self._trigger_callbacks("report_failed", {
                "report_id": report_id,
                "error": str(e)
            })
            
            return False, None
    
    async def _clean_old_reports(self):
        """Background task to clean old reports"""
        interval = self.config["global_settings"]["cleanup_interval_seconds"]
        while self.running:
            try:
                current_time = int(time.time())
                retention_days = self.config["global_settings"]["report_retention_days"]
                retention_seconds = retention_days * 86400
                
                # Find reports older than retention period
                old_reports = []
                for report_id, report in self.reports.items():
                    if current_time - report.created_at > retention_seconds:
                        # Only archive reports that are not in active states
                        if report.status not in [ReportStatus.SCHEDULED, ReportStatus.GENERATING, 
                                               ReportStatus.PENDING_REVIEW]:
                            old_reports.append(report_id)
                
                # Archive old reports
                for report_id in old_reports:
                    report = self.reports[report_id]
                    
                    # Update status to archived
                    report.status = ReportStatus.ARCHIVED
                    report.updated_at = current_time
                    
                    logger.info(f"Archived old report {report_id} (created {retention_days} days ago)")
                
                if old_reports:
                    logger.info(f"Archived {len(old_reports)} old reports")
            
            except Exception as e:
                logger.error(f"Error cleaning old reports: {e}")
            
            await asyncio.sleep(interval)
    
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
    
    def get_report(self, report_id: str) -> Optional[RegulatoryReport]:
        """
        Get a report by ID.
        
        Args:
            report_id: Report ID
            
        Returns:
            Report if found, None otherwise
        """
        return self.reports.get(report_id)
    
    def get_template(self, template_id: str) -> Optional[ReportTemplate]:
        """
        Get a template by ID.
        
        Args:
            template_id: Template ID
            
        Returns:
            Template if found, None otherwise
        """
        return self.templates.get(template_id)
    
    def get_schedule(self, schedule_id: str) -> Optional[ReportSchedule]:
        """
        Get a schedule by ID.
        
        Args:
            schedule_id: Schedule ID
            
        Returns:
            Schedule if found, None otherwise
        """
        return self.schedules.get(schedule_id)
    
    def get_reports_by_status(self, status: ReportStatus) -> List[RegulatoryReport]:
        """
        Get reports by status.
        
        Args:
            status: Report status
            
        Returns:
            List of reports with the specified status
        """
        return [report for report in self.reports.values() if report.status == status]
    
    def get_reports_by_template(self, template_id: str) -> List[RegulatoryReport]:
        """
        Get reports by template.
        
        Args:
            template_id: Template ID
            
        Returns:
            List of reports with the specified template
        """
        return [report for report in self.reports.values() if report.template_id == template_id]
    
    def get_reports_by_schedule(self, schedule_id: str) -> List[RegulatoryReport]:
        """
        Get reports by schedule.
        
        Args:
            schedule_id: Schedule ID
            
        Returns:
            List of reports with the specified schedule
        """
        return [report for report in self.reports.values() if report.schedule_id == schedule_id]
    
    def get_reporting_statistics(self) -> Dict[str, Any]:
        """
        Get reporting statistics.
        
        Returns:
            Reporting statistics
        """
        # Count reports by status
        status_counts = {}
        for report in self.reports.values():
            status_counts[report.status.value] = status_counts.get(report.status.value, 0) + 1
        
        # Count reports by template
        template_counts = {}
        for report in self.reports.values():
            template_counts[report.template_id] = template_counts.get(report.template_id, 0) + 1
        
        # Count reports by regulatory body
        body_counts = {}
        for report in self.reports.values():
            template = self.templates.get(report.template_id)
            if template:
                body = template.regulatory_body.value
                body_counts[body] = body_counts.get(body, 0) + 1
        
        # Calculate submission statistics
        submitted_reports = [report for report in self.reports.values() if report.status == ReportStatus.SUBMITTED]
        submission_count = len(submitted_reports)
        
        # Calculate average time from creation to submission
        submission_times = []
        for report in submitted_reports:
            if report.submitted_at and report.created_at:
                submission_times.append(report.submitted_at - report.created_at)
        
        avg_submission_time = sum(submission_times) / len(submission_times) if submission_times else 0
        
        return {
            "total_reports": len(self.reports),
            "total_templates": len(self.templates),
            "total_schedules": len(self.schedules),
            "status_distribution": status_counts,
            "template_distribution": template_counts,
            "regulatory_body_distribution": body_counts,
            "submitted_reports": submission_count,
            "average_submission_time_seconds": avg_submission_time,
            "pending_review": len(self.get_reports_by_status(ReportStatus.PENDING_REVIEW)),
            "failed_reports": len(self.get_reports_by_status(ReportStatus.FAILED))
        }
    
    async def shutdown(self):
        """Shutdown the regulatory reporting system"""
        logger.info("Shutting down Regulatory Reporting")
        self.running = False
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        logger.info("Regulatory Reporting shutdown complete")


async def main():
    """Example usage of the Regulatory Reporting system"""
    # Create output directory
    output_dir = "regulatory_reports"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create regulatory reporting system
    reporting = RegulatoryReporting("reporting_config.json", output_dir)
    
    # Register callbacks
    reporting.register_callback("report_generated", lambda report: print(f"Report generated: {report.report_id}"))
    
    # Generate an on-demand report
    template_id = next(iter(reporting.templates.keys())) if reporting.templates else "template1"
    report_id = await reporting.generate_on_demand_report(template_id, {
        "generated_by": "example_user",
        "date_range": {
            "start_date": "2023-01-01",
            "end_date": "2023-01-31"
        },
        "notification_emails": ["compliance@example.com"]
    })
    
    if report_id:
        # Review the report
        await reporting.review_report(report_id, True, "compliance_officer", "Looks good")
        
        # Submit the report
        success, reference = await reporting.submit_report(report_id, "compliance_manager")
        
        if success:
            print(f"Report submitted with reference: {reference}")
    
    # Get reporting statistics
    stats = reporting.get_reporting_statistics()
    print(f"Reporting statistics: {stats}")
    
    # Run for a while to process scheduled reports
    await asyncio.sleep(10)
    
    # Shutdown
    await reporting.shutdown()


if __name__ == "__main__":
    asyncio.run(main())