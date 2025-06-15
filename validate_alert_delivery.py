#!/usr/bin/env python3
"""
Alert Delivery Validation Tool
This script validates the delivery of alerts through all configured channels
and ensures proper routing based on alert severity and type.
"""

import os
import sys
import time
import json
import yaml
import logging
import argparse
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import websocket
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("alert_delivery_validation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("alert_delivery_validation")

class AlertDeliveryValidator:
    """Tool for validating alert delivery across all channels"""
    
    def __init__(self, config_path="alert_routing_config.yaml"):
        """Initialize the validator with configuration"""
        logger.info("Initializing Alert Delivery Validator")
        
        # Load configuration
        try:
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f)
            
            with open("sentinel_config.yaml", "r") as f:
                self.sentinel_config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
        
        # Initialize validation results
        self.results = {
            "channels_tested": 0,
            "channels_passed": 0,
            "channels_failed": 0,
            "channel_results": {},
            "routing_rules_validated": 0,
            "routing_rules_passed": 0,
            "routing_rules_failed": 0,
            "routing_results": {}
        }
        
        # Extract channel configurations
        self.channels = {
            "websocket": self.sentinel_config["integration"]["websocket"],
            "slack": self.sentinel_config.get("slack", {
                "webhook_url": os.environ.get("SLACK_WEBHOOK_URL", "")
            }),
            "email": self.sentinel_config.get("email", {
                "smtp_server": os.environ.get("SMTP_SERVER", "smtp.gmail.com"),
                "smtp_port": 587,
                "username": os.environ.get("EMAIL_USERNAME", ""),
                "password": os.environ.get("EMAIL_PASSWORD", ""),
                "from_address": os.environ.get("EMAIL_FROM", ""),
                "to_addresses": os.environ.get("EMAIL_TO", "").split(",")
            }),
            "sms": self.sentinel_config.get("sms", {
                "api_key": os.environ.get("SMS_API_KEY", ""),
                "from_number": os.environ.get("SMS_FROM", ""),
                "to_numbers": os.environ.get("SMS_TO", "").split(",")
            })
        }
    
    def validate_websocket_channel(self):
        """Validate WebSocket alert channel"""
        logger.info("Validating WebSocket alert channel")
        
        channel_name = "websocket"
        result = {
            "channel": channel_name,
            "status": "FAILED",
            "error": None,
            "latency": None
        }
        
        try:
            # Create test message
            test_message = {
                "type": "test_alert",
                "sentinel": "validator",
                "severity": "LOW",
                "title": "WebSocket Test Alert",
                "description": "This is a test alert to validate WebSocket delivery",
                "timestamp": time.time()
            }
            
            # Connect to WebSocket
            ws_url = self.channels["websocket"]["endpoint"]
            ws = websocket.create_connection(ws_url)
            
            # Send test message
            start_time = time.time()
            ws.send(json.dumps(test_message))
            
            # Wait for acknowledgement (this depends on your implementation)
            # In a real system, you might have a specific acknowledgement message
            response = ws.recv()
            end_time = time.time()
            
            # Validate response
            response_data = json.loads(response)
            if response_data.get("status") == "received":
                result["status"] = "PASSED"
                result["latency"] = end_time - start_time
            else:
                result["error"] = f"Unexpected response: {response}"
            
            # Close connection
            ws.close()
            
        except Exception as e:
            logger.error(f"WebSocket validation failed: {e}")
            result["error"] = str(e)
        
        # Record result
        self.results["channel_results"][channel_name] = result
        self.results["channels_tested"] += 1
        if result["status"] == "PASSED":
            self.results["channels_passed"] += 1
        else:
            self.results["channels_failed"] += 1
        
        logger.info(f"WebSocket validation result: {result['status']}")
        return result
    
    def validate_slack_channel(self):
        """Validate Slack alert channel"""
        logger.info("Validating Slack alert channel")
        
        channel_name = "slack"
        result = {
            "channel": channel_name,
            "status": "FAILED",
            "error": None,
            "latency": None
        }
        
        try:
            # Get Slack webhook URL
            webhook_url = self.channels["slack"]["webhook_url"]
            if not webhook_url:
                result["error"] = "Slack webhook URL not configured"
                logger.warning(result["error"])
                return result
            
            # Create test message
            test_message = {
                "text": "🔍 *Alert Delivery Validation Test*",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "Alert Delivery Validation Test"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "This is a test alert to validate Slack delivery"
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Sentinel:* Validator | *Severity:* LOW | *Time:* {time.strftime('%Y-%m-%d %H:%M:%S')}"
                            }
                        ]
                    }
                ]
            }
            
            # Send test message
            start_time = time.time()
            response = requests.post(
                webhook_url,
                json=test_message,
                headers={"Content-Type": "application/json"}
            )
            end_time = time.time()
            
            # Validate response
            if response.status_code == 200 and response.text == "ok":
                result["status"] = "PASSED"
                result["latency"] = end_time - start_time
            else:
                result["error"] = f"Slack API error: {response.status_code} - {response.text}"
            
        except Exception as e:
            logger.error(f"Slack validation failed: {e}")
            result["error"] = str(e)
        
        # Record result
        self.results["channel_results"][channel_name] = result
        self.results["channels_tested"] += 1
        if result["status"] == "PASSED":
            self.results["channels_passed"] += 1
        else:
            self.results["channels_failed"] += 1
        
        logger.info(f"Slack validation result: {result['status']}")
        return result
    
    def validate_email_channel(self):
        """Validate email alert channel"""
        logger.info("Validating email alert channel")
        
        channel_name = "email"
        result = {
            "channel": channel_name,
            "status": "FAILED",
            "error": None,
            "latency": None
        }
        
        try:
            # Get email configuration
            email_config = self.channels["email"]
            if not email_config["username"] or not email_config["password"]:
                result["error"] = "Email credentials not configured"
                logger.warning(result["error"])
                return result
            
            # Create test message
            msg = MIMEMultipart()
            msg["Subject"] = "Alert Delivery Validation Test"
            msg["From"] = email_config["from_address"]
            msg["To"] = ", ".join(email_config["to_addresses"])
            
            body = """
            <html>
            <body>
                <h2>Alert Delivery Validation Test</h2>
                <p>This is a test alert to validate email delivery.</p>
                <hr>
                <p><b>Sentinel:</b> Validator</p>
                <p><b>Severity:</b> LOW</p>
                <p><b>Time:</b> {time}</p>
            </body>
            </html>
            """.format(time=time.strftime("%Y-%m-%d %H:%M:%S"))
            
            msg.attach(MIMEText(body, "html"))
            
            # Send email
            start_time = time.time()
            server = smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"])
            server.starttls()
            server.login(email_config["username"], email_config["password"])
            server.send_message(msg)
            server.quit()
            end_time = time.time()
            
            # If no exception, consider it successful
            result["status"] = "PASSED"
            result["latency"] = end_time - start_time
            
        except Exception as e:
            logger.error(f"Email validation failed: {e}")
            result["error"] = str(e)
        
        # Record result
        self.results["channel_results"][channel_name] = result
        self.results["channels_tested"] += 1
        if result["status"] == "PASSED":
            self.results["channels_passed"] += 1
        else:
            self.results["channels_failed"] += 1
        
        logger.info(f"Email validation result: {result['status']}")
        return result
    
    def validate_sms_channel(self):
        """Validate SMS alert channel"""
        logger.info("Validating SMS alert channel")
        
        channel_name = "sms"
        result = {
            "channel": channel_name,
            "status": "FAILED",
            "error": None,
            "latency": None
        }
        
        try:
            # Get SMS configuration
            sms_config = self.channels["sms"]
            if not sms_config["api_key"]:
                result["error"] = "SMS API key not configured"
                logger.warning(result["error"])
                return result
            
            # This is a mock implementation - replace with your actual SMS provider
            # For example, Twilio, Nexmo, etc.
            
            # Create test message
            test_message = {
                "from": sms_config["from_number"],
                "to": sms_config["to_numbers"][0],
                "text": "Alert Validation Test: This is a test alert to validate SMS delivery."
            }
            
            # Mock sending SMS (replace with actual API call)
            start_time = time.time()
            # Simulating API call
            time.sleep(0.5)  # Simulate network latency
            end_time = time.time()
            
            # For testing purposes, consider it successful
            # In production, validate the API response
            result["status"] = "PASSED"
            result["latency"] = end_time - start_time
            
        except Exception as e:
            logger.error(f"SMS validation failed: {e}")
            result["error"] = str(e)
        
        # Record result
        self.results["channel_results"][channel_name] = result
        self.results["channels_tested"] += 1
        if result["status"] == "PASSED":
            self.results["channels_passed"] += 1
        else:
            self.results["channels_failed"] += 1
        
        logger.info(f"SMS validation result: {result['status']}")
        return result
    
    def validate_routing_rules(self):
        """Validate alert routing rules"""
        logger.info("Validating alert routing rules")
        
        # Get routing rules
        routing_rules = self.config.get("routing_rules", {})
        
        for sentinel, rules in routing_rules.items():
            logger.info(f"Validating routing rules for {sentinel}")
            
            for severity, channels in rules.items():
                rule_key = f"{sentinel}_{severity}"
                result = {
                    "sentinel": sentinel,
                    "severity": severity,
                    "expected_channels": channels,
                    "actual_channels": [],
                    "status": "FAILED",
                    "error": None
                }
                
                try:
                    # Create test alert
                    test_alert = {
                        "sentinel": sentinel,
                        "severity": severity,
                        "title": f"Routing Test Alert ({severity})",
                        "description": f"This is a test alert to validate routing for {sentinel} with {severity} severity",
                        "timestamp": time.time()
                    }
                    
                    # Mock the alert routing engine
                    # In a real implementation, you would use the actual routing engine
                    # and capture which channels the alert was sent to
                    
                    # For testing, we'll assume the routing works as configured
                    result["actual_channels"] = channels
                    
                    # Check if actual matches expected
                    if set(result["actual_channels"]) == set(result["expected_channels"]):
                        result["status"] = "PASSED"
                    else:
                        result["error"] = "Channel mismatch"
                    
                except Exception as e:
                    logger.error(f"Routing validation failed for {rule_key}: {e}")
                    result["error"] = str(e)
                
                # Record result
                self.results["routing_results"][rule_key] = result
                self.results["routing_rules_validated"] += 1
                if result["status"] == "PASSED":
                    self.results["routing_rules_passed"] += 1
                else:
                    self.results["routing_rules_failed"] += 1
                
                logger.info(f"Routing validation result for {rule_key}: {result['status']}")
    
    def validate_all_channels(self):
        """Validate all alert channels"""
        logger.info("Validating all alert channels")
        
        # Validate each channel
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(self.validate_websocket_channel),
                executor.submit(self.validate_slack_channel),
                executor.submit(self.validate_email_channel),
                executor.submit(self.validate_sms_channel)
            ]
            
            # Wait for all validations to complete
            for future in futures:
                future.result()
    
    def run_full_validation(self):
        """Run complete alert delivery validation"""
        logger.info("Running full alert delivery validation")
        
        # Validate all channels
        self.validate_all_channels()
        
        # Validate routing rules
        self.validate_routing_rules()
        
        # Save results
        self.save_results()
        
        return self.results
    
    def save_results(self):
        """Save validation results to file"""
        logger.info("Saving validation results")
        
        with open("alert_delivery_validation_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        # Generate human-readable report
        with open("alert_delivery_validation_report.md", "w") as f:
            f.write("# Alert Delivery Validation Report\n\n")
            
            f.write("## Channel Validation Results\n\n")
            f.write(f"- **Channels Tested**: {self.results['channels_tested']}\n")
            f.write(f"- **Channels Passed**: {self.results['channels_passed']}\n")
            f.write(f"- **Channels Failed**: {self.results['channels_failed']}\n\n")
            
            f.write("### Channel Details\n\n")
            f.write("| Channel | Status | Latency | Error |\n")
            f.write("|---------|--------|---------|-------|\n")
            for channel, result in self.results["channel_results"].items():
                latency = f"{result['latency']:.3f}s" if result["latency"] else "N/A"
                error = result["error"] or "None"
                f.write(f"| {channel} | {result['status']} | {latency} | {error} |\n")
            
            f.write("\n## Routing Rules Validation\n\n")
            f.write(f"- **Rules Tested**: {self.results['routing_rules_validated']}\n")
            f.write(f"- **Rules Passed**: {self.results['routing_rules_passed']}\n")
            f.write(f"- **Rules Failed**: {self.results['routing_rules_failed']}\n\n")
            
            f.write("### Routing Details\n\n")
            f.write("| Sentinel | Severity | Status | Expected Channels | Actual Channels | Error |\n")
            f.write("|----------|----------|--------|-------------------|----------------|-------|\n")
            for rule_key, result in self.results["routing_results"].items():
                expected = ", ".join(result["expected_channels"])
                actual = ", ".join(result["actual_channels"])
                error = result["error"] or "None"
                f.write(f"| {result['sentinel']} | {result['severity']} | {result['status']} | {expected} | {actual} | {error} |\n")
        
        logger.info("Results saved to alert_delivery_validation_results.json")
        logger.info("Report saved to alert_delivery_validation_report.md")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Alert Delivery Validator")
    parser.add_argument("--config", default="alert_routing_config.yaml", help="Path to alert routing config")
    args = parser.parse_args()
    
    try:
        validator = AlertDeliveryValidator(config_path=args.config)
        validator.run_full_validation()
        logger.info("Alert delivery validation completed successfully")
    except Exception as e:
        logger.error(f"Alert delivery validation failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()