"""
AI-Powered Market Making Module
Provides deep learning and reinforcement learning for market making.
"""
from ai_market_making.ai_market_maker import AIMarketMaker
from ai_market_making.matlab_integration import MATLABIntegration, save_matlab_script

__version__ = "0.1.0"
__all__ = [
    "AIMarketMaker",
    "MATLABIntegration",
    "save_matlab_script"
]