"""
Multi-Region Deployment Module
Provides infrastructure for deploying services across multiple global regions.
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

class RegionConfig:
    """
    Configuration for a deployment region.
    """
    
    def __init__(self, region_code: str, config: Dict[str, Any]):
        """
        Initialize region configuration.
        
        Args:
            region_code: Region code
            config: Region configuration
        """
        self.region_code = region_code
        self.name = config.get("name", region_code)
        self.provider = config.get("provider", "aws")
        self.enabled = config.get("enabled", True)
        self.primary = config.get("primary", False)
        self.services = config.get("services", [])
        self.resources = config.get("resources", {})
        self.network = config.get("network", {})
        self.compliance = config.get("compliance", {})
        self.latency_ms = config.get("latency_ms", {})
        
        logger.info(f"Initialized configuration for region {self.name} ({region_code})")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert region configuration to dictionary.
        
        Returns:
            Region configuration dictionary
        """
        return {
            "region_code": self.region_code,
            "name": self.name,
            "provider": self.provider,
            "enabled": self.enabled,
            "primary": self.primary,
            "services": self.services,
            "resources": self.resources,
            "network": self.network,
            "compliance": self.compliance,
            "latency_ms": self.latency_ms
        }


class MultiRegionConfig:
    """
    Configuration manager for multi-region deployment.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize multi-region configuration manager.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config = self._load_config(config_path)
        self.regions = {}
        
        # Initialize regions
        for region_code, region_config in self.config.get("regions", {}).items():
            self.regions[region_code] = RegionConfig(region_code, region_config)
        
        logger.info(f"Initialized Multi-Region Configuration with {len(self.regions)} regions")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        Load configuration from file or use defaults.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        default_config = {
            "regions": {
                "us-east": {
                    "name": "US East (N. Virginia)",
                    "provider": "aws",
                    "enabled": True,
                    "primary": True,
                    "services": ["api", "trading", "data", "auth", "admin"],
                    "resources": {
                        "compute_units": 100,
                        "memory_gb": 256,
                        "storage_gb": 1000,
                        "database_instances": 3
                    },
                    "network": {
                        "vpc_cidr": "10.0.0.0/16",
                        "subnets": ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"],
                        "nat_gateways": 3,
                        "load_balancers": 2
                    },
                    "compliance": {
                        "data_residency": ["US"],
                        "certifications": ["SOC1", "SOC2", "PCI-DSS"]
                    },
                    "latency_ms": {
                        "us-east": 0,
                        "us-west": 80,
                        "eu-central": 100,
                        "ap-southeast": 200,
                        "sa-east": 150
                    }
                },
                "eu-central": {
                    "name": "EU Central (Frankfurt)",
                    "provider": "aws",
                    "enabled": True,
                    "primary": False,
                    "services": ["api", "trading", "data", "auth"],
                    "resources": {
                        "compute_units": 50,
                        "memory_gb": 128,
                        "storage_gb": 500,
                        "database_instances": 2
                    },
                    "network": {
                        "vpc_cidr": "10.1.0.0/16",
                        "subnets": ["10.1.1.0/24", "10.1.2.0/24", "10.1.3.0/24"],
                        "nat_gateways": 2,
                        "load_balancers": 1
                    },
                    "compliance": {
                        "data_residency": ["EU", "GDPR"],
                        "certifications": ["SOC1", "SOC2", "PCI-DSS", "GDPR"]
                    },
                    "latency_ms": {
                        "us-east": 100,
                        "us-west": 150,
                        "eu-central": 0,
                        "ap-southeast": 150,
                        "sa-east": 200
                    }
                },
                "ap-southeast": {
                    "name": "Asia Pacific (Singapore)",
                    "provider": "aws",
                    "enabled": True,
                    "primary": False,
                    "services": ["api", "trading", "data", "auth"],
                    "resources": {
                        "compute_units": 50,
                        "memory_gb": 128,
                        "storage_gb": 500,
                        "database_instances": 2
                    },
                    "network": {
                        "vpc_cidr": "10.2.0.0/16",
                        "subnets": ["10.2.1.0/24", "10.2.2.0/24", "10.2.3.0/24"],
                        "nat_gateways": 2,
                        "load_balancers": 1
                    },
                    "compliance": {
                        "data_residency": ["APAC"],
                        "certifications": ["SOC1", "SOC2", "PCI-DSS"]
                    },
                    "latency_ms": {
                        "us-east": 200,
                        "us-west": 180,
                        "eu-central": 150,
                        "ap-southeast": 0,
                        "sa-east": 300
                    }
                },
                "sa-east": {
                    "name": "South America (São Paulo)",
                    "provider": "aws",
                    "enabled": False,
                    "primary": False,
                    "services": ["api", "trading", "data"],
                    "resources": {
                        "compute_units": 25,
                        "memory_gb": 64,
                        "storage_gb": 250,
                        "database_instances": 1
                    },
                    "network": {
                        "vpc_cidr": "10.3.0.0/16",
                        "subnets": ["10.3.1.0/24", "10.3.2.0/24"],
                        "nat_gateways": 1,
                        "load_balancers": 1
                    },
                    "compliance": {
                        "data_residency": ["LATAM"],
                        "certifications": ["SOC1", "SOC2"]
                    },
                    "latency_ms": {
                        "us-east": 150,
                        "us-west": 180,
                        "eu-central": 200,
                        "ap-southeast": 300,
                        "sa-east": 0
                    }
                },
                "me-central": {
                    "name": "Middle East (UAE)",
                    "provider": "aws",
                    "enabled": False,
                    "primary": False,
                    "services": ["api", "trading", "data"],
                    "resources": {
                        "compute_units": 25,
                        "memory_gb": 64,
                        "storage_gb": 250,
                        "database_instances": 1
                    },
                    "network": {
                        "vpc_cidr": "10.4.0.0/16",
                        "subnets": ["10.4.1.0/24", "10.4.2.0/24"],
                        "nat_gateways": 1,
                        "load_balancers": 1
                    },
                    "compliance": {
                        "data_residency": ["ME"],
                        "certifications": ["SOC1", "SOC2"]
                    },
                    "latency_ms": {
                        "us-east": 180,
                        "us-west": 200,
                        "eu-central": 120,
                        "ap-southeast": 150,
                        "sa-east": 250,
                        "me-central": 0
                    }
                },
                "af-south": {
                    "name": "Africa (Cape Town)",
                    "provider": "aws",
                    "enabled": False,
                    "primary": False,
                    "services": ["api", "data"],
                    "resources": {
                        "compute_units": 10,
                        "memory_gb": 32,
                        "storage_gb": 100,
                        "database_instances": 1
                    },
                    "network": {
                        "vpc_cidr": "10.5.0.0/16",
                        "subnets": ["10.5.1.0/24", "10.5.2.0/24"],
                        "nat_gateways": 1,
                        "load_balancers": 1
                    },
                    "compliance": {
                        "data_residency": ["AF"],
                        "certifications": ["SOC1", "SOC2"]
                    },
                    "latency_ms": {
                        "us-east": 220,
                        "us-west": 250,
                        "eu-central": 150,
                        "ap-southeast": 200,
                        "sa-east": 180,
                        "me-central": 120,
                        "af-south": 0
                    }
                }
            },
            "global_config": {
                "replication": {
                    "enabled": True,
                    "strategy": "active-active",
                    "sync_interval_seconds": 60
                },
                "routing": {
                    "strategy": "latency",
                    "fallback_strategy": "round-robin",
                    "health_check_interval_seconds": 30
                },
                "failover": {
                    "enabled": True,
                    "automatic": True,
                    "threshold_ms": 500,
                    "cooldown_seconds": 300
                },
                "compliance": {
                    "data_sovereignty": True,
                    "pii_restrictions": True,
                    "audit_logging": True
                }
            },
            "service_config": {
                "api": {
                    "deployment_type": "kubernetes",
                    "replicas": 3,
                    "autoscaling": True,
                    "min_replicas": 2,
                    "max_replicas": 10
                },
                "trading": {
                    "deployment_type": "kubernetes",
                    "replicas": 5,
                    "autoscaling": True,
                    "min_replicas": 3,
                    "max_replicas": 20
                },
                "data": {
                    "deployment_type": "kubernetes",
                    "replicas": 2,
                    "autoscaling": True,
                    "min_replicas": 1,
                    "max_replicas": 5
                },
                "auth": {
                    "deployment_type": "kubernetes",
                    "replicas": 3,
                    "autoscaling": True,
                    "min_replicas": 2,
                    "max_replicas": 10
                },
                "admin": {
                    "deployment_type": "kubernetes",
                    "replicas": 2,
                    "autoscaling": True,
                    "min_replicas": 1,
                    "max_replicas": 5
                }
            }
        }
        
        if not config_path or not os.path.exists(config_path):
            logger.info("Using default multi-region configuration")
            return default_config
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Merge with defaults for any missing keys
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            
            logger.info(f"Loaded multi-region configuration from {config_path}")
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
            # Update regions in config
            self.config["regions"] = {region_code: region.to_dict() for region_code, region in self.regions.items()}
            
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"Saved multi-region configuration to {config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration to {config_path}: {e}")
            return False
    
    def get_region(self, region_code: str) -> Optional[RegionConfig]:
        """
        Get a region configuration.
        
        Args:
            region_code: Region code
            
        Returns:
            Region configuration or None if not found
        """
        return self.regions.get(region_code)
    
    def get_all_regions(self) -> Dict[str, RegionConfig]:
        """
        Get all region configurations.
        
        Returns:
            Dictionary mapping region codes to region configurations
        """
        return self.regions
    
    def get_enabled_regions(self) -> Dict[str, RegionConfig]:
        """
        Get all enabled region configurations.
        
        Returns:
            Dictionary mapping region codes to enabled region configurations
        """
        return {code: region for code, region in self.regions.items() if region.enabled}
    
    def get_primary_region(self) -> Optional[RegionConfig]:
        """
        Get the primary region configuration.
        
        Returns:
            Primary region configuration or None if not found
        """
        for region in self.regions.values():
            if region.primary and region.enabled:
                return region
        return None
    
    def add_region(self, region_code: str, region_config: Dict[str, Any]) -> RegionConfig:
        """
        Add a new region configuration.
        
        Args:
            region_code: Region code
            region_config: Region configuration
            
        Returns:
            New region configuration
        """
        if region_code in self.regions:
            raise ValueError(f"Region already exists: {region_code}")
        
        region = RegionConfig(region_code, region_config)
        self.regions[region_code] = region
        
        logger.info(f"Added new region: {region.name} ({region_code})")
        return region
    
    def update_region(self, region_code: str, region_config: Dict[str, Any]) -> RegionConfig:
        """
        Update an existing region configuration.
        
        Args:
            region_code: Region code
            region_config: Updated region configuration
            
        Returns:
            Updated region configuration
        """
        if region_code not in self.regions:
            raise ValueError(f"Region not found: {region_code}")
        
        region = RegionConfig(region_code, region_config)
        self.regions[region_code] = region
        
        logger.info(f"Updated region: {region.name} ({region_code})")
        return region
    
    def delete_region(self, region_code: str) -> bool:
        """
        Delete a region configuration.
        
        Args:
            region_code: Region code
            
        Returns:
            True if successful, False otherwise
        """
        if region_code not in self.regions:
            logger.warning(f"Region not found: {region_code}")
            return False
        
        region = self.regions[region_code]
        if region.primary:
            raise ValueError(f"Cannot delete primary region: {region_code}")
        
        del self.regions[region_code]
        
        logger.info(f"Deleted region: {region_code}")
        return True
    
    def set_primary_region(self, region_code: str) -> bool:
        """
        Set the primary region.
        
        Args:
            region_code: Region code
            
        Returns:
            True if successful, False otherwise
        """
        if region_code not in self.regions:
            logger.warning(f"Region not found: {region_code}")
            return False
        
        # Ensure the region is enabled
        if not self.regions[region_code].enabled:
            logger.warning(f"Cannot set disabled region as primary: {region_code}")
            return False
        
        # Clear primary flag from all regions
        for region in self.regions.values():
            region.primary = False
        
        # Set primary flag for the specified region
        self.regions[region_code].primary = True
        
        logger.info(f"Set primary region to: {region_code}")
        return True
    
    def get_global_config(self) -> Dict[str, Any]:
        """
        Get global configuration.
        
        Returns:
            Global configuration dictionary
        """
        return self.config.get("global_config", {})
    
    def update_global_config(self, global_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update global configuration.
        
        Args:
            global_config: Updated global configuration
            
        Returns:
            Updated global configuration
        """
        self.config["global_config"] = global_config
        
        logger.info("Updated global configuration")
        return global_config
    
    def get_service_config(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get service configuration.
        
        Args:
            service_name: Service name (optional)
            
        Returns:
            Service configuration dictionary
        """
        service_config = self.config.get("service_config", {})
        
        if service_name:
            return service_config.get(service_name, {})
        
        return service_config
    
    def update_service_config(self, service_name: str, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update service configuration.
        
        Args:
            service_name: Service name
            service_config: Updated service configuration
            
        Returns:
            Updated service configuration
        """
        if "service_config" not in self.config:
            self.config["service_config"] = {}
        
        self.config["service_config"][service_name] = service_config
        
        logger.info(f"Updated configuration for service: {service_name}")
        return service_config


class MultiRegionDeployment:
    """
    Manager for multi-region deployment.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize multi-region deployment manager.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config_manager = MultiRegionConfig(config_path)
        
        logger.info("Initialized Multi-Region Deployment Manager")
    
    def deploy_region(self, region_code: str) -> Dict[str, Any]:
        """
        Deploy infrastructure to a region.
        
        Args:
            region_code: Region code
            
        Returns:
            Deployment status
        """
        # Get region configuration
        region = self.config_manager.get_region(region_code)
        if not region:
            raise ValueError(f"Region not found: {region_code}")
        
        if not region.enabled:
            raise ValueError(f"Region is disabled: {region_code}")
        
        logger.info(f"Deploying infrastructure to region: {region.name} ({region_code})")
        
        # In a real implementation, this would deploy infrastructure to the region
        # This is a placeholder
        
        # Generate deployment status
        deployment_id = str(uuid.uuid4())
        deployment_status = {
            "deployment_id": deployment_id,
            "region_code": region_code,
            "region_name": region.name,
            "status": "COMPLETED",
            "start_time": datetime.datetime.now().isoformat(),
            "end_time": datetime.datetime.now().isoformat(),
            "services_deployed": region.services,
            "resources_provisioned": region.resources
        }
        
        logger.info(f"Deployed infrastructure to region: {region.name} ({region_code})")
        return deployment_status
    
    def deploy_all_regions(self) -> Dict[str, Dict[str, Any]]:
        """
        Deploy infrastructure to all enabled regions.
        
        Returns:
            Dictionary mapping region codes to deployment status
        """
        logger.info("Deploying infrastructure to all enabled regions")
        
        # Get enabled regions
        enabled_regions = self.config_manager.get_enabled_regions()
        
        # Deploy to each region
        deployment_statuses = {}
        for region_code in enabled_regions:
            try:
                status = self.deploy_region(region_code)
                deployment_statuses[region_code] = status
            except Exception as e:
                logger.error(f"Error deploying to region {region_code}: {e}")
                deployment_statuses[region_code] = {
                    "region_code": region_code,
                    "status": "FAILED",
                    "error": str(e)
                }
        
        logger.info(f"Deployed infrastructure to {len(deployment_statuses)} regions")
        return deployment_statuses
    
    def update_region(self, region_code: str) -> Dict[str, Any]:
        """
        Update infrastructure in a region.
        
        Args:
            region_code: Region code
            
        Returns:
            Update status
        """
        # Get region configuration
        region = self.config_manager.get_region(region_code)
        if not region:
            raise ValueError(f"Region not found: {region_code}")
        
        if not region.enabled:
            raise ValueError(f"Region is disabled: {region_code}")
        
        logger.info(f"Updating infrastructure in region: {region.name} ({region_code})")
        
        # In a real implementation, this would update infrastructure in the region
        # This is a placeholder
        
        # Generate update status
        update_id = str(uuid.uuid4())
        update_status = {
            "update_id": update_id,
            "region_code": region_code,
            "region_name": region.name,
            "status": "COMPLETED",
            "start_time": datetime.datetime.now().isoformat(),
            "end_time": datetime.datetime.now().isoformat(),
            "services_updated": region.services,
            "resources_updated": region.resources
        }
        
        logger.info(f"Updated infrastructure in region: {region.name} ({region_code})")
        return update_status
    
    def decommission_region(self, region_code: str) -> Dict[str, Any]:
        """
        Decommission infrastructure in a region.
        
        Args:
            region_code: Region code
            
        Returns:
            Decommission status
        """
        # Get region configuration
        region = self.config_manager.get_region(region_code)
        if not region:
            raise ValueError(f"Region not found: {region_code}")
        
        if region.primary:
            raise ValueError(f"Cannot decommission primary region: {region_code}")
        
        logger.info(f"Decommissioning infrastructure in region: {region.name} ({region_code})")
        
        # In a real implementation, this would decommission infrastructure in the region
        # This is a placeholder
        
        # Generate decommission status
        decommission_id = str(uuid.uuid4())
        decommission_status = {
            "decommission_id": decommission_id,
            "region_code": region_code,
            "region_name": region.name,
            "status": "COMPLETED",
            "start_time": datetime.datetime.now().isoformat(),
            "end_time": datetime.datetime.now().isoformat(),
            "services_decommissioned": region.services,
            "resources_released": region.resources
        }
        
        # Disable the region
        region.enabled = False
        
        logger.info(f"Decommissioned infrastructure in region: {region.name} ({region_code})")
        return decommission_status
    
    def get_deployment_status(self, region_code: str) -> Dict[str, Any]:
        """
        Get deployment status for a region.
        
        Args:
            region_code: Region code
            
        Returns:
            Deployment status
        """
        # Get region configuration
        region = self.config_manager.get_region(region_code)
        if not region:
            raise ValueError(f"Region not found: {region_code}")
        
        logger.info(f"Getting deployment status for region: {region.name} ({region_code})")
        
        # In a real implementation, this would fetch the actual deployment status
        # This is a placeholder
        
        # Generate deployment status
        deployment_status = {
            "region_code": region_code,
            "region_name": region.name,
            "status": "ACTIVE" if region.enabled else "INACTIVE",
            "last_updated": datetime.datetime.now().isoformat(),
            "services": {
                service: {
                    "status": "RUNNING",
                    "instances": 3,
                    "health": "HEALTHY"
                }
                for service in region.services
            },
            "resources": region.resources,
            "metrics": {
                "cpu_utilization": 0.35,
                "memory_utilization": 0.42,
                "storage_utilization": 0.28,
                "network_in_mbps": 150,
                "network_out_mbps": 75
            }
        }
        
        logger.info(f"Retrieved deployment status for region: {region.name} ({region_code})")
        return deployment_status
    
    def get_all_deployment_statuses(self) -> Dict[str, Dict[str, Any]]:
        """
        Get deployment status for all regions.
        
        Returns:
            Dictionary mapping region codes to deployment status
        """
        logger.info("Getting deployment status for all regions")
        
        # Get all regions
        regions = self.config_manager.get_all_regions()
        
        # Get status for each region
        deployment_statuses = {}
        for region_code in regions:
            try:
                status = self.get_deployment_status(region_code)
                deployment_statuses[region_code] = status
            except Exception as e:
                logger.error(f"Error getting status for region {region_code}: {e}")
                deployment_statuses[region_code] = {
                    "region_code": region_code,
                    "status": "ERROR",
                    "error": str(e)
                }
        
        logger.info(f"Retrieved deployment status for {len(deployment_statuses)} regions")
        return deployment_statuses
    
    def configure_global_routing(self, routing_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Configure global routing.
        
        Args:
            routing_config: Routing configuration
            
        Returns:
            Updated routing configuration
        """
        logger.info("Configuring global routing")
        
        # Get global configuration
        global_config = self.config_manager.get_global_config()
        
        # Update routing configuration
        if "routing" not in global_config:
            global_config["routing"] = {}
        
        global_config["routing"].update(routing_config)
        
        # Update global configuration
        self.config_manager.update_global_config(global_config)
        
        logger.info("Configured global routing")
        return global_config["routing"]
    
    def configure_replication(self, replication_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Configure data replication between regions.
        
        Args:
            replication_config: Replication configuration
            
        Returns:
            Updated replication configuration
        """
        logger.info("Configuring data replication")
        
        # Get global configuration
        global_config = self.config_manager.get_global_config()
        
        # Update replication configuration
        if "replication" not in global_config:
            global_config["replication"] = {}
        
        global_config["replication"].update(replication_config)
        
        # Update global configuration
        self.config_manager.update_global_config(global_config)
        
        logger.info("Configured data replication")
        return global_config["replication"]
    
    def configure_failover(self, failover_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Configure failover between regions.
        
        Args:
            failover_config: Failover configuration
            
        Returns:
            Updated failover configuration
        """
        logger.info("Configuring failover")
        
        # Get global configuration
        global_config = self.config_manager.get_global_config()
        
        # Update failover configuration
        if "failover" not in global_config:
            global_config["failover"] = {}
        
        global_config["failover"].update(failover_config)
        
        # Update global configuration
        self.config_manager.update_global_config(global_config)
        
        logger.info("Configured failover")
        return global_config["failover"]
    
    def test_region_connectivity(self, source_region: str, target_region: str) -> Dict[str, Any]:
        """
        Test connectivity between regions.
        
        Args:
            source_region: Source region code
            target_region: Target region code
            
        Returns:
            Connectivity test results
        """
        # Get region configurations
        source = self.config_manager.get_region(source_region)
        if not source:
            raise ValueError(f"Source region not found: {source_region}")
        
        target = self.config_manager.get_region(target_region)
        if not target:
            raise ValueError(f"Target region not found: {target_region}")
        
        if not source.enabled or not target.enabled:
            raise ValueError("Both regions must be enabled")
        
        logger.info(f"Testing connectivity from {source.name} to {target.name}")
        
        # In a real implementation, this would test actual connectivity
        # This is a placeholder
        
        # Get latency from configuration
        latency_ms = source.latency_ms.get(target_region, 100)
        
        # Generate test results
        test_results = {
            "source_region": source_region,
            "target_region": target_region,
            "timestamp": datetime.datetime.now().isoformat(),
            "connectivity": "SUCCESS",
            "latency_ms": latency_ms,
            "packet_loss": 0.0,
            "bandwidth_mbps": 1000
        }
        
        logger.info(f"Connectivity test from {source.name} to {target.name}: {test_results['connectivity']}")
        return test_results
    
    def test_all_region_connectivity(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        Test connectivity between all enabled regions.
        
        Returns:
            Dictionary mapping source regions to target regions to test results
        """
        logger.info("Testing connectivity between all enabled regions")
        
        # Get enabled regions
        enabled_regions = self.config_manager.get_enabled_regions()
        
        # Test connectivity between each pair of regions
        test_results = {}
        for source_region in enabled_regions:
            test_results[source_region] = {}
            for target_region in enabled_regions:
                if source_region != target_region:
                    try:
                        results = self.test_region_connectivity(source_region, target_region)
                        test_results[source_region][target_region] = results
                    except Exception as e:
                        logger.error(f"Error testing connectivity from {source_region} to {target_region}: {e}")
                        test_results[source_region][target_region] = {
                            "source_region": source_region,
                            "target_region": target_region,
                            "connectivity": "ERROR",
                            "error": str(e)
                        }
        
        logger.info(f"Completed connectivity tests between {len(enabled_regions)} regions")
        return test_results
    
    def generate_deployment_plan(self, region_code: str) -> Dict[str, Any]:
        """
        Generate a deployment plan for a region.
        
        Args:
            region_code: Region code
            
        Returns:
            Deployment plan
        """
        # Get region configuration
        region = self.config_manager.get_region(region_code)
        if not region:
            raise ValueError(f"Region not found: {region_code}")
        
        logger.info(f"Generating deployment plan for region: {region.name} ({region_code})")
        
        # Get service configurations
        service_configs = self.config_manager.get_service_config()
        
        # Generate deployment plan
        deployment_plan = {
            "region_code": region_code,
            "region_name": region.name,
            "provider": region.provider,
            "network": region.network,
            "services": {},
            "resources": region.resources,
            "estimated_cost": {
                "monthly": 0,
                "breakdown": {}
            }
        }
        
        # Add services to deployment plan
        for service in region.services:
            service_config = service_configs.get(service, {})
            deployment_plan["services"][service] = {
                "deployment_type": service_config.get("deployment_type", "kubernetes"),
                "replicas": service_config.get("replicas", 3),
                "autoscaling": service_config.get("autoscaling", True),
                "min_replicas": service_config.get("min_replicas", 2),
                "max_replicas": service_config.get("max_replicas", 10),
                "resources": {
                    "cpu": "1",
                    "memory": "2Gi",
                    "storage": "10Gi"
                }
            }
        
        # Calculate estimated cost
        compute_cost = region.resources.get("compute_units", 0) * 10
        memory_cost = region.resources.get("memory_gb", 0) * 5
        storage_cost = region.resources.get("storage_gb", 0) * 0.1
        database_cost = region.resources.get("database_instances", 0) * 100
        network_cost = 500
        
        total_cost = compute_cost + memory_cost + storage_cost + database_cost + network_cost
        
        deployment_plan["estimated_cost"]["monthly"] = total_cost
        deployment_plan["estimated_cost"]["breakdown"] = {
            "compute": compute_cost,
            "memory": memory_cost,
            "storage": storage_cost,
            "database": database_cost,
            "network": network_cost
        }
        
        logger.info(f"Generated deployment plan for region: {region.name} ({region_code})")
        return deployment_plan
    
    def generate_compliance_report(self, region_code: str) -> Dict[str, Any]:
        """
        Generate a compliance report for a region.
        
        Args:
            region_code: Region code
            
        Returns:
            Compliance report
        """
        # Get region configuration
        region = self.config_manager.get_region(region_code)
        if not region:
            raise ValueError(f"Region not found: {region_code}")
        
        logger.info(f"Generating compliance report for region: {region.name} ({region_code})")
        
        # Get global compliance configuration
        global_config = self.config_manager.get_global_config()
        global_compliance = global_config.get("compliance", {})
        
        # Generate compliance report
        compliance_report = {
            "region_code": region_code,
            "region_name": region.name,
            "timestamp": datetime.datetime.now().isoformat(),
            "data_residency": region.compliance.get("data_residency", []),
            "certifications": region.compliance.get("certifications", []),
            "compliance_status": "COMPLIANT",
            "data_sovereignty": {
                "enabled": global_compliance.get("data_sovereignty", True),
                "status": "COMPLIANT"
            },
            "pii_handling": {
                "enabled": global_compliance.get("pii_restrictions", True),
                "status": "COMPLIANT"
            },
            "audit_logging": {
                "enabled": global_compliance.get("audit_logging", True),
                "status": "COMPLIANT"
            },
            "encryption": {
                "at_rest": True,
                "in_transit": True,
                "status": "COMPLIANT"
            }
        }
        
        logger.info(f"Generated compliance report for region: {region.name} ({region_code})")
        return compliance_report


if __name__ == "__main__":
    # Example usage
    deployment = MultiRegionDeployment()
    
    # Get all regions
    regions = deployment.config_manager.get_all_regions()
    print(f"Configured regions: {', '.join(regions.keys())}")
    
    # Get primary region
    primary_region = deployment.config_manager.get_primary_region()
    print(f"Primary region: {primary_region.name} ({primary_region.region_code})")
    
    # Get enabled regions
    enabled_regions = deployment.config_manager.get_enabled_regions()
    print(f"Enabled regions: {', '.join(enabled_regions.keys())}")
    
    # Generate deployment plan for a region
    us_east_plan = deployment.generate_deployment_plan("us-east")
    print("\nDeployment plan for US East:")
    print(f"Provider: {us_east_plan['provider']}")
    print(f"Services: {', '.join(us_east_plan['services'].keys())}")
    print(f"Estimated monthly cost: ${us_east_plan['estimated_cost']['monthly']}")
    
    # Test connectivity between regions
    connectivity = deployment.test_region_connectivity("us-east", "eu-central")
    print("\nConnectivity test from US East to EU Central:")
    print(f"Status: {connectivity['connectivity']}")
    print(f"Latency: {connectivity['latency_ms']} ms")
    
    # Generate compliance report for a region
    compliance = deployment.generate_compliance_report("eu-central")
    print("\nCompliance report for EU Central:")
    print(f"Data residency: {', '.join(compliance['data_residency'])}")
    print(f"Certifications: {', '.join(compliance['certifications'])}")
    print(f"Compliance status: {compliance['compliance_status']}")