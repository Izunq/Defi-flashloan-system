#!/usr/bin/env python3
"""
SMS Alert Manager
Handles sending alerts via SMS
"""

import os
import sys
import time
import json
import yaml
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sms_alerts.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("sms_alert_manager")

# Try to import Twilio client if available
try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logger.warning("Twilio client not available. SMS will be logged but not sent.")

# Try to import AWS SNS client if available
try:
    import boto3
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
    logger.warning("AWS SDK not available. AWS SNS will not be used.")

class SMSAlertManager:
    """
    Manages sending alerts via SMS
    - Formats alerts to fit SMS character limits
    - Supports multiple SMS providers (Twilio, AWS SNS)
    - Manages rate limiting and priority
    """
    
    def __init__(self, config_path="alert_routing_config.yaml"):
        """
        Initialize the SMS Alert Manager
        
        Args:
            config_path: Path to the alert routing configuration file
        """
        self.config_path = config_path
        self.last_sent_time = 0
        self.pending_alerts = []
        self.twilio_client = None
        self.sns_client = None
        
        # Load configuration
        self.load_config()
        
        # Initialize SMS clients
        self._init_sms_clients()
        
        logger.info("SMS Alert Manager initialized")
    
    def load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
                
            # Extract SMS-specific configuration
            self.config = config.get("channel_configs", {}).get("sms", {})
            self.global_config = config.get("global_settings", {})
            
            # Set defaults if not specified
            if not self.config:
                self.config = {}
                
            logger.info(f"Loaded configuration from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self.config = {}
            self.global_config = {}
    
    def _init_sms_clients(self):
        """Initialize SMS provider clients"""
        service = self.config.get("service", "twilio").lower()
        
        if service == "twilio" and TWILIO_AVAILABLE:
            # Initialize Twilio client
            account_sid = self.config.get("account_sid", os.environ.get("TWILIO_ACCOUNT_SID", ""))
            auth_token = self.config.get("auth_token", os.environ.get("TWILIO_AUTH_TOKEN", ""))
            
            if account_sid and auth_token:
                try:
                    self.twilio_client = TwilioClient(account_sid, auth_token)
                    logger.info("Twilio client initialized")
                except Exception as e:
                    logger.error(f"Failed to initialize Twilio client: {e}")
        
        elif service == "aws_sns" and AWS_AVAILABLE:
            # Initialize AWS SNS client
            try:
                self.sns_client = boto3.client('sns')
                logger.info("AWS SNS client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize AWS SNS client: {e}")
    
    def send_alert(self, alert: Dict[str, Any]) -> bool:
        """
        Send an alert via SMS
        
        Args:
            alert: Alert data dictionary
            
        Returns:
            bool: True if alert was sent successfully
        """
        # Check if SMS is enabled
        if not self.config.get("enabled", False):
            logger.info("SMS alerts are disabled")
            return False
            
        # Get SMS configuration
        service = self.config.get("service", "twilio").lower()
        from_number = self.config.get("from_number", os.environ.get("SMS_FROM_NUMBER", ""))
        to_numbers = self.config.get("to_numbers", [])
        
        # Validate configuration
        if not from_number or not to_numbers:
            logger.warning("SMS configuration incomplete")
            return False
            
        # Check rate limiting
        if not self._check_rate_limit():
            logger.warning("SMS rate limit exceeded, adding to pending alerts")
            self.pending_alerts.append(alert)
            return False
            
        # Format alert for SMS
        message = self._format_alert(alert)
        
        # Send via appropriate service
        if service == "twilio":
            return self._send_via_twilio(message, from_number, to_numbers)
        elif service == "aws_sns":
            return self._send_via_aws_sns(message, to_numbers)
        else:
            logger.warning(f"Unsupported SMS service: {service}")
            return False
    
    def _check_rate_limit(self) -> bool:
        """
        Check if rate limit allows sending an SMS
        
        Returns:
            bool: True if SMS can be sent
        """
        # Get rate limit from config
        rate_limit = self.global_config.get("rate_limit", 5)  # alerts per minute for SMS
        
        # Calculate minimum interval between SMS
        min_interval = 60.0 / rate_limit  # seconds
        
        # Check if enough time has passed since last SMS
        current_time = time.time()
        return (current_time - self.last_sent_time) >= min_interval
    
    def _format_alert(self, alert: Dict[str, Any]) -> str:
        """
        Format an alert for SMS
        
        Args:
            alert: Alert data dictionary
            
        Returns:
            str: Formatted SMS message
        """
        # Extract alert properties
        sentinel = alert.get("sentinel", "").lower()
        severity = alert.get("severity", "").upper()
        title = alert.get("title", "")
        
        # Use abbreviations to keep SMS short
        abbr_severity = self.config.get("abbreviations", {}).get(severity, severity)
        abbr_sentinel = self.config.get("abbreviations", {}).get(sentinel, sentinel)
        
        # Create SMS message (keep it short)
        max_length = self.config.get("max_length", 160)
        message = f"{abbr_severity} {abbr_sentinel}: {title}"
        
        # Add minimal data if space allows
        if "data" in alert and alert["data"]:
            data_str = ""
            for key, value in alert["data"].items():
                # Only add critical data points
                if key in ["asset", "deviation_percent", "estimated_loss"]:
                    data_str += f" {key}={value}"
                    
            # Add data if it fits
            if len(message) + len(data_str) <= max_length:
                message += data_str
        
        # Truncate if too long
        if len(message) > max_length:
            message = message[:max_length-3] + "..."
            
        return message
    
    def _send_via_twilio(self, message: str, from_number: str, to_numbers: List[str]) -> bool:
        """
        Send SMS via Twilio
        
        Args:
            message: SMS message
            from_number: Sender phone number
            to_numbers: List of recipient phone numbers
            
        Returns:
            bool: True if SMS was sent successfully
        """
        if not TWILIO_AVAILABLE or not self.twilio_client:
            logger.warning("Twilio client not available")
            logger.info(f"Would send SMS: {message}")
            return False
            
        success = True
        
        # Send to each recipient
        for to_number in to_numbers:
            try:
                sms = self.twilio_client.messages.create(
                    body=message,
                    from_=from_number,
                    to=to_number
                )
                logger.info(f"SMS sent to {to_number}: {sms.sid}")
            except Exception as e:
                logger.error(f"Error sending SMS to {to_number}: {e}")
                success = False
                
        # Update last sent time
        self.last_sent_time = time.time()
        
        return success
    
    def _send_via_aws_sns(self, message: str, to_numbers: List[str]) -> bool:
        """
        Send SMS via AWS SNS
        
        Args:
            message: SMS message
            to_numbers: List of recipient phone numbers
            
        Returns:
            bool: True if SMS was sent successfully
        """
        if not AWS_AVAILABLE or not self.sns_client:
            logger.warning("AWS SNS client not available")
            logger.info(f"Would send SMS: {message}")
            return False
            
        success = True
        
        # Send to each recipient
        for to_number in to_numbers:
            try:
                response = self.sns_client.publish(
                    PhoneNumber=to_number,
                    Message=message,
                    MessageAttributes={
                        'AWS.SNS.SMS.SenderID': {
                            'DataType': 'String',
                            'StringValue': 'SENTINEL'
                        },
                        'AWS.SNS.SMS.SMSType': {
                            'DataType': 'String',
                            'StringValue': 'Transactional'
                        }
                    }
                )
                logger.info(f"SMS sent to {to_number}: {response['MessageId']}")
            except Exception as e:
                logger.error(f"Error sending SMS to {to_number}: {e}")
                success = False
                
        # Update last sent time
        self.last_sent_time = time.time()
        
        return success
    
    def send_pending_alerts(self):
        """Send any pending alerts if rate limit allows"""
        if not self.pending_alerts:
            return
            
        # Check if rate limit allows sending
        if not self._check_rate_limit():
            return
            
        # Get next alert
        alert = self.pending_alerts.pop(0)
        
        # Send alert
        self.send_alert(alert)
    
    def shutdown(self):
        """Shutdown the SMS alert manager"""
        logger.info("Shutting down SMS Alert Manager")
        
        # Send any pending alerts
        pending_count = len(self.pending_alerts)
        if pending_count > 0:
            logger.info(f"{pending_count} pending alerts will not be sent")
        
        logger.info("SMS Alert Manager shutdown complete")

if __name__ == "__main__":
    # This block allows for standalone testing of the SMS alert manager
    
    # Initialize manager
    manager = SMSAlertManager(config_path="alert_routing_config.yaml")
    
    # Test alert
    test_alert = {
        "sentinel": "oracle_sentinel",
        "timestamp": time.time(),
        "severity": "CRITICAL",
        "title": "Oracle Price Deviation",
        "description": "ETH/USD price deviation of 5% detected",
        "data": {
            "asset": "ETH/USD",
            "expected_price": 2000.00,
            "actual_price": 2100.00,
            "deviation_percent": 5.0
        }
    }
    
    # Send test alert
    manager.send_alert(test_alert)
    
    # Shutdown
    manager.shutdown()