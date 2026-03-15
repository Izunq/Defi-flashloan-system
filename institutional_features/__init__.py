"""
Institutional Features Module
Provides enterprise-grade features for institutional clients.
"""
from institutional_features.prime_brokerage import PrimeBrokerageClient, PrimeBrokerageManager
from institutional_features.reporting_dashboard import ReportGenerator, ReportingDashboard
from institutional_features.risk_management import RiskCalculator, RiskManager, RiskManagementConsole
from institutional_features.white_label import WhiteLabelConfig, WhiteLabelManager

__version__ = "0.1.0"
__all__ = [
    "PrimeBrokerageClient",
    "PrimeBrokerageManager",
    "ReportGenerator",
    "ReportingDashboard",
    "RiskCalculator",
    "RiskManager",
    "RiskManagementConsole",
    "WhiteLabelConfig",
    "WhiteLabelManager"
]