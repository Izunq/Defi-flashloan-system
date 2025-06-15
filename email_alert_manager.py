#!/usr/bin/env python3
"""
Email Alert Manager
Handles sending alerts via email
"""

import os
import sys
import time
import json
import yaml
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("email_alerts.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("email_alert_manager")

class EmailAlertManager:
    """
    Manages sending alerts via email
    - Formats alerts according to templates
    - Handles SMTP connection and sending
    - Supports HTML and plain text formats
    - Manages rate limiting and batching
    """
    
    def __init__(self, config_path="alert_routing_config.yaml"):
        """
        Initialize the Email Alert Manager
        
        Args:
            config_path: Path to the alert routing configuration file
        """
        self.config_path = config_path
        self.last_sent_time = 0
        self.pending_alerts = []
        
        # Load configuration
        self.load_config()
        
        logger.info("Email Alert Manager initialized")
    
    def load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
                
            # Extract email-specific configuration
            self.config = config.get("channel_configs", {}).get("email", {})
            self.global_config = config.get("global_settings", {})
            
            # Set defaults if not specified
            if not self.config:
                self.config = {}
                
            logger.info(f"Loaded configuration from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self.config = {}
            self.global_config = {}
    
    def send_alert(self, alert: Dict[str, Any]) -> bool:
        """
        Send an alert via email
        
        Args:
            alert: Alert data dictionary
            
        Returns:
            bool: True if alert was sent successfully
        """
        # Check if email is enabled
        if not self.config.get("enabled", False):
            logger.info("Email alerts are disabled")
            return False
            
        # Get email configuration
        smtp_server = self.config.get("smtp_server", os.environ.get("SMTP_SERVER", ""))
        smtp_port = self.config.get("smtp_port", 587)
        username = self.config.get("username", os.environ.get("EMAIL_USERNAME", ""))
        password = self.config.get("password", os.environ.get("EMAIL_PASSWORD", ""))
        from_address = self.config.get("from_address", os.environ.get("FROM_EMAIL", ""))
        to_addresses = self.config.get("to_addresses", [])
        
        # Validate configuration
        if not smtp_server or not username or not password or not from_address or not to_addresses:
            logger.warning("Email configuration incomplete")
            return False
            
        # Check rate limiting
        if not self._check_rate_limit():
            logger.warning("Email rate limit exceeded, adding to pending alerts")
            self.pending_alerts.append(alert)
            return False
            
        # Format alert for email
        subject, html_body = self._format_alert(alert)
        
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_address
        msg["To"] = ", ".join(to_addresses)
        
        # Attach HTML part
        msg.attach(MIMEText(html_body, "html"))
        
        # Send email
        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
            server.quit()
            
            # Update last sent time
            self.last_sent_time = time.time()
            
            logger.info(f"Alert sent via email: {alert.get('title')}")
            return True
        except Exception as e:
            logger.error(f"Error sending alert via email: {e}")
            return False
    
    def _check_rate_limit(self) -> bool:
        """
        Check if rate limit allows sending an email
        
        Returns:
            bool: True if email can be sent
        """
        # Get rate limit from config
        rate_limit = self.global_config.get("rate_limit", 10)  # alerts per minute
        
        # Calculate minimum interval between emails
        min_interval = 60.0 / rate_limit  # seconds
        
        # Check if enough time has passed since last email
        current_time = time.time()
        return (current_time - self.last_sent_time) >= min_interval
    
    def _format_alert(self, alert: Dict[str, Any]) -> tuple:
        """
        Format an alert for email
        
        Args:
            alert: Alert data dictionary
            
        Returns:
            tuple: (subject, html_body)
        """
        # Extract alert properties
        sentinel = alert.get("sentinel", "").lower()
        severity = alert.get("severity", "").upper()
        title = alert.get("title", "")
        description = alert.get("description", "")
        timestamp = alert.get("timestamp", time.time())
        
        # Format timestamp
        formatted_time = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        
        # Create email subject
        subject = f"{self.config.get('subject_prefix', '[SENTINEL ALERT]')} {severity}: {title}"
        
        # Create email body using HTML template
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .alert {{ padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .LOW {{ background-color: #d9edf7; }}
                .MEDIUM {{ background-color: #fcf8e3; }}
                .HIGH {{ background-color: #f2dede; }}
                .CRITICAL {{ background-color: #f2dede; border: 2px solid #c9302c; }}
                .EMERGENCY {{ background-color: #f2dede; border: 3px solid #c9302c; color: #c9302c; font-weight: bold; }}
                .header {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
                .details {{ margin-top: 20px; }}
                .timestamp {{ color: #777; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="alert {severity}">
                <div class="header">{severity}: {title}</div>
                <p>{description}</p>
                <div class="timestamp">Time: {formatted_time}</div>
            </div>
            <div class="details">
                <h3>Alert Details:</h3>
                <ul>
                    <li><strong>Sentinel:</strong> {sentinel}</li>
                    <li><strong>Severity:</strong> {severity}</li>
                    <li><strong>Type:</strong> {alert.get('type', 'N/A')}</li>
                </ul>
            </div>
        """
        
        # Add alert data if available
        if "data" in alert and alert["data"]:
            html_body += "<h3>Additional Data:</h3><ul>"
            for key, value in alert["data"].items():
                html_body += f"<li><strong>{key}:</strong> {value}</li>"
            html_body += "</ul>"
            
        html_body += "</body></html>"
        
        return subject, html_body
    
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
    
    def send_batch(self, alerts: List[Dict[str, Any]]) -> bool:
        """
        Send a batch of alerts in a single email
        
        Args:
            alerts: List of alert data dictionaries
            
        Returns:
            bool: True if batch was sent successfully
        """
        if not alerts:
            return False
            
        # Check if email is enabled
        if not self.config.get("enabled", False):
            logger.info("Email alerts are disabled")
            return False
            
        # Get email configuration
        smtp_server = self.config.get("smtp_server", os.environ.get("SMTP_SERVER", ""))
        smtp_port = self.config.get("smtp_port", 587)
        username = self.config.get("username", os.environ.get("EMAIL_USERNAME", ""))
        password = self.config.get("password", os.environ.get("EMAIL_PASSWORD", ""))
        from_address = self.config.get("from_address", os.environ.get("FROM_EMAIL", ""))
        to_addresses = self.config.get("to_addresses", [])
        
        # Validate configuration
        if not smtp_server or not username or not password or not from_address or not to_addresses:
            logger.warning("Email configuration incomplete")
            return False
            
        # Check rate limiting
        if not self._check_rate_limit():
            logger.warning("Email rate limit exceeded, adding to pending alerts")
            self.pending_alerts.extend(alerts)
            return False
            
        # Get sentinel and severity from first alert
        sentinel = alerts[0].get("sentinel", "").lower()
        severity = alerts[0].get("severity", "").upper()
        
        # Create email subject
        subject = f"{self.config.get('subject_prefix', '[SENTINEL ALERT]')} Batch: {len(alerts)} {sentinel} alerts"
        
        # Create email body
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .alert {{ padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .LOW {{ background-color: #d9edf7; }}
                .MEDIUM {{ background-color: #fcf8e3; }}
                .HIGH {{ background-color: #f2dede; }}
                .CRITICAL {{ background-color: #f2dede; border: 2px solid #c9302c; }}
                .EMERGENCY {{ background-color: #f2dede; border: 3px solid #c9302c; color: #c9302c; font-weight: bold; }}
                .header {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
                .details {{ margin-top: 20px; }}
                .timestamp {{ color: #777; font-size: 12px; }}
                .batch-header {{ font-size: 20px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="batch-header">Batch Alert: {len(alerts)} {sentinel} alerts</div>
        """
        
        # Add each alert
        for alert in alerts:
            alert_severity = alert.get("severity", "").upper()
            alert_title = alert.get("title", "")
            alert_description = alert.get("description", "")
            alert_timestamp = alert.get("timestamp", time.time())
            formatted_time = datetime.fromtimestamp(alert_timestamp).strftime("%Y-%m-%d %H:%M:%S")
            
            html_body += f"""
            <div class="alert {alert_severity}">
                <div class="header">{alert_severity}: {alert_title}</div>
                <p>{alert_description}</p>
                <div class="timestamp">Time: {formatted_time}</div>
            </div>
            """
            
        html_body += "</body></html>"
        
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_address
        msg["To"] = ", ".join(to_addresses)
        
        # Attach HTML part
        msg.attach(MIMEText(html_body, "html"))
        
        # Send email
        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
            server.quit()
            
            # Update last sent time
            self.last_sent_time = time.time()
            
            logger.info(f"Batch of {len(alerts)} alerts sent via email")
            return True
        except Exception as e:
            logger.error(f"Error sending batch alert via email: {e}")
            return False
    
    def shutdown(self):
        """Shutdown the email alert manager"""
        logger.info("Shutting down Email Alert Manager")
        
        # Send any pending alerts
        pending_count = len(self.pending_alerts)
        if pending_count > 0:
            logger.info(f"Sending {pending_count} pending alerts")
            
            # Try to send as batch
            if pending_count > 1:
                self.send_batch(self.pending_alerts)
            else:
                self.send_alert(self.pending_alerts[0])
        
        logger.info("Email Alert Manager shutdown complete")

if __name__ == "__main__":
    # This block allows for standalone testing of the email alert manager
    
    # Initialize manager
    manager = EmailAlertManager(config_path="alert_routing_config.yaml")
    
    # Test alert
    test_alert = {
        "sentinel": "oracle_sentinel",
        "timestamp": time.time(),
        "severity": "HIGH",
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