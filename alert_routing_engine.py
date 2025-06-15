#!/usr/bin/env python3
"""
Alert Routing Engine
Routes alerts to appropriate channels based on configuration
"""

import os
import sys
import time
import json
import yaml
import logging
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("alert_routing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("alert_routing_engine")

class AlertRoutingEngine:
    """
    Routes alerts to appropriate channels based on configuration:
    - WebSocket for real-time dashboard updates
    - Slack for team notifications
    - Email for critical alerts
    - SMS for emergency situations
    - Webhook for integration with external systems
    """
    
    def __init__(self, config_path="alert_routing_config.yaml"):
        """
        Initialize the Alert Routing Engine
        
        Args:
            config_path: Path to the alert routing configuration file
        """
        self.config_path = config_path
        self.alert_history = []
        self.last_alert_times = {}  # For throttling
        self.batch_queues = {}  # For batching alerts
        self.batch_timers = {}  # For batch timeouts
        
        # Load configuration
        self.load_config()
        
        # Initialize alert channel managers
        self._init_channel_managers()
        
        logger.info("Alert Routing Engine initialized")
    
    def load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, "r") as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self.config = {}
    
    def _init_channel_managers(self):
        """Initialize alert channel managers"""
        # Initialize WebSocket manager
        self.websocket_manager = None
        if self.config.get("channel_configs", {}).get("websocket", {}).get("enabled", True):
            try:
                from sentinel_websocket_broadcaster import SentinelWebSocketBroadcaster
                websocket_url = self.config.get("channel_configs", {}).get("websocket", {}).get("endpoint", "ws://localhost:8080")
                self.websocket_manager = SentinelWebSocketBroadcaster(
                    websocket_url=websocket_url,
                    reconnect_interval=5
                )
                logger.info("WebSocket manager initialized")
            except ImportError as e:
                logger.error(f"Failed to import SentinelWebSocketBroadcaster: {e}")
        
        # Initialize other channel managers as needed
        # These would typically be imported from separate modules
        self.slack_manager = None
        self.email_manager = None
        self.sms_manager = None
        self.webhook_manager = None
        
        # For now, we'll use direct implementations in this class
        logger.info("Using direct channel implementations")
    
    def route_alert(self, alert: Dict[str, Any]):
        """
        Route an alert to appropriate channels based on configuration
        
        Args:
            alert: Alert data dictionary
        """
        # Extract alert properties
        sentinel = alert.get("sentinel", "").lower()
        severity = alert.get("severity", "").upper()
        alert_type = alert.get("type", "").lower()
        
        # Add timestamp if not present
        if "timestamp" not in alert:
            alert["timestamp"] = time.time()
        
        # Add unique ID if not present
        if "id" not in alert:
            alert["id"] = f"{sentinel}_{int(alert['timestamp'])}_{hash(str(alert))}"
        
        # Check for duplicate alerts
        if self._is_duplicate_alert(alert):
            logger.info(f"Skipping duplicate alert: {alert.get('title')}")
            return
        
        # Add to alert history
        self.alert_history.append(alert)
        
        # Determine routing based on configuration
        channels = self._get_channels_for_alert(alert)
        
        # Check if alert should be batched
        if self._should_batch_alert(alert, channels):
            self._add_to_batch_queue(alert, channels)
            return
        
        # Route to each channel
        for channel in channels:
            if self._should_throttle_alert(alert, channel):
                logger.info(f"Throttling alert to {channel}: {alert.get('title')}")
                continue
                
            self._route_to_channel(alert, channel)
            
        # Check if emergency contacts should be notified
        if self._should_notify_emergency_contacts(alert):
            self._notify_emergency_contacts(alert)
            
        # Check if contract action should be triggered
        if self._should_trigger_contract_action(alert):
            self._trigger_contract_action(alert)
    
    def _is_duplicate_alert(self, alert: Dict[str, Any]) -> bool:
        """
        Check if an alert is a duplicate within the deduplication window
        
        Args:
            alert: Alert data dictionary
            
        Returns:
            bool: True if alert is a duplicate
        """
        # Get deduplication window from config
        window = self.config.get("global_settings", {}).get("deduplication_window", 300)  # Default 5 minutes
        
        # Check recent alerts
        current_time = time.time()
        for recent_alert in reversed(self.alert_history):
            # Skip alerts outside the window
            if current_time - recent_alert.get("timestamp", 0) > window:
                break
                
            # Check if alerts are similar
            if self._are_alerts_similar(alert, recent_alert):
                return True
                
        return False
    
    def _are_alerts_similar(self, alert1: Dict[str, Any], alert2: Dict[str, Any]) -> bool:
        """
        Check if two alerts are similar (for deduplication)
        
        Args:
            alert1: First alert
            alert2: Second alert
            
        Returns:
            bool: True if alerts are similar
        """
        # Check key fields
        if alert1.get("sentinel") != alert2.get("sentinel"):
            return False
            
        if alert1.get("title") != alert2.get("title"):
            return False
            
        # For data fields, do a simple comparison of keys that exist in both
        data1 = alert1.get("data", {})
        data2 = alert2.get("data", {})
        
        common_keys = set(data1.keys()) & set(data2.keys())
        for key in common_keys:
            if data1[key] != data2[key]:
                return False
                
        return True
    
    def _get_channels_for_alert(self, alert: Dict[str, Any]) -> List[str]:
        """
        Determine which channels an alert should be routed to
        
        Args:
            alert: Alert data dictionary
            
        Returns:
            List[str]: List of channel names
        """
        sentinel = alert.get("sentinel", "").lower()
        severity = alert.get("severity", "").upper()
        alert_type = alert.get("type", "").lower()
        
        channels = []
        
        # Check for alert type specific routing
        if alert_type and alert_type in self.config.get("alert_type_routing", {}):
            type_config = self.config["alert_type_routing"][alert_type]
            
            # Check if severity meets minimum level
            min_level = type_config.get("min_level", "LOW").upper()
            if self._severity_meets_threshold(severity, min_level):
                # Use override channels if specified
                if "override_channels" in type_config:
                    return type_config["override_channels"]
        
        # Get channels from routing rules
        if sentinel in self.config.get("routing_rules", {}):
            if severity in self.config["routing_rules"][sentinel]:
                channels = self.config["routing_rules"][sentinel][severity].get("channels", [])
                
                # Handle special "all_channels" value
                if "all_channels" in channels:
                    return ["websocket", "slack", "email", "sms", "webhook"]
        
        # Default to websocket only if no channels specified
        if not channels:
            channels = ["websocket"]
            
        return channels
    
    def _severity_meets_threshold(self, severity: str, threshold: str) -> bool:
        """
        Check if a severity level meets or exceeds a threshold
        
        Args:
            severity: Alert severity
            threshold: Severity threshold
            
        Returns:
            bool: True if severity meets or exceeds threshold
        """
        severity_levels = {
            "LOW": 1,
            "MEDIUM": 2,
            "HIGH": 3,
            "CRITICAL": 4,
            "EMERGENCY": 5
        }
        
        return severity_levels.get(severity, 0) >= severity_levels.get(threshold, 0)
    
    def _should_throttle_alert(self, alert: Dict[str, Any], channel: str) -> bool:
        """
        Check if an alert should be throttled for a specific channel
        
        Args:
            alert: Alert data dictionary
            channel: Channel name
            
        Returns:
            bool: True if alert should be throttled
        """
        sentinel = alert.get("sentinel", "").lower()
        severity = alert.get("severity", "").upper()
        alert_type = alert.get("type", "").lower()
        
        # Get throttle time from config
        throttle = 0
        
        # Check for alert type specific throttle
        if alert_type and alert_type in self.config.get("alert_type_routing", {}):
            type_config = self.config["alert_type_routing"][alert_type]
            if "throttle_override" in type_config:
                throttle = type_config["throttle_override"]
        
        # If no type-specific throttle, check sentinel+severity throttle
        if throttle == 0 and sentinel in self.config.get("routing_rules", {}):
            if severity in self.config["routing_rules"][sentinel]:
                throttle = self.config["routing_rules"][sentinel][severity].get("throttle", 0)
        
        # If throttle is 0, no throttling
        if throttle == 0:
            return False
            
        # Check last alert time for this sentinel+severity+channel
        key = f"{sentinel}_{severity}_{channel}"
        last_time = self.last_alert_times.get(key, 0)
        current_time = time.time()
        
        # Update last alert time
        self.last_alert_times[key] = current_time
        
        # Check if within throttle window
        return (current_time - last_time) < throttle
    
    def _should_batch_alert(self, alert: Dict[str, Any], channels: List[str]) -> bool:
        """
        Check if an alert should be batched
        
        Args:
            alert: Alert data dictionary
            channels: List of channels
            
        Returns:
            bool: True if alert should be batched
        """
        sentinel = alert.get("sentinel", "").lower()
        severity = alert.get("severity", "").upper()
        
        # Check if batching is enabled for this sentinel+severity
        if sentinel in self.config.get("routing_rules", {}):
            if severity in self.config["routing_rules"][sentinel]:
                return self.config["routing_rules"][sentinel][severity].get("batch_enabled", False)
                
        return False
    
    def _add_to_batch_queue(self, alert: Dict[str, Any], channels: List[str]):
        """
        Add an alert to the batch queue
        
        Args:
            alert: Alert data dictionary
            channels: List of channels
        """
        sentinel = alert.get("sentinel", "").lower()
        severity = alert.get("severity", "").upper()
        
        # Create key for batch queue
        key = f"{sentinel}_{severity}"
        
        # Initialize queue if not exists
        if key not in self.batch_queues:
            self.batch_queues[key] = {
                "alerts": [],
                "channels": channels,
                "last_update": time.time()
            }
            
            # Start batch timer
            batch_timeout = self.config.get("global_settings", {}).get("batch_timeout", 30)
            # In a real implementation, this would use a proper timer mechanism
            # For simplicity, we'll just record the time and check it later
            self.batch_timers[key] = time.time() + batch_timeout
        
        # Add alert to queue
        self.batch_queues[key]["alerts"].append(alert)
        self.batch_queues[key]["last_update"] = time.time()
        
        # Check if batch should be sent
        batch_size = self.config.get("global_settings", {}).get("batch_size", 5)
        if len(self.batch_queues[key]["alerts"]) >= batch_size:
            self._send_batch(key)
    
    def _send_batch(self, key: str):
        """
        Send a batch of alerts
        
        Args:
            key: Batch queue key
        """
        if key not in self.batch_queues:
            return
            
        batch = self.batch_queues[key]
        alerts = batch["alerts"]
        channels = batch["channels"]
        
        if not alerts:
            return
            
        # Create batch message
        batch_alert = {
            "type": "batch",
            "timestamp": time.time(),
            "count": len(alerts),
            "sentinel": alerts[0].get("sentinel"),
            "severity": alerts[0].get("severity"),
            "title": f"Batch Alert: {len(alerts)} {alerts[0].get('sentinel')} alerts",
            "alerts": alerts
        }
        
        # Send to each channel
        for channel in channels:
            self._route_to_channel(batch_alert, channel)
            
        # Clear batch queue
        del self.batch_queues[key]
        if key in self.batch_timers:
            del self.batch_timers[key]
    
    def _route_to_channel(self, alert: Dict[str, Any], channel: str):
        """
        Route an alert to a specific channel
        
        Args:
            alert: Alert data dictionary
            channel: Channel name
        """
        try:
            if channel == "websocket":
                self.send_to_websocket(alert)
            elif channel == "slack":
                self.send_to_slack(alert)
            elif channel == "email":
                self.send_to_email(alert)
            elif channel == "sms":
                self.send_to_sms(alert)
            elif channel == "webhook":
                self.send_to_webhook(alert)
            else:
                logger.warning(f"Unknown channel: {channel}")
        except Exception as e:
            logger.error(f"Failed to send alert to {channel}: {e}")
    
    def send_to_websocket(self, alert: Dict[str, Any]):
        """
        Send an alert to WebSocket
        
        Args:
            alert: Alert data dictionary
        """
        if self.websocket_manager:
            self.websocket_manager.broadcast_alert(alert)
            logger.info(f"Alert sent to WebSocket: {alert.get('title')}")
        else:
            logger.warning("WebSocket manager not initialized")
    
    def send_to_slack(self, alert: Dict[str, Any]):
        """
        Send an alert to Slack
        
        Args:
            alert: Alert data dictionary
        """
        # Get Slack configuration
        slack_config = self.config.get("channel_configs", {}).get("slack", {})
        webhook_url = slack_config.get("webhook_url", os.environ.get("SLACK_WEBHOOK_URL", ""))
        
        if not webhook_url:
            logger.warning("Slack webhook URL not configured")
            return
            
        # Format alert for Slack
        sentinel = alert.get("sentinel", "").lower()
        severity = alert.get("severity", "").upper()
        
        # Get template for this sentinel
        template = slack_config.get("templates", {}).get(sentinel.split("_")[0], "")
        if not template:
            template = f"*{sentinel.upper()} Alert* [{severity}]\n*Title:* {{title}}\n*Message:* {{description}}\n*Time:* {{timestamp}}"
            
        # Format message
        timestamp = datetime.fromtimestamp(alert.get("timestamp", time.time())).strftime("%Y-%m-%d %H:%M:%S")
        message = template.format(
            level=severity,
            alert_type=alert.get("type", ""),
            title=alert.get("title", ""),
            message=alert.get("description", ""),
            timestamp=timestamp
        )
        
        # Add mentions for critical/emergency alerts
        if severity in slack_config.get("mention_users", {}):
            mentions = " ".join(slack_config["mention_users"][severity])
            message = f"{mentions} {message}"
            
        # Prepare payload
        payload = {
            "text": message,
            "username": slack_config.get("username", "Sentinel Alert System"),
            "icon_emoji": ":warning:"
        }
        
        # Send to Slack
        try:
            response = requests.post(webhook_url, json=payload)
            if response.status_code != 200:
                logger.error(f"Failed to send alert to Slack: {response.text}")
            else:
                logger.info(f"Alert sent to Slack: {alert.get('title')}")
        except Exception as e:
            logger.error(f"Error sending alert to Slack: {e}")
    
    def send_to_email(self, alert: Dict[str, Any]):
        """
        Send an alert to Email
        
        Args:
            alert: Alert data dictionary
        """
        # Get email configuration
        email_config = self.config.get("channel_configs", {}).get("email", {})
        smtp_server = email_config.get("smtp_server", os.environ.get("SMTP_SERVER", ""))
        smtp_port = email_config.get("smtp_port", 587)
        username = email_config.get("username", os.environ.get("EMAIL_USERNAME", ""))
        password = email_config.get("password", os.environ.get("EMAIL_PASSWORD", ""))
        from_address = email_config.get("from_address", os.environ.get("FROM_EMAIL", ""))
        to_addresses = email_config.get("to_addresses", [])
        
        if not smtp_server or not username or not password or not from_address or not to_addresses:
            logger.warning("Email configuration incomplete")
            return
            
        # Format alert for email
        sentinel = alert.get("sentinel", "").lower()
        severity = alert.get("severity", "").upper()
        
        # Create email subject
        subject = f"{email_config.get('subject_prefix', '[SENTINEL ALERT]')} {severity}: {alert.get('title')}"
        
        # Create email body
        timestamp = datetime.fromtimestamp(alert.get("timestamp", time.time())).strftime("%Y-%m-%d %H:%M:%S")
        
        # Simple HTML template
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
                <div class="header">{severity}: {alert.get('title')}</div>
                <p>{alert.get('description')}</p>
                <div class="timestamp">Time: {timestamp}</div>
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
            logger.info(f"Alert sent to Email: {alert.get('title')}")
        except Exception as e:
            logger.error(f"Error sending alert to Email: {e}")
    
    def send_to_sms(self, alert: Dict[str, Any]):
        """
        Send an alert to SMS
        
        Args:
            alert: Alert data dictionary
        """
        # Get SMS configuration
        sms_config = self.config.get("channel_configs", {}).get("sms", {})
        service = sms_config.get("service", "twilio")
        api_key = sms_config.get("api_key", os.environ.get("SMS_API_KEY", ""))
        from_number = sms_config.get("from_number", os.environ.get("SMS_FROM_NUMBER", ""))
        to_numbers = sms_config.get("to_numbers", [])
        
        if not api_key or not from_number or not to_numbers:
            logger.warning("SMS configuration incomplete")
            return
            
        # Format alert for SMS
        sentinel = alert.get("sentinel", "").lower()
        severity = alert.get("severity", "").upper()
        
        # Use abbreviations to keep SMS short
        abbr_severity = sms_config.get("abbreviations", {}).get(severity, severity)
        abbr_sentinel = sms_config.get("abbreviations", {}).get(sentinel, sentinel)
        
        # Create SMS message (keep it short)
        max_length = sms_config.get("max_length", 160)
        message = f"{abbr_severity} {abbr_sentinel}: {alert.get('title')}"
        
        # Truncate if too long
        if len(message) > max_length:
            message = message[:max_length-3] + "..."
            
        # In a real implementation, this would use the Twilio SDK or another SMS service
        # For this example, we'll just log it
        logger.info(f"Would send SMS to {to_numbers}: {message}")
        logger.info(f"Alert sent to SMS: {alert.get('title')}")
    
    def send_to_webhook(self, alert: Dict[str, Any]):
        """
        Send an alert to Webhook
        
        Args:
            alert: Alert data dictionary
        """
        # Get webhook configuration
        webhook_config = self.config.get("channel_configs", {}).get("webhook", {})
        url = webhook_config.get("url", os.environ.get("WEBHOOK_URL", ""))
        method = webhook_config.get("method", "POST")
        headers = webhook_config.get("headers", {"Content-Type": "application/json"})
        timeout = webhook_config.get("timeout", 10)
        
        if not url:
            logger.warning("Webhook URL not configured")
            return
            
        # Prepare payload
        payload = alert
        if webhook_config.get("include_full_context", True):
            # Add additional context
            payload = dict(alert)
            payload["_meta"] = {
                "sent_at": time.time(),
                "sender": "sentinel_alert_system"
            }
            
        # Send to webhook
        try:
            if method.upper() == "POST":
                response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            elif method.upper() == "PUT":
                response = requests.put(url, json=payload, headers=headers, timeout=timeout)
            else:
                logger.error(f"Unsupported webhook method: {method}")
                return
                
            if response.status_code not in [200, 201, 202, 204]:
                logger.error(f"Failed to send alert to Webhook: {response.text}")
            else:
                logger.info(f"Alert sent to Webhook: {alert.get('title')}")
        except Exception as e:
            logger.error(f"Error sending alert to Webhook: {e}")
    
    def _should_notify_emergency_contacts(self, alert: Dict[str, Any]) -> bool:
        """
        Check if emergency contacts should be notified
        
        Args:
            alert: Alert data dictionary
            
        Returns:
            bool: True if emergency contacts should be notified
        """
        sentinel = alert.get("sentinel", "").lower()
        severity = alert.get("severity", "").upper()
        
        # Check if emergency contacts are enabled for this sentinel+severity
        if sentinel in self.config.get("routing_rules", {}):
            if severity in self.config["routing_rules"][sentinel]:
                return self.config["routing_rules"][sentinel][severity].get("emergency_contacts", False)
                
        return False
    
    def _notify_emergency_contacts(self, alert: Dict[str, Any]):
        """
        Notify emergency contacts
        
        Args:
            alert: Alert data dictionary
        """
        # Get emergency contacts configuration
        contacts_config = self.config.get("emergency_contacts", {})
        if not contacts_config.get("enabled", False):
            logger.warning("Emergency contacts not enabled")
            return
            
        contacts = contacts_config.get("contacts", [])
        if not contacts:
            logger.warning("No emergency contacts configured")
            return
            
        # Get primary contacts (priority 1)
        primary_contacts = [c for c in contacts if c.get("priority", 999) == 1]
        
        # Notify primary contacts
        for contact in primary_contacts:
            self._notify_contact(contact, alert)
            
        # Schedule escalation if needed
        # In a real implementation, this would use a proper scheduler
        # For this example, we'll just log it
        logger.info(f"Would schedule escalation for alert: {alert.get('title')}")
    
    def _notify_contact(self, contact: Dict[str, Any], alert: Dict[str, Any]):
        """
        Notify a specific contact
        
        Args:
            contact: Contact information
            alert: Alert data dictionary
        """
        # Notify via all available methods
        if "email" in contact and contact["email"]:
            # In a real implementation, this would send a personalized email
            logger.info(f"Would send emergency email to {contact['email']}")
            
        if "phone" in contact and contact["phone"]:
            # In a real implementation, this would send an SMS
            logger.info(f"Would send emergency SMS to {contact['phone']}")
            
        if "slack_user" in contact and contact["slack_user"]:
            # In a real implementation, this would send a direct Slack message
            logger.info(f"Would send emergency Slack message to {contact['slack_user']}")
    
    def _should_trigger_contract_action(self, alert: Dict[str, Any]) -> bool:
        """
        Check if a contract action should be triggered
        
        Args:
            alert: Alert data dictionary
            
        Returns:
            bool: True if contract action should be triggered
        """
        sentinel = alert.get("sentinel", "").lower()
        severity = alert.get("severity", "").upper()
        alert_type = alert.get("type", "").lower()
        
        # Check for alert type specific contract action
        if alert_type and alert_type in self.config.get("alert_type_routing", {}):
            type_config = self.config["alert_type_routing"][alert_type]
            if "contract_action" in type_config:
                return True
        
        # Check if contract action is enabled for this sentinel+severity
        if sentinel in self.config.get("routing_rules", {}):
            if severity in self.config["routing_rules"][sentinel]:
                return "contract_action" in self.config["routing_rules"][sentinel][severity]
                
        return False
    
    def _trigger_contract_action(self, alert: Dict[str, Any]):
        """
        Trigger a contract action
        
        Args:
            alert: Alert data dictionary
        """
        sentinel = alert.get("sentinel", "").lower()
        severity = alert.get("severity", "").upper()
        alert_type = alert.get("type", "").lower()
        
        # Determine which action to take
        action_name = None
        
        # Check for alert type specific contract action
        if alert_type and alert_type in self.config.get("alert_type_routing", {}):
            type_config = self.config["alert_type_routing"][alert_type]
            if "contract_action" in type_config:
                action_name = type_config["contract_action"]
        
        # If no type-specific action, check sentinel+severity action
        if not action_name and sentinel in self.config.get("routing_rules", {}):
            if severity in self.config["routing_rules"][sentinel]:
                action_name = self.config["routing_rules"][sentinel][severity].get("contract_action")
        
        if not action_name:
            logger.warning(f"No contract action specified for alert: {alert.get('title')}")
            return
            
        # Get action configuration
        actions_config = self.config.get("contract_actions", {})
        if not actions_config.get("enabled", False):
            logger.warning("Contract actions not enabled")
            return
            
        if action_name not in actions_config.get("actions", {}):
            logger.warning(f"Unknown contract action: {action_name}")
            return
            
        action_config = actions_config["actions"][action_name]
        
        # In a real implementation, this would use the SentinelContractManager
        # For this example, we'll just log it
        logger.info(f"Would execute contract action '{action_name}' for alert: {alert.get('title')}")
        
        # Log details
        contracts = action_config.get("contracts", [])
        function = action_config.get("function", "")
        parameters = action_config.get("parameters", [])
        
        logger.info(f"Contract action details: contracts={contracts}, function={function}, parameters={parameters}")
    
    def check_batch_timeouts(self):
        """Check for batch timeouts and send any timed-out batches"""
        current_time = time.time()
        timed_out_keys = []
        
        for key, timeout in self.batch_timers.items():
            if current_time >= timeout:
                self._send_batch(key)
                timed_out_keys.append(key)
                
        # Remove timed out keys
        for key in timed_out_keys:
            if key in self.batch_timers:
                del self.batch_timers[key]
    
    def cleanup_alert_history(self):
        """Clean up old alerts from history"""
        # Get deduplication window from config
        window = self.config.get("global_settings", {}).get("deduplication_window", 300)  # Default 5 minutes
        
        # Remove alerts older than the window
        current_time = time.time()
        self.alert_history = [
            alert for alert in self.alert_history
            if current_time - alert.get("timestamp", 0) <= window
        ]
    
    def shutdown(self):
        """Shutdown the alert routing engine"""
        logger.info("Shutting down Alert Routing Engine")
        
        # Send any pending batches
        for key in list(self.batch_queues.keys()):
            self._send_batch(key)
            
        # Close WebSocket manager
        if self.websocket_manager:
            try:
                self.websocket_manager.close()
                logger.info("WebSocket manager closed")
            except Exception as e:
                logger.error(f"Error closing WebSocket manager: {e}")
        
        logger.info("Alert Routing Engine shutdown complete")

if __name__ == "__main__":
    # This block allows for standalone testing of the alert routing engine
    
    # Initialize engine
    engine = AlertRoutingEngine(config_path="alert_routing_config.yaml")
    
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
    
    # Route test alert
    engine.route_alert(test_alert)
    
    # Shutdown
    engine.shutdown()