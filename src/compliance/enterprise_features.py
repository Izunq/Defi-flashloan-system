"""
Enterprise Features Module
Integrates all enterprise-grade features for institutional clients.
"""
import os
import logging
import json
import datetime
from typing import Dict, List, Tuple, Any, Optional, Union

# Import modules for each priority
from quantum_security import QuantumSecurityManager
from ai_market_making import AIMarketMaker
from institutional_features import (
    PrimeBrokerageManager,
    ReportingDashboard,
    RiskManagementConsole,
    WhiteLabelManager
)
from global_expansion import (
    MultiRegionDeployment,
    ComplianceIntegration,
    MarketAccess
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnterpriseFeatures:
    """
    Manager for enterprise features.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize enterprise features manager.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config = self._load_config(config_path)
        
        # Initialize components based on configuration
        self._initialize_components()
        
        logger.info("Initialized Enterprise Features Manager")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        Load configuration from file or use defaults.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        default_config = {
            "enabled_features": {
                "quantum_security": True,
                "ai_market_making": True,
                "prime_brokerage": True,
                "reporting_dashboard": True,
                "risk_management": True,
                "white_label": True,
                "multi_region_deployment": True,
                "compliance_integration": True,
                "market_access": True
            },
            "feature_configs": {
                "quantum_security": {
                    "config_path": "quantum_security/config.json"
                },
                "ai_market_making": {
                    "config_path": "ai_market_making/config.json"
                },
                "institutional_features": {
                    "prime_brokerage_config_path": "institutional_features/prime_brokerage_config.json",
                    "reporting_dashboard_config_path": "institutional_features/reporting_dashboard_config.json",
                    "risk_management_config_path": "institutional_features/risk_management_config.json",
                    "white_label_config_path": "institutional_features/white_label_config.json"
                },
                "global_expansion": {
                    "multi_region_config_path": "global_expansion/multi_region_config.json",
                    "compliance_config_path": "global_expansion/compliance_config.json",
                    "market_access_config_path": "global_expansion/market_access_config.json"
                }
            }
        }
        
        if not config_path or not os.path.exists(config_path):
            logger.info("Using default enterprise features configuration")
            return default_config
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Merge with defaults for any missing keys
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
                elif isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        if subkey not in config[key]:
                            config[key][subkey] = subvalue
            
            logger.info(f"Loaded enterprise features configuration from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
            return default_config
    
    def _initialize_components(self) -> None:
        """Initialize components based on configuration."""
        self.components = {}
        
        # Initialize Quantum Security
        if self.config["enabled_features"]["quantum_security"]:
            try:
                config_path = self.config["feature_configs"]["quantum_security"]["config_path"]
                self.components["quantum_security"] = QuantumSecurityManager(config_path)
                logger.info("Initialized Quantum Security component")
            except Exception as e:
                logger.error(f"Error initializing Quantum Security component: {e}")
        
        # Initialize AI Market Making
        if self.config["enabled_features"]["ai_market_making"]:
            try:
                config_path = self.config["feature_configs"]["ai_market_making"]["config_path"]
                self.components["ai_market_making"] = AIMarketMaker(config_path)
                logger.info("Initialized AI Market Making component")
            except Exception as e:
                logger.error(f"Error initializing AI Market Making component: {e}")
        
        # Initialize Prime Brokerage
        if self.config["enabled_features"]["prime_brokerage"]:
            try:
                config_path = self.config["feature_configs"]["institutional_features"]["prime_brokerage_config_path"]
                self.components["prime_brokerage"] = PrimeBrokerageManager(config_path)
                logger.info("Initialized Prime Brokerage component")
            except Exception as e:
                logger.error(f"Error initializing Prime Brokerage component: {e}")
        
        # Initialize Reporting Dashboard
        if self.config["enabled_features"]["reporting_dashboard"]:
            try:
                config_path = self.config["feature_configs"]["institutional_features"]["reporting_dashboard_config_path"]
                self.components["reporting_dashboard"] = ReportingDashboard(config_path)
                logger.info("Initialized Reporting Dashboard component")
            except Exception as e:
                logger.error(f"Error initializing Reporting Dashboard component: {e}")
        
        # Initialize Risk Management
        if self.config["enabled_features"]["risk_management"]:
            try:
                config_path = self.config["feature_configs"]["institutional_features"]["risk_management_config_path"]
                self.components["risk_management"] = RiskManagementConsole(config_path)
                logger.info("Initialized Risk Management component")
            except Exception as e:
                logger.error(f"Error initializing Risk Management component: {e}")
        
        # Initialize White Label
        if self.config["enabled_features"]["white_label"]:
            try:
                config_path = self.config["feature_configs"]["institutional_features"]["white_label_config_path"]
                self.components["white_label"] = WhiteLabelManager(config_path)
                logger.info("Initialized White Label component")
            except Exception as e:
                logger.error(f"Error initializing White Label component: {e}")
        
        # Initialize Multi-Region Deployment
        if self.config["enabled_features"]["multi_region_deployment"]:
            try:
                config_path = self.config["feature_configs"]["global_expansion"]["multi_region_config_path"]
                self.components["multi_region_deployment"] = MultiRegionDeployment(config_path)
                logger.info("Initialized Multi-Region Deployment component")
            except Exception as e:
                logger.error(f"Error initializing Multi-Region Deployment component: {e}")
        
        # Initialize Compliance Integration
        if self.config["enabled_features"]["compliance_integration"]:
            try:
                config_path = self.config["feature_configs"]["global_expansion"]["compliance_config_path"]
                self.components["compliance_integration"] = ComplianceIntegration(config_path)
                logger.info("Initialized Compliance Integration component")
            except Exception as e:
                logger.error(f"Error initializing Compliance Integration component: {e}")
        
        # Initialize Market Access
        if self.config["enabled_features"]["market_access"]:
            try:
                config_path = self.config["feature_configs"]["global_expansion"]["market_access_config_path"]
                self.components["market_access"] = MarketAccess(config_path)
                logger.info("Initialized Market Access component")
            except Exception as e:
                logger.error(f"Error initializing Market Access component: {e}")
    
    def get_component(self, component_name: str) -> Any:
        """
        Get a component by name.
        
        Args:
            component_name: Component name
            
        Returns:
            Component instance
        """
        if component_name not in self.components:
            raise ValueError(f"Component not found or not enabled: {component_name}")
        
        return self.components[component_name]
    
    def get_enabled_components(self) -> Dict[str, Any]:
        """
        Get all enabled components.
        
        Returns:
            Dictionary mapping component names to component instances
        """
        return self.components
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get status of all components.
        
        Returns:
            Status dictionary
        """
        status = {
            "timestamp": datetime.datetime.now().isoformat(),
            "components": {}
        }
        
        for component_name, component in self.components.items():
            status["components"][component_name] = {
                "enabled": True,
                "status": "ACTIVE"
            }
        
        for component_name in self.config["enabled_features"]:
            if component_name not in self.components:
                status["components"][component_name] = {
                    "enabled": self.config["enabled_features"][component_name],
                    "status": "INACTIVE"
                }
        
        return status


if __name__ == "__main__":
    # Example usage
    enterprise = EnterpriseFeatures()
    
    # Get status
    status = enterprise.get_status()
    print("Enterprise Features Status:")
    for component_name, component_status in status["components"].items():
        print(f"- {component_name}: {component_status['status']}")
    
    # Use Quantum Security component
    if "quantum_security" in enterprise.components:
        quantum_security = enterprise.get_component("quantum_security")
        quantum_status = quantum_security.get_security_status()
        print("\nQuantum Security Status:")
        print(f"Dilithium Available: {quantum_status['dilithium_available']}")
        print(f"SPHINCS+ Available: {quantum_status['sphincs_available']}")
        print(f"QKD Available: {quantum_status['qkd_available']}")
    
    # Use AI Market Making component
    if "ai_market_making" in enterprise.components:
        ai_market_maker = enterprise.get_component("ai_market_making")
        ai_status = ai_market_maker.get_status()
        print("\nAI Market Maker Status:")
        print(f"Trading Active: {ai_status['trading_active']}")
        print(f"Model Trained: {ai_status['model_trained']}")
        print(f"Total Trades: {ai_status['total_trades']}")
    
    # Use Multi-Region Deployment component
    if "multi_region_deployment" in enterprise.components:
        multi_region = enterprise.get_component("multi_region_deployment")
        regions = multi_region.config_manager.get_enabled_regions()
        print("\nEnabled Regions:")
        for region_code, region in regions.items():
            print(f"- {region.name} ({region_code})")
    
    # Use Market Access component
    if "market_access" in enterprise.components:
        market_access = enterprise.get_component("market_access")
        markets = market_access.config_manager.get_enabled_markets()
        print("\nEnabled Markets:")
        for market_id, market in markets.items():
            print(f"- {market.name} ({market_id})")