#!/usr/bin/env python3
"""
Slack Alert Manager
Handles sending alerts to Slack channels
"""

import os
import sys
import time
import json
import yaml
import logging
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("slack_alerts.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("slack_alert_manager")

class SlackAlertManager:
    """
    Manages sending alerts to Slack
    - Formats alerts according to templates
    - Handles webhook API calls
    - Supports markdown formatting
    - Manages rate limiting and batching
    """
    
    def __init__(self, config_path="alert_routing_config.yaml"):
        """
        Initialize the Slack Alert Manager
        
        Args:
            config_path: Path to the alert routing configuration file
        """
        self.config_path = config_path
        self.last_sent_time = 0
        self.pending_alerts = []
        
        # Load configuration
        self.load_config()
        
        logger.info("Slack Alert Manager initialized")
    
    def load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
                
            # Extract slack-specific configuration
            self.config = config.get("channel_configs", {}).get("slack", {})
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
        Send an alert to Slack
        
        Args:
            alert: Alert data dictionary
            
        Returns:
            bool: True if alert was sent successfully
        """
        # Check if Slack is enabled
        if not self.config.get("enabled", False):
            logger.info("Slack alerts are disabled")
            return False
            
        # Get Slack configuration
        webhook_url = self.config.get("webhook_url", os.environ.get("SLACK_WEBHOOK_URL", ""))
        
        # Validate configuration
        if not webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False
            
        # Check rate limiting
        if not self._check_rate_limit():
            logger.warning("Slack rate limit exceeded, adding to pending alerts")
            self.pending_alerts.append(alert)
            return False
            
        # Format alert for Slack
        message = self._format_alert(alert)
        
        # Send to Slack
        try:
            response = requests.post(webhook_url, json=message)
            
            if response.status_code != 200:
                logger.error(f"Failed to send alert to Slack: {response.text}")
                return False
                
            # Update last sent time
            self.last_sent_time = time.time()
            
            logger.info(f"Alert sent to Slack: {alert.get('title')}")
            return True
        except Exception as e:
            logger.error(f"Error sending alert to Slack: {e}")
            return False
    
    def _check_rate_limit(self) -> bool:
        """
        Check if rate limit allows sending a Slack message
        
        Returns:
            bool: True if message can be sent
        """
        # Get rate limit from config
        rate_limit = self.global_config.get("rate_limit", 10)  # alerts per minute
        
        # Calculate minimum interval between messages
        min_interval = 60.0 / rate_limit  # seconds
        
        # Check if enough time has passed since last message
        current_time = time.time()
        return (current_time - self.last_sent_time) >= min_interval
    
    def _format_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format an alert for Slack
        
        Args:
            alert: Alert data dictionary
            
        Returns:
            Dict[str, Any]: Formatted Slack message payload
        """
        # Extract alert properties
        sentinel = alert.get("sentinel", "").lower()
        severity = alert.get("severity", "").upper()
        title = alert.get("title", "")
        description = alert.get("description", "")
        timestamp = alert.get("timestamp", time.time())
        
        # Format timestamp
        formatted_time = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        
        # Get template for this sentinel
        template_key = sentinel.split("_")[0] if "_" in sentinel else sentinel
        template = self.config.get("templates", {}).get(template_key, "")
        
        # Use default template if none specified
        if not template:
            template = "*{level}* Alert: {title}\n>{message}\nTime: {timestamp}"
            
        # Format message
        text = template.format(
            level=severity,
            title=title,
            message=description,
            timestamp=formatted_time,
            alert_type=alert.get("type", "")
        )
        
        # Add mentions for critical/emergency alerts
        if severity in self.config.get("mention_users", {}):
            mentions = " ".join(self.config["mention_users"][severity])
            text = f"{mentions} {text}"
            
        # Get emoji for severity if enabled
        emoji = ""
        if self.config.get("emoji_severity", True):
            emoji_map = {
                "LOW": ":information_source:",
                "MEDIUM": ":warning:",
                "HIGH": ":rotating_light:",
                "CRITICAL": ":fire:",
                "EMERGENCY": ":sos:"
            }
            emoji = emoji_map.get(severity, ":warning:")
            
        # Prepare payload
        payload = {
            "text": f"{emoji} {text}",
            "username": self.config.get("username", "Sentinel Alert System"),
            "channel": self.config.get("channel", "#sentinel-alerts")
        }
        
        # Add blocks for better formatting if using modern Slack
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{severity}*: {title}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": description
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Sentinel:* {sentinel} | *Time:* {formatted_time}"
                    }
                ]
            }
        ]
        
        # Add data fields if available
        if "data" in alert and alert["data"]:
            fields = []
            for key, value in alert["data"].items():
                fields.append({
                    "type": "mrkdwn",
                    "text": f"*{key}:* {value}"
                })
                
            # Add fields in groups of 2 (for 2-column layout)
            if fields:
                blocks.append({
                    "type": "section",
                    "fields": fields[:10]  # Limit to 10 fields
                })
                
        # Add divider
        blocks.append({"type": "divider"})
        
        # Add blocks to payload
        payload["blocks"] = blocks
        
        return payload
    
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
        Send a batch of alerts in a single Slack message
        
        Args:
            alerts: List of alert data dictionaries
            
        Returns:
            bool: True if batch was sent successfully
        """
        if not alerts:
            return False
            
        # Check if Slack is enabled
        if not self.config.get("enabled", False):
            logger.info("Slack alerts are disabled")
            return False
            
        # Get Slack configuration
        webhook_url = self.config.get("webhook_url", os.environ.get("SLACK_WEBHOOK_URL", ""))
        
        # Validate configuration
        if not webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False
            
        # Check rate limiting
        if not self._check_rate_limit():
            logger.warning("Slack rate limit exceeded, adding to pending alerts")
            self.pending_alerts.extend(alerts)
            return False
            
        # Get sentinel and severity from first alert
        sentinel = alerts[0].get("sentinel", "").lower()
        severity = alerts[0].get("severity", "").upper()
        
        # Create batch message
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Batch Alert: {len(alerts)} {sentinel} alerts"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Severity:* {severity} | *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            },
            {"type": "divider"}
        ]
        
        # Add each alert (limited to 5 for readability)
        for i, alert in enumerate(alerts[:5]):
            alert_severity = alert.get("severity", "").upper()
            alert_title = alert.get("title", "")
            alert_description = alert.get("description", "")
            alert_timestamp = alert.get("timestamp", time.time())
            formatted_time = datetime.fromtimestamp(alert_timestamp).strftime("%Y-%m-%d %H:%M:%S")
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{alert_severity}:* {alert_title}\n>{alert_description}\n_Time: {formatted_time}_"
                }
            })
            
            # Add divider between alerts
            if i < len(alerts[:5]) - 1:
                blocks.append({"type": "divider"})
                
        # Add note if there are more alerts
        if len(alerts) > 5:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"_...and {len(alerts) - 5} more alerts_"
                    }
                ]
            })
            
        # Prepare payload
        payload = {
            "text": f"Batch Alert: {len(alerts)} {sentinel} alerts",
            "username": self.config.get("username", "Sentinel Alert System"),
            "channel": self.config.get("channel", "#sentinel-alerts"),
            "blocks": blocks
        }
        
        # Send to Slack
        try:
            response = requests.post(webhook_url, json=payload)
            
            if response.status_code != 200:
                logger.error(f"Failed to send batch alert to Slack: {response.text}")
                return False
                
            # Update last sent time
            self.last_sent_time = time.time()
            
            logger.info(f"Batch of {len(alerts)} alerts sent to Slack")
            return True
        except Exception as e:
            logger.error(f"Error sending batch alert to Slack: {e}")
            return False
    
    def shutdown(self):
        """Shutdown the Slack alert manager"""
        logger.info("Shutting down Slack Alert Manager")
        
        # Send any pending alerts
        pending_count = len(self.pending_alerts)
        if pending_count > 0:
            logger.info(f"Sending {pending_count} pending alerts")
            
            # Try to send as batch
            if pending_count > 1:
                self.send_batch(self.pending_alerts)
            else:
                self.send_alert(self.pending_alerts[0])
        
        logger.info("Slack Alert Manager shutdown complete")

if __name__ == "__main__":
    # This block allows for standalone testing of the Slack alert manager
    
    # Initialize manager
    manager = SlackAlertManager(config_path="alert_routing_config.yaml")
    
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