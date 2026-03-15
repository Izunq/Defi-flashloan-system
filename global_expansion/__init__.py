"""
Global Expansion Module
Provides infrastructure for global deployment and market access.
"""
from global_expansion.multi_region_deployment import MultiRegionConfig, RegionConfig, MultiRegionDeployment
from global_expansion.compliance_integration import ComplianceConfig, ComplianceFramework, ComplianceIntegration
from global_expansion.market_access import MarketAccessConfig, MarketConfig, MarketAccess

__version__ = "0.1.0"
__all__ = [
    "MultiRegionConfig",
    "RegionConfig",
    "MultiRegionDeployment",
    "ComplianceConfig",
    "ComplianceFramework",
    "ComplianceIntegration",
    "MarketAccessConfig",
    "MarketConfig",
    "MarketAccess"
]