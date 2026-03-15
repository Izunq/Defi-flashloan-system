"""
White-Label Solutions Module
Provides white-label trading and infrastructure solutions for institutional clients.
"""
import os
import logging
import json
import datetime
import uuid
from typing import Dict, List, Tuple, Any, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WhiteLabelConfig:
    """
    Configuration manager for white-label solutions.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize white-label configuration manager.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config = self._load_config(config_path)
        
        logger.info("Initialized White-Label Configuration Manager")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        Load configuration from file or use defaults.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        default_config = {
            "clients": [],
            "templates": {
                "trading_interface": {
                    "name": "Standard Trading Interface",
                    "features": [
                        "market_data", "order_entry", "position_management",
                        "risk_management", "reporting"
                    ],
                    "customization_options": {
                        "theme": ["light", "dark", "custom"],
                        "layout": ["standard", "advanced", "compact"],
                        "modules": ["all", "trading_only", "analytics_only", "custom"]
                    }
                },
                "mobile_app": {
                    "name": "Mobile Trading App",
                    "features": [
                        "market_data", "order_entry", "alerts",
                        "portfolio_overview", "biometric_authentication"
                    ],
                    "customization_options": {
                        "theme": ["light", "dark", "custom"],
                        "layout": ["standard", "compact"],
                        "modules": ["all", "view_only", "trading_enabled", "custom"]
                    }
                },
                "api_suite": {
                    "name": "Trading API Suite",
                    "features": [
                        "rest_api", "websocket_api", "fix_api",
                        "market_data_api", "order_api", "account_api"
                    ],
                    "customization_options": {
                        "authentication": ["oauth2", "api_key", "certificate"],
                        "rate_limits": ["standard", "premium", "enterprise"],
                        "endpoints": ["all", "market_data_only", "trading_only", "custom"]
                    }
                }
            },
            "pricing_tiers": {
                "standard": {
                    "monthly_fee": 5000,
                    "included_users": 10,
                    "additional_user_fee": 100,
                    "features": ["trading_interface", "mobile_app", "basic_api"]
                },
                "premium": {
                    "monthly_fee": 10000,
                    "included_users": 25,
                    "additional_user_fee": 75,
                    "features": ["trading_interface", "mobile_app", "full_api_suite", "custom_branding"]
                },
                "enterprise": {
                    "monthly_fee": 25000,
                    "included_users": 100,
                    "additional_user_fee": 50,
                    "features": ["trading_interface", "mobile_app", "full_api_suite", "custom_branding", "dedicated_support", "custom_features"]
                }
            },
            "deployment_options": {
                "cloud": {
                    "providers": ["aws", "azure", "gcp"],
                    "regions": ["us-east", "us-west", "eu-central", "ap-southeast", "sa-east"]
                },
                "on_premise": {
                    "supported_os": ["ubuntu-20.04", "rhel-8", "windows-server-2019"],
                    "minimum_requirements": {
                        "cpu_cores": 16,
                        "ram_gb": 64,
                        "storage_gb": 1000
                    }
                },
                "hybrid": {
                    "components": {
                        "cloud": ["market_data", "analytics", "reporting"],
                        "on_premise": ["order_management", "risk_management", "user_data"]
                    }
                }
            }
        }
        
        if not config_path or not os.path.exists(config_path):
            logger.info("Using default white-label configuration")
            return default_config
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Merge with defaults for any missing keys
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            
            logger.info(f"Loaded white-label configuration from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
            return default_config
    
    def save_config(self, config_path: str) -> bool:
        """
        Save current configuration to file.
        
        Args:
            config_path: Path to save configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"Saved white-label configuration to {config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration to {config_path}: {e}")
            return False
    
    def add_client(self, client_info: Dict[str, Any]) -> str:
        """
        Add a new white-label client.
        
        Args:
            client_info: Client information
            
        Returns:
            Client ID
        """
        # Generate client ID if not provided
        if "client_id" not in client_info:
            client_info["client_id"] = str(uuid.uuid4())
        
        # Add creation timestamp
        client_info["created_at"] = datetime.datetime.now().isoformat()
        
        # Add client to configuration
        self.config["clients"].append(client_info)
        
        logger.info(f"Added new white-label client: {client_info['name']} (ID: {client_info['client_id']})")
        return client_info["client_id"]
    
    def update_client(self, client_id: str, client_info: Dict[str, Any]) -> bool:
        """
        Update an existing white-label client.
        
        Args:
            client_id: Client ID
            client_info: Updated client information
            
        Returns:
            True if successful, False otherwise
        """
        # Find client
        for i, client in enumerate(self.config["clients"]):
            if client["client_id"] == client_id:
                # Preserve client ID and creation timestamp
                client_info["client_id"] = client_id
                client_info["created_at"] = client.get("created_at")
                
                # Add update timestamp
                client_info["updated_at"] = datetime.datetime.now().isoformat()
                
                # Update client
                self.config["clients"][i] = client_info
                
                logger.info(f"Updated white-label client: {client_info['name']} (ID: {client_id})")
                return True
        
        logger.warning(f"Client not found: {client_id}")
        return False
    
    def delete_client(self, client_id: str) -> bool:
        """
        Delete a white-label client.
        
        Args:
            client_id: Client ID
            
        Returns:
            True if successful, False otherwise
        """
        # Find client
        for i, client in enumerate(self.config["clients"]):
            if client["client_id"] == client_id:
                # Remove client
                del self.config["clients"][i]
                
                logger.info(f"Deleted white-label client: ID {client_id}")
                return True
        
        logger.warning(f"Client not found: {client_id}")
        return False
    
    def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a white-label client by ID.
        
        Args:
            client_id: Client ID
            
        Returns:
            Client information or None if not found
        """
        # Find client
        for client in self.config["clients"]:
            if client["client_id"] == client_id:
                return client
        
        logger.warning(f"Client not found: {client_id}")
        return None
    
    def get_all_clients(self) -> List[Dict[str, Any]]:
        """
        Get all white-label clients.
        
        Returns:
            List of client information
        """
        return self.config["clients"]
    
    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a white-label template by name.
        
        Args:
            template_name: Template name
            
        Returns:
            Template information or None if not found
        """
        templates = self.config.get("templates", {})
        return templates.get(template_name)
    
    def get_all_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all white-label templates.
        
        Returns:
            Dictionary mapping template names to template information
        """
        return self.config.get("templates", {})
    
    def get_pricing_tier(self, tier_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a pricing tier by name.
        
        Args:
            tier_name: Tier name
            
        Returns:
            Tier information or None if not found
        """
        pricing_tiers = self.config.get("pricing_tiers", {})
        return pricing_tiers.get(tier_name)
    
    def get_all_pricing_tiers(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all pricing tiers.
        
        Returns:
            Dictionary mapping tier names to tier information
        """
        return self.config.get("pricing_tiers", {})
    
    def get_deployment_options(self) -> Dict[str, Dict[str, Any]]:
        """
        Get deployment options.
        
        Returns:
            Dictionary of deployment options
        """
        return self.config.get("deployment_options", {})


class WhiteLabelManager:
    """
    Manager for white-label solutions.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize white-label manager.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config_manager = WhiteLabelConfig(config_path)
        
        logger.info("Initialized White-Label Manager")
    
    def create_client_instance(self, client_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new white-label client instance.
        
        Args:
            client_info: Client information
            
        Returns:
            Client instance information
        """
        # Validate required fields
        required_fields = ["name", "contact_email", "pricing_tier", "template"]
        for field in required_fields:
            if field not in client_info:
                raise ValueError(f"Missing required field: {field}")
        
        # Check if pricing tier exists
        pricing_tier = self.config_manager.get_pricing_tier(client_info["pricing_tier"])
        if not pricing_tier:
            raise ValueError(f"Invalid pricing tier: {client_info['pricing_tier']}")
        
        # Check if template exists
        template = self.config_manager.get_template(client_info["template"])
        if not template:
            raise ValueError(f"Invalid template: {client_info['template']}")
        
        # Add client
        client_id = self.config_manager.add_client(client_info)
        
        # Create client instance
        instance_info = {
            "client_id": client_id,
            "name": client_info["name"],
            "status": "PROVISIONING",
            "created_at": datetime.datetime.now().isoformat(),
            "pricing_tier": client_info["pricing_tier"],
            "template": client_info["template"],
            "customization": client_info.get("customization", {}),
            "deployment": client_info.get("deployment", {"type": "cloud", "region": "us-east"}),
            "access_credentials": {
                "api_key": str(uuid.uuid4()),
                "api_secret": str(uuid.uuid4())
            }
        }
        
        # In a real implementation, this would provision the actual white-label instance
        # This is a placeholder
        
        logger.info(f"Created white-label instance for client: {client_info['name']} (ID: {client_id})")
        
        # Update client status after "provisioning"
        instance_info["status"] = "ACTIVE"
        
        return instance_info
    
    def update_client_instance(self, client_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing white-label client instance.
        
        Args:
            client_id: Client ID
            updates: Updates to apply
            
        Returns:
            Updated client instance information
        """
        # Get client
        client = self.config_manager.get_client(client_id)
        if not client:
            raise ValueError(f"Client not found: {client_id}")
        
        # Apply updates
        for key, value in updates.items():
            if key not in ["client_id", "created_at"]:
                client[key] = value
        
        # Update client
        self.config_manager.update_client(client_id, client)
        
        # In a real implementation, this would update the actual white-label instance
        # This is a placeholder
        
        logger.info(f"Updated white-label instance for client: {client['name']} (ID: {client_id})")
        
        return client
    
    def delete_client_instance(self, client_id: str) -> bool:
        """
        Delete a white-label client instance.
        
        Args:
            client_id: Client ID
            
        Returns:
            True if successful, False otherwise
        """
        # Get client
        client = self.config_manager.get_client(client_id)
        if not client:
            raise ValueError(f"Client not found: {client_id}")
        
        # In a real implementation, this would deprovision the actual white-label instance
        # This is a placeholder
        
        # Delete client
        result = self.config_manager.delete_client(client_id)
        
        if result:
            logger.info(f"Deleted white-label instance for client: {client['name']} (ID: {client_id})")
        
        return result
    
    def get_client_instance(self, client_id: str) -> Dict[str, Any]:
        """
        Get a white-label client instance.
        
        Args:
            client_id: Client ID
            
        Returns:
            Client instance information
        """
        # Get client
        client = self.config_manager.get_client(client_id)
        if not client:
            raise ValueError(f"Client not found: {client_id}")
        
        return client
    
    def get_all_client_instances(self) -> List[Dict[str, Any]]:
        """
        Get all white-label client instances.
        
        Returns:
            List of client instance information
        """
        return self.config_manager.get_all_clients()
    
    def generate_client_report(self, client_id: str) -> Dict[str, Any]:
        """
        Generate a report for a white-label client.
        
        Args:
            client_id: Client ID
            
        Returns:
            Client report
        """
        # Get client
        client = self.config_manager.get_client(client_id)
        if not client:
            raise ValueError(f"Client not found: {client_id}")
        
        # Get pricing tier
        pricing_tier = self.config_manager.get_pricing_tier(client["pricing_tier"])
        
        # Calculate billing
        monthly_fee = pricing_tier["monthly_fee"]
        included_users = pricing_tier["included_users"]
        additional_user_fee = pricing_tier["additional_user_fee"]
        
        actual_users = client.get("active_users", 0)
        additional_users = max(0, actual_users - included_users)
        additional_user_cost = additional_users * additional_user_fee
        
        total_monthly_cost = monthly_fee + additional_user_cost
        
        # Generate report
        report = {
            "client_id": client_id,
            "name": client["name"],
            "status": client.get("status", "UNKNOWN"),
            "created_at": client["created_at"],
            "pricing_tier": client["pricing_tier"],
            "template": client["template"],
            "active_users": actual_users,
            "billing": {
                "monthly_fee": monthly_fee,
                "included_users": included_users,
                "additional_users": additional_users,
                "additional_user_fee": additional_user_fee,
                "additional_user_cost": additional_user_cost,
                "total_monthly_cost": total_monthly_cost
            },
            "features": pricing_tier["features"],
            "usage_statistics": {
                "api_calls_last_30_days": client.get("api_calls_last_30_days", 0),
                "trades_last_30_days": client.get("trades_last_30_days", 0),
                "logins_last_30_days": client.get("logins_last_30_days", 0),
                "data_transfer_gb_last_30_days": client.get("data_transfer_gb_last_30_days", 0)
            }
        }
        
        logger.info(f"Generated report for white-label client: {client['name']} (ID: {client_id})")
        return report
    
    def generate_deployment_plan(self, client_id: str) -> Dict[str, Any]:
        """
        Generate a deployment plan for a white-label client.
        
        Args:
            client_id: Client ID
            
        Returns:
            Deployment plan
        """
        # Get client
        client = self.config_manager.get_client(client_id)
        if not client:
            raise ValueError(f"Client not found: {client_id}")
        
        # Get deployment options
        deployment_options = self.config_manager.get_deployment_options()
        
        # Get client deployment preferences
        deployment_prefs = client.get("deployment", {"type": "cloud", "region": "us-east"})
        deployment_type = deployment_prefs.get("type", "cloud")
        
        # Generate deployment plan based on type
        if deployment_type == "cloud":
            region = deployment_prefs.get("region", "us-east")
            provider = deployment_prefs.get("provider", "aws")
            
            plan = {
                "type": "cloud",
                "provider": provider,
                "region": region,
                "components": [
                    {
                        "name": "frontend",
                        "type": "web_application",
                        "resources": {
                            "cpu": 2,
                            "memory_gb": 4,
                            "storage_gb": 20
                        }
                    },
                    {
                        "name": "api_gateway",
                        "type": "api_service",
                        "resources": {
                            "cpu": 2,
                            "memory_gb": 4,
                            "storage_gb": 20
                        }
                    },
                    {
                        "name": "database",
                        "type": "database",
                        "resources": {
                            "cpu": 4,
                            "memory_gb": 16,
                            "storage_gb": 100
                        }
                    },
                    {
                        "name": "trading_engine",
                        "type": "application_service",
                        "resources": {
                            "cpu": 8,
                            "memory_gb": 32,
                            "storage_gb": 50
                        }
                    }
                ],
                "network": {
                    "vpc": f"{client_id}-vpc",
                    "subnets": [
                        f"{client_id}-public-subnet",
                        f"{client_id}-private-subnet"
                    ],
                    "security_groups": [
                        f"{client_id}-web-sg",
                        f"{client_id}-api-sg",
                        f"{client_id}-db-sg"
                    ]
                },
                "estimated_cost": {
                    "monthly": 2500,
                    "breakdown": {
                        "compute": 1500,
                        "storage": 500,
                        "network": 300,
                        "other": 200
                    }
                }
            }
        elif deployment_type == "on_premise":
            os_type = deployment_prefs.get("os", "ubuntu-20.04")
            
            plan = {
                "type": "on_premise",
                "os": os_type,
                "components": [
                    {
                        "name": "frontend",
                        "type": "web_application",
                        "resources": {
                            "cpu": 2,
                            "memory_gb": 4,
                            "storage_gb": 20
                        }
                    },
                    {
                        "name": "api_gateway",
                        "type": "api_service",
                        "resources": {
                            "cpu": 2,
                            "memory_gb": 4,
                            "storage_gb": 20
                        }
                    },
                    {
                        "name": "database",
                        "type": "database",
                        "resources": {
                            "cpu": 4,
                            "memory_gb": 16,
                            "storage_gb": 100
                        }
                    },
                    {
                        "name": "trading_engine",
                        "type": "application_service",
                        "resources": {
                            "cpu": 8,
                            "memory_gb": 32,
                            "storage_gb": 50
                        }
                    }
                ],
                "network": {
                    "firewall_rules": [
                        {"port": 80, "source": "0.0.0.0/0", "protocol": "tcp"},
                        {"port": 443, "source": "0.0.0.0/0", "protocol": "tcp"},
                        {"port": 22, "source": "ADMIN_IP", "protocol": "tcp"}
                    ]
                },
                "hardware_requirements": {
                    "cpu_cores": 16,
                    "ram_gb": 64,
                    "storage_gb": 1000,
                    "network_bandwidth_mbps": 1000
                }
            }
        elif deployment_type == "hybrid":
            cloud_provider = deployment_prefs.get("cloud_provider", "aws")
            cloud_region = deployment_prefs.get("cloud_region", "us-east")
            on_premise_os = deployment_prefs.get("on_premise_os", "ubuntu-20.04")
            
            plan = {
                "type": "hybrid",
                "cloud": {
                    "provider": cloud_provider,
                    "region": cloud_region,
                    "components": [
                        {
                            "name": "frontend",
                            "type": "web_application",
                            "resources": {
                                "cpu": 2,
                                "memory_gb": 4,
                                "storage_gb": 20
                            }
                        },
                        {
                            "name": "api_gateway",
                            "type": "api_service",
                            "resources": {
                                "cpu": 2,
                                "memory_gb": 4,
                                "storage_gb": 20
                            }
                        }
                    ]
                },
                "on_premise": {
                    "os": on_premise_os,
                    "components": [
                        {
                            "name": "database",
                            "type": "database",
                            "resources": {
                                "cpu": 4,
                                "memory_gb": 16,
                                "storage_gb": 100
                            }
                        },
                        {
                            "name": "trading_engine",
                            "type": "application_service",
                            "resources": {
                                "cpu": 8,
                                "memory_gb": 32,
                                "storage_gb": 50
                            }
                        }
                    ]
                },
                "connectivity": {
                    "type": "vpn",
                    "bandwidth_mbps": 1000,
                    "encryption": "aes-256-gcm"
                },
                "estimated_cost": {
                    "monthly": 1500,
                    "breakdown": {
                        "cloud_compute": 800,
                        "cloud_storage": 300,
                        "cloud_network": 200,
                        "connectivity": 200
                    }
                }
            }
        else:
            raise ValueError(f"Invalid deployment type: {deployment_type}")
        
        logger.info(f"Generated deployment plan for white-label client: {client['name']} (ID: {client_id})")
        return plan
    
    def generate_customization_options(self, template_name: str) -> Dict[str, Any]:
        """
        Generate customization options for a template.
        
        Args:
            template_name: Template name
            
        Returns:
            Customization options
        """
        # Get template
        template = self.config_manager.get_template(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")
        
        # Get customization options from template
        customization_options = template.get("customization_options", {})
        
        # Add additional options
        customization_options["branding"] = {
            "logo": {
                "type": "image",
                "formats": ["png", "svg"],
                "dimensions": "200x50"
            },
            "colors": {
                "primary": {
                    "type": "color",
                    "default": "#1E88E5"
                },
                "secondary": {
                    "type": "color",
                    "default": "#26A69A"
                },
                "accent": {
                    "type": "color",
                    "default": "#FF8F00"
                },
                "background": {
                    "type": "color",
                    "default": "#FFFFFF"
                },
                "text": {
                    "type": "color",
                    "default": "#212121"
                }
            },
            "fonts": {
                "heading": {
                    "type": "font",
                    "options": ["Roboto", "Open Sans", "Montserrat", "Custom"]
                },
                "body": {
                    "type": "font",
                    "options": ["Roboto", "Open Sans", "Lato", "Custom"]
                }
            }
        }
        
        customization_options["localization"] = {
            "languages": {
                "type": "multi_select",
                "options": ["en", "es", "fr", "de", "zh", "ja", "ru"],
                "default": ["en"]
            },
            "date_format": {
                "type": "select",
                "options": ["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"],
                "default": "MM/DD/YYYY"
            },
            "time_format": {
                "type": "select",
                "options": ["12h", "24h"],
                "default": "12h"
            },
            "timezone": {
                "type": "select",
                "options": ["UTC", "America/New_York", "Europe/London", "Asia/Tokyo"],
                "default": "UTC"
            }
        }
        
        logger.info(f"Generated customization options for template: {template_name}")
        return customization_options
    
    def estimate_costs(self, client_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate costs for a white-label client configuration.
        
        Args:
            client_config: Client configuration
            
        Returns:
            Cost estimate
        """
        # Get pricing tier
        pricing_tier_name = client_config.get("pricing_tier", "standard")
        pricing_tier = self.config_manager.get_pricing_tier(pricing_tier_name)
        if not pricing_tier:
            raise ValueError(f"Invalid pricing tier: {pricing_tier_name}")
        
        # Get user count
        user_count = client_config.get("expected_users", pricing_tier["included_users"])
        additional_users = max(0, user_count - pricing_tier["included_users"])
        
        # Calculate base costs
        monthly_fee = pricing_tier["monthly_fee"]
        additional_user_cost = additional_users * pricing_tier["additional_user_fee"]
        
        # Calculate deployment costs
        deployment_type = client_config.get("deployment", {}).get("type", "cloud")
        deployment_cost = 0
        
        if deployment_type == "cloud":
            deployment_cost = 2500
        elif deployment_type == "on_premise":
            deployment_cost = 0  # Customer's hardware
        elif deployment_type == "hybrid":
            deployment_cost = 1500
        
        # Calculate support costs
        support_level = client_config.get("support_level", "standard")
        support_cost = 0
        
        if support_level == "standard":
            support_cost = 0  # Included
        elif support_level == "premium":
            support_cost = 2000
        elif support_level == "enterprise":
            support_cost = 5000
        
        # Calculate customization costs
        customization_level = client_config.get("customization_level", "standard")
        customization_cost = 0
        
        if customization_level == "standard":
            customization_cost = 0  # Included
        elif customization_level == "advanced":
            customization_cost = 5000
        elif customization_level == "enterprise":
            customization_cost = 15000
        
        # Calculate total costs
        total_monthly_cost = monthly_fee + additional_user_cost + deployment_cost + support_cost
        total_setup_cost = customization_cost
        
        # Generate cost estimate
        cost_estimate = {
            "monthly_costs": {
                "base_fee": monthly_fee,
                "additional_users": {
                    "count": additional_users,
                    "cost": additional_user_cost
                },
                "deployment": deployment_cost,
                "support": support_cost,
                "total": total_monthly_cost
            },
            "one_time_costs": {
                "customization": customization_cost,
                "total": total_setup_cost
            },
            "annual_cost": total_monthly_cost * 12 + total_setup_cost,
            "pricing_tier": pricing_tier_name,
            "included_features": pricing_tier["features"]
        }
        
        logger.info(f"Generated cost estimate for white-label client configuration")
        return cost_estimate


if __name__ == "__main__":
    # Example usage
    manager = WhiteLabelManager()
    
    # Create a new client instance
    client_info = {
        "name": "Acme Capital",
        "contact_email": "trading@acmecapital.com",
        "pricing_tier": "premium",
        "template": "trading_interface",
        "customization": {
            "theme": "dark",
            "layout": "advanced",
            "modules": "all",
            "branding": {
                "colors": {
                    "primary": "#00796B",
                    "secondary": "#FFC107"
                }
            }
        },
        "deployment": {
            "type": "cloud",
            "provider": "aws",
            "region": "us-east"
        },
        "expected_users": 30,
        "active_users": 28,
        "api_calls_last_30_days": 150000,
        "trades_last_30_days": 5000,
        "logins_last_30_days": 1200,
        "data_transfer_gb_last_30_days": 50
    }
    
    instance = manager.create_client_instance(client_info)
    print("Created client instance:", instance["client_id"])
    
    # Generate client report
    report = manager.generate_client_report(instance["client_id"])
    print("\nClient Report:")
    print(f"Name: {report['name']}")
    print(f"Status: {report['status']}")
    print(f"Pricing Tier: {report['pricing_tier']}")
    print(f"Active Users: {report['active_users']}")
    print(f"Monthly Cost: ${report['billing']['total_monthly_cost']}")
    
    # Generate deployment plan
    plan = manager.generate_deployment_plan(instance["client_id"])
    print("\nDeployment Plan:")
    print(f"Type: {plan['type']}")
    if plan['type'] == 'cloud':
        print(f"Provider: {plan['provider']}")
        print(f"Region: {plan['region']}")
        print(f"Estimated Monthly Cost: ${plan['estimated_cost']['monthly']}")
    
    # Get customization options
    options = manager.generate_customization_options("trading_interface")
    print("\nCustomization Options:")
    print(f"Themes: {options['theme']}")
    print(f"Layouts: {options['layout']}")
    print(f"Branding Options: {', '.join(options['branding'].keys())}")
    
    # Estimate costs
    estimate = manager.estimate_costs(client_info)
    print("\nCost Estimate:")
    print(f"Monthly Cost: ${estimate['monthly_costs']['total']}")
    print(f"One-time Setup Cost: ${estimate['one_time_costs']['total']}")
    print(f"Annual Cost: ${estimate['annual_cost']}")
    
    # Clean up
    manager.delete_client_instance(instance["client_id"])
    print("\nDeleted client instance")