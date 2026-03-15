"""
Market Access Module
Provides integration with global markets and exchanges.
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

class MarketConfig:
    """
    Configuration for a market.
    """
    
    def __init__(self, market_id: str, config: Dict[str, Any]):
        """
        Initialize market configuration.
        
        Args:
            market_id: Market ID
            config: Market configuration
        """
        self.market_id = market_id
        self.name = config.get("name", market_id)
        self.region = config.get("region", "")
        self.country = config.get("country", "")
        self.currency = config.get("currency", "")
        self.timezone = config.get("timezone", "UTC")
        self.trading_hours = config.get("trading_hours", {})
        self.holidays = config.get("holidays", [])
        self.exchanges = config.get("exchanges", [])
        self.regulatory_requirements = config.get("regulatory_requirements", {})
        self.access_requirements = config.get("access_requirements", {})
        self.fee_structure = config.get("fee_structure", {})
        self.market_data = config.get("market_data", {})
        self.enabled = config.get("enabled", True)
        
        logger.info(f"Initialized configuration for market {self.name} ({market_id})")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert market configuration to dictionary.
        
        Returns:
            Market configuration dictionary
        """
        return {
            "market_id": self.market_id,
            "name": self.name,
            "region": self.region,
            "country": self.country,
            "currency": self.currency,
            "timezone": self.timezone,
            "trading_hours": self.trading_hours,
            "holidays": self.holidays,
            "exchanges": self.exchanges,
            "regulatory_requirements": self.regulatory_requirements,
            "access_requirements": self.access_requirements,
            "fee_structure": self.fee_structure,
            "market_data": self.market_data,
            "enabled": self.enabled
        }


class MarketAccessConfig:
    """
    Configuration manager for market access.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize market access configuration manager.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config = self._load_config(config_path)
        self.markets = {}
        
        # Initialize markets
        for market_id, market_config in self.config.get("markets", {}).items():
            self.markets[market_id] = MarketConfig(market_id, market_config)
        
        logger.info(f"Initialized Market Access Configuration with {len(self.markets)} markets")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        Load configuration from file or use defaults.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        default_config = {
            "markets": {
                "us-equities": {
                    "name": "US Equities",
                    "region": "us-east",
                    "country": "United States",
                    "currency": "USD",
                    "timezone": "America/New_York",
                    "trading_hours": {
                        "regular": {
                            "open": "09:30",
                            "close": "16:00"
                        },
                        "pre_market": {
                            "open": "04:00",
                            "close": "09:30"
                        },
                        "after_hours": {
                            "open": "16:00",
                            "close": "20:00"
                        },
                        "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                    },
                    "holidays": [
                        "2023-01-02",  # New Year's Day (observed)
                        "2023-01-16",  # Martin Luther King Jr. Day
                        "2023-02-20",  # Presidents' Day
                        "2023-04-07",  # Good Friday
                        "2023-05-29",  # Memorial Day
                        "2023-06-19",  # Juneteenth
                        "2023-07-04",  # Independence Day
                        "2023-09-04",  # Labor Day
                        "2023-11-23",  # Thanksgiving Day
                        "2023-12-25"   # Christmas Day
                    ],
                    "exchanges": [
                        {
                            "id": "nyse",
                            "name": "New York Stock Exchange",
                            "mic": "XNYS",
                            "enabled": True
                        },
                        {
                            "id": "nasdaq",
                            "name": "NASDAQ",
                            "mic": "XNAS",
                            "enabled": True
                        },
                        {
                            "id": "cboe",
                            "name": "CBOE",
                            "mic": "XCBO",
                            "enabled": True
                        }
                    ],
                    "regulatory_requirements": {
                        "registration": "SEC",
                        "reporting": ["FINRA", "SEC Form 13F"],
                        "compliance": ["Rule 15c3-5", "Regulation SHO", "Regulation NMS"]
                    },
                    "access_requirements": {
                        "broker_dealer_registration": True,
                        "membership": ["FINRA"],
                        "capital_requirement_usd": 500000,
                        "documentation": [
                            "Form BD",
                            "FINRA Membership Application",
                            "Exchange Membership Application"
                        ]
                    },
                    "fee_structure": {
                        "exchange_fees": {
                            "nyse": {
                                "maker": -0.0022,
                                "taker": 0.0030
                            },
                            "nasdaq": {
                                "maker": -0.0020,
                                "taker": 0.0030
                            },
                            "cboe": {
                                "maker": -0.0022,
                                "taker": 0.0030
                            }
                        },
                        "regulatory_fees": {
                            "sec": 0.0000051,
                            "taf": 0.000119
                        },
                        "clearing_fees": 0.0002
                    },
                    "market_data": {
                        "providers": [
                            {
                                "name": "CTA",
                                "feeds": ["CTS", "CQS"],
                                "monthly_fee_usd": 5000
                            },
                            {
                                "name": "UTP",
                                "feeds": ["UTDF", "UQDF"],
                                "monthly_fee_usd": 5000
                            }
                        ],
                        "depth_levels": 10,
                        "latency_ms": 10
                    },
                    "enabled": True
                },
                "eu-equities": {
                    "name": "European Equities",
                    "region": "eu-central",
                    "country": "Multiple",
                    "currency": "EUR",
                    "timezone": "Europe/Paris",
                    "trading_hours": {
                        "regular": {
                            "open": "09:00",
                            "close": "17:30"
                        },
                        "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                    },
                    "holidays": [
                        "2023-01-02",  # New Year's Day (observed)
                        "2023-04-07",  # Good Friday
                        "2023-04-10",  # Easter Monday
                        "2023-05-01",  # Labor Day
                        "2023-12-25",  # Christmas Day
                        "2023-12-26"   # Boxing Day
                    ],
                    "exchanges": [
                        {
                            "id": "xetra",
                            "name": "Deutsche Börse Xetra",
                            "mic": "XETR",
                            "enabled": True
                        },
                        {
                            "id": "euronext",
                            "name": "Euronext",
                            "mic": "XPAR",
                            "enabled": True
                        },
                        {
                            "id": "borsa-italiana",
                            "name": "Borsa Italiana",
                            "mic": "XMIL",
                            "enabled": True
                        }
                    ],
                    "regulatory_requirements": {
                        "registration": "ESMA",
                        "reporting": ["MiFID II Transaction Reporting", "EMIR"],
                        "compliance": ["MiFID II", "MAR", "GDPR"]
                    },
                    "access_requirements": {
                        "broker_dealer_registration": True,
                        "membership": ["Local Regulatory Authority"],
                        "capital_requirement_eur": 730000,
                        "documentation": [
                            "MiFID II Authorization",
                            "Exchange Membership Application",
                            "LEI Registration"
                        ]
                    },
                    "fee_structure": {
                        "exchange_fees": {
                            "xetra": {
                                "maker": -0.0001,
                                "taker": 0.0003
                            },
                            "euronext": {
                                "maker": -0.0002,
                                "taker": 0.0003
                            },
                            "borsa-italiana": {
                                "maker": -0.0001,
                                "taker": 0.0003
                            }
                        },
                        "regulatory_fees": {
                            "esma": 0.00005
                        },
                        "clearing_fees": 0.0001
                    },
                    "market_data": {
                        "providers": [
                            {
                                "name": "STOXX",
                                "feeds": ["Level 1", "Level 2"],
                                "monthly_fee_eur": 4000
                            },
                            {
                                "name": "Euronext Market Data",
                                "feeds": ["Cash", "Derivatives"],
                                "monthly_fee_eur": 3500
                            }
                        ],
                        "depth_levels": 10,
                        "latency_ms": 15
                    },
                    "enabled": True
                },
                "asia-equities": {
                    "name": "Asian Equities",
                    "region": "ap-southeast",
                    "country": "Multiple",
                    "currency": "Multiple",
                    "timezone": "Asia/Singapore",
                    "trading_hours": {
                        "regular": {
                            "open": "09:00",
                            "close": "17:00"
                        },
                        "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                    },
                    "holidays": [
                        "2023-01-02",  # New Year's Day (observed)
                        "2023-01-23",  # Chinese New Year
                        "2023-01-24",  # Chinese New Year
                        "2023-05-01",  # Labor Day
                        "2023-12-25"   # Christmas Day
                    ],
                    "exchanges": [
                        {
                            "id": "sgx",
                            "name": "Singapore Exchange",
                            "mic": "XSES",
                            "enabled": True
                        },
                        {
                            "id": "hkex",
                            "name": "Hong Kong Exchange",
                            "mic": "XHKG",
                            "enabled": True
                        },
                        {
                            "id": "jpx",
                            "name": "Japan Exchange Group",
                            "mic": "XTKS",
                            "enabled": True
                        }
                    ],
                    "regulatory_requirements": {
                        "registration": "Local Regulatory Authority",
                        "reporting": ["Local Regulatory Reporting"],
                        "compliance": ["Local Market Regulations"]
                    },
                    "access_requirements": {
                        "broker_dealer_registration": True,
                        "membership": ["Local Exchange Membership"],
                        "capital_requirement_usd": 1000000,
                        "documentation": [
                            "Local Broker-Dealer License",
                            "Exchange Membership Application",
                            "Local Business Registration"
                        ]
                    },
                    "fee_structure": {
                        "exchange_fees": {
                            "sgx": {
                                "maker": -0.0001,
                                "taker": 0.0003
                            },
                            "hkex": {
                                "maker": 0.0000,
                                "taker": 0.0003
                            },
                            "jpx": {
                                "maker": -0.0001,
                                "taker": 0.0002
                            }
                        },
                        "regulatory_fees": {
                            "local": 0.00005
                        },
                        "clearing_fees": 0.0001
                    },
                    "market_data": {
                        "providers": [
                            {
                                "name": "SGX Market Data",
                                "feeds": ["Level 1", "Level 2"],
                                "monthly_fee_usd": 3000
                            },
                            {
                                "name": "HKEX Market Data",
                                "feeds": ["Standard", "Premium"],
                                "monthly_fee_usd": 3500
                            },
                            {
                                "name": "JPX Market Data",
                                "feeds": ["FLEX Standard", "FLEX Full"],
                                "monthly_fee_usd": 4000
                            }
                        ],
                        "depth_levels": 10,
                        "latency_ms": 20
                    },
                    "enabled": True
                },
                "latam-equities": {
                    "name": "Latin American Equities",
                    "region": "sa-east",
                    "country": "Multiple",
                    "currency": "Multiple",
                    "timezone": "America/Sao_Paulo",
                    "trading_hours": {
                        "regular": {
                            "open": "10:00",
                            "close": "17:30"
                        },
                        "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                    },
                    "holidays": [
                        "2023-01-01",  # New Year's Day
                        "2023-02-20",  # Carnival
                        "2023-02-21",  # Carnival
                        "2023-04-07",  # Good Friday
                        "2023-05-01",  # Labor Day
                        "2023-12-25"   # Christmas Day
                    ],
                    "exchanges": [
                        {
                            "id": "b3",
                            "name": "B3 (Brasil Bolsa Balcão)",
                            "mic": "BVMF",
                            "enabled": True
                        },
                        {
                            "id": "bmv",
                            "name": "Bolsa Mexicana de Valores",
                            "mic": "XMEX",
                            "enabled": True
                        }
                    ],
                    "regulatory_requirements": {
                        "registration": "Local Regulatory Authority",
                        "reporting": ["Local Regulatory Reporting"],
                        "compliance": ["Local Market Regulations"]
                    },
                    "access_requirements": {
                        "broker_dealer_registration": True,
                        "membership": ["Local Exchange Membership"],
                        "capital_requirement_usd": 500000,
                        "documentation": [
                            "Local Broker-Dealer License",
                            "Exchange Membership Application",
                            "Local Business Registration"
                        ]
                    },
                    "fee_structure": {
                        "exchange_fees": {
                            "b3": {
                                "maker": -0.0001,
                                "taker": 0.0003
                            },
                            "bmv": {
                                "maker": 0.0000,
                                "taker": 0.0002
                            }
                        },
                        "regulatory_fees": {
                            "local": 0.00005
                        },
                        "clearing_fees": 0.0001
                    },
                    "market_data": {
                        "providers": [
                            {
                                "name": "B3 Market Data",
                                "feeds": ["Level 1", "Level 2"],
                                "monthly_fee_usd": 2500
                            },
                            {
                                "name": "BMV Market Data",
                                "feeds": ["Basic", "Advanced"],
                                "monthly_fee_usd": 2000
                            }
                        ],
                        "depth_levels": 5,
                        "latency_ms": 25
                    },
                    "enabled": True
                },
                "mena-equities": {
                    "name": "Middle East and North Africa Equities",
                    "region": "me-central",
                    "country": "Multiple",
                    "currency": "Multiple",
                    "timezone": "Asia/Dubai",
                    "trading_hours": {
                        "regular": {
                            "open": "10:00",
                            "close": "15:00"
                        },
                        "days": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
                    },
                    "holidays": [
                        "2023-04-21",  # Eid al-Fitr
                        "2023-04-22",  # Eid al-Fitr
                        "2023-06-28",  # Eid al-Adha
                        "2023-06-29",  # Eid al-Adha
                        "2023-07-19",  # Islamic New Year
                        "2023-09-27"   # Prophet's Birthday
                    ],
                    "exchanges": [
                        {
                            "id": "dfm",
                            "name": "Dubai Financial Market",
                            "mic": "XDFM",
                            "enabled": True
                        },
                        {
                            "id": "adx",
                            "name": "Abu Dhabi Securities Exchange",
                            "mic": "XADS",
                            "enabled": True
                        },
                        {
                            "id": "tadawul",
                            "name": "Saudi Stock Exchange (Tadawul)",
                            "mic": "XSAU",
                            "enabled": True
                        }
                    ],
                    "regulatory_requirements": {
                        "registration": "Local Regulatory Authority",
                        "reporting": ["Local Regulatory Reporting"],
                        "compliance": ["Local Market Regulations", "Shariah Compliance"]
                    },
                    "access_requirements": {
                        "broker_dealer_registration": True,
                        "membership": ["Local Exchange Membership"],
                        "capital_requirement_usd": 1000000,
                        "documentation": [
                            "Local Broker-Dealer License",
                            "Exchange Membership Application",
                            "Local Business Registration"
                        ]
                    },
                    "fee_structure": {
                        "exchange_fees": {
                            "dfm": {
                                "maker": 0.0000,
                                "taker": 0.0003
                            },
                            "adx": {
                                "maker": 0.0000,
                                "taker": 0.0003
                            },
                            "tadawul": {
                                "maker": 0.0000,
                                "taker": 0.0003
                            }
                        },
                        "regulatory_fees": {
                            "local": 0.00005
                        },
                        "clearing_fees": 0.0001
                    },
                    "market_data": {
                        "providers": [
                            {
                                "name": "DFM Market Data",
                                "feeds": ["Level 1", "Level 2"],
                                "monthly_fee_usd": 2000
                            },
                            {
                                "name": "ADX Market Data",
                                "feeds": ["Basic", "Advanced"],
                                "monthly_fee_usd": 2000
                            },
                            {
                                "name": "Tadawul Market Data",
                                "feeds": ["Basic", "Advanced"],
                                "monthly_fee_usd": 2500
                            }
                        ],
                        "depth_levels": 5,
                        "latency_ms": 30
                    },
                    "enabled": True
                },
                "africa-equities": {
                    "name": "African Equities",
                    "region": "af-south",
                    "country": "Multiple",
                    "currency": "Multiple",
                    "timezone": "Africa/Johannesburg",
                    "trading_hours": {
                        "regular": {
                            "open": "09:00",
                            "close": "17:00"
                        },
                        "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                    },
                    "holidays": [
                        "2023-01-02",  # New Year's Day (observed)
                        "2023-03-21",  # Human Rights Day
                        "2023-04-07",  # Good Friday
                        "2023-04-10",  # Family Day
                        "2023-04-27",  # Freedom Day
                        "2023-05-01",  # Workers' Day
                        "2023-06-16",  # Youth Day
                        "2023-08-09",  # National Women's Day
                        "2023-09-25",  # Heritage Day
                        "2023-12-16",  # Day of Reconciliation
                        "2023-12-25",  # Christmas Day
                        "2023-12-26"   # Day of Goodwill
                    ],
                    "exchanges": [
                        {
                            "id": "jse",
                            "name": "Johannesburg Stock Exchange",
                            "mic": "XJSE",
                            "enabled": True
                        },
                        {
                            "id": "nse",
                            "name": "Nigerian Stock Exchange",
                            "mic": "XNSA",
                            "enabled": True
                        }
                    ],
                    "regulatory_requirements": {
                        "registration": "Local Regulatory Authority",
                        "reporting": ["Local Regulatory Reporting"],
                        "compliance": ["Local Market Regulations"]
                    },
                    "access_requirements": {
                        "broker_dealer_registration": True,
                        "membership": ["Local Exchange Membership"],
                        "capital_requirement_usd": 300000,
                        "documentation": [
                            "Local Broker-Dealer License",
                            "Exchange Membership Application",
                            "Local Business Registration"
                        ]
                    },
                    "fee_structure": {
                        "exchange_fees": {
                            "jse": {
                                "maker": 0.0000,
                                "taker": 0.0003
                            },
                            "nse": {
                                "maker": 0.0000,
                                "taker": 0.0002
                            }
                        },
                        "regulatory_fees": {
                            "local": 0.00005
                        },
                        "clearing_fees": 0.0001
                    },
                    "market_data": {
                        "providers": [
                            {
                                "name": "JSE Market Data",
                                "feeds": ["Level 1", "Level 2"],
                                "monthly_fee_usd": 1500
                            },
                            {
                                "name": "NSE Market Data",
                                "feeds": ["Basic", "Advanced"],
                                "monthly_fee_usd": 1000
                            }
                        ],
                        "depth_levels": 5,
                        "latency_ms": 35
                    },
                    "enabled": True
                }
            },
            "global_config": {
                "default_currency": "USD",
                "default_timezone": "UTC",
                "market_data_aggregation": {
                    "enabled": True,
                    "aggregation_interval_ms": 100,
                    "normalization": True
                },
                "order_routing": {
                    "smart_routing": True,
                    "latency_based_routing": True,
                    "cost_based_routing": True
                },
                "risk_management": {
                    "pre_trade_checks": True,
                    "position_limits": True,
                    "market_impact_analysis": True
                },
                "compliance": {
                    "trade_surveillance": True,
                    "regulatory_reporting": True,
                    "audit_trail": True
                }
            }
        }
        
        if not config_path or not os.path.exists(config_path):
            logger.info("Using default market access configuration")
            return default_config
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Merge with defaults for any missing keys
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            
            logger.info(f"Loaded market access configuration from {config_path}")
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
            # Update markets in config
            self.config["markets"] = {market_id: market.to_dict() for market_id, market in self.markets.items()}
            
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"Saved market access configuration to {config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration to {config_path}: {e}")
            return False
    
    def get_market(self, market_id: str) -> Optional[MarketConfig]:
        """
        Get a market configuration.
        
        Args:
            market_id: Market ID
            
        Returns:
            Market configuration or None if not found
        """
        return self.markets.get(market_id)
    
    def get_all_markets(self) -> Dict[str, MarketConfig]:
        """
        Get all market configurations.
        
        Returns:
            Dictionary mapping market IDs to market configurations
        """
        return self.markets
    
    def get_enabled_markets(self) -> Dict[str, MarketConfig]:
        """
        Get all enabled market configurations.
        
        Returns:
            Dictionary mapping market IDs to enabled market configurations
        """
        return {market_id: market for market_id, market in self.markets.items() if market.enabled}
    
    def get_markets_for_region(self, region_code: str) -> Dict[str, MarketConfig]:
        """
        Get market configurations for a region.
        
        Args:
            region_code: Region code
            
        Returns:
            Dictionary mapping market IDs to market configurations
        """
        return {market_id: market for market_id, market in self.markets.items() if market.region == region_code}
    
    def add_market(self, market_id: str, market_config: Dict[str, Any]) -> MarketConfig:
        """
        Add a new market configuration.
        
        Args:
            market_id: Market ID
            market_config: Market configuration
            
        Returns:
            New market configuration
        """
        if market_id in self.markets:
            raise ValueError(f"Market already exists: {market_id}")
        
        market = MarketConfig(market_id, market_config)
        self.markets[market_id] = market
        
        logger.info(f"Added new market: {market.name} ({market_id})")
        return market
    
    def update_market(self, market_id: str, market_config: Dict[str, Any]) -> MarketConfig:
        """
        Update an existing market configuration.
        
        Args:
            market_id: Market ID
            market_config: Updated market configuration
            
        Returns:
            Updated market configuration
        """
        if market_id not in self.markets:
            raise ValueError(f"Market not found: {market_id}")
        
        market = MarketConfig(market_id, market_config)
        self.markets[market_id] = market
        
        logger.info(f"Updated market: {market.name} ({market_id})")
        return market
    
    def delete_market(self, market_id: str) -> bool:
        """
        Delete a market configuration.
        
        Args:
            market_id: Market ID
            
        Returns:
            True if successful, False otherwise
        """
        if market_id not in self.markets:
            logger.warning(f"Market not found: {market_id}")
            return False
        
        del self.markets[market_id]
        
        logger.info(f"Deleted market: {market_id}")
        return True
    
    def enable_market(self, market_id: str) -> bool:
        """
        Enable a market.
        
        Args:
            market_id: Market ID
            
        Returns:
            True if successful, False otherwise
        """
        if market_id not in self.markets:
            logger.warning(f"Market not found: {market_id}")
            return False
        
        self.markets[market_id].enabled = True
        
        logger.info(f"Enabled market: {market_id}")
        return True
    
    def disable_market(self, market_id: str) -> bool:
        """
        Disable a market.
        
        Args:
            market_id: Market ID
            
        Returns:
            True if successful, False otherwise
        """
        if market_id not in self.markets:
            logger.warning(f"Market not found: {market_id}")
            return False
        
        self.markets[market_id].enabled = False
        
        logger.info(f"Disabled market: {market_id}")
        return True
    
    def get_global_config(self) -> Dict[str, Any]:
        """
        Get global market access configuration.
        
        Returns:
            Global configuration dictionary
        """
        return self.config.get("global_config", {})
    
    def update_global_config(self, global_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update global market access configuration.
        
        Args:
            global_config: Updated global configuration
            
        Returns:
            Updated global configuration
        """
        self.config["global_config"] = global_config
        
        logger.info("Updated global market access configuration")
        return global_config


class MarketAccess:
    """
    Manager for market access.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize market access manager.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config_manager = MarketAccessConfig(config_path)
        
        logger.info("Initialized Market Access Manager")
    
    def get_market_info(self, market_id: str) -> Dict[str, Any]:
        """
        Get information about a market.
        
        Args:
            market_id: Market ID
            
        Returns:
            Market information
        """
        # Get market configuration
        market = self.config_manager.get_market(market_id)
        if not market:
            raise ValueError(f"Market not found: {market_id}")
        
        logger.info(f"Getting information for market: {market.name} ({market_id})")
        
        # Convert market configuration to dictionary
        market_info = market.to_dict()
        
        # Add additional information
        market_info["status"] = "ACTIVE" if market.enabled else "INACTIVE"
        market_info["current_time"] = datetime.datetime.now().astimezone(datetime.timezone.utc).isoformat()
        
        # Determine if market is currently open
        market_info["is_open"] = self._is_market_open(market)
        
        # Add next open/close times
        next_open, next_close = self._get_next_open_close(market)
        market_info["next_open"] = next_open
        market_info["next_close"] = next_close
        
        logger.info(f"Retrieved information for market: {market.name} ({market_id})")
        return market_info
    
    def _is_market_open(self, market: MarketConfig) -> bool:
        """
        Check if a market is currently open.
        
        Args:
            market: Market configuration
            
        Returns:
            True if market is open, False otherwise
        """
        # Get current time in market timezone
        now = datetime.datetime.now(datetime.timezone.utc)
        market_tz = datetime.timezone(datetime.timedelta(hours=0))  # Default to UTC
        
        try:
            import pytz
            market_tz = pytz.timezone(market.timezone)
            now = now.astimezone(market_tz)
        except ImportError:
            logger.warning("pytz not available, using UTC")
        except Exception as e:
            logger.warning(f"Error converting timezone: {e}")
        
        # Check if today is a trading day
        weekday = now.strftime("%A")
        if weekday not in market.trading_hours.get("days", []):
            return False
        
        # Check if today is a holiday
        today = now.strftime("%Y-%m-%d")
        if today in market.holidays:
            return False
        
        # Check if current time is within trading hours
        current_time = now.strftime("%H:%M")
        
        # Check regular hours
        regular_hours = market.trading_hours.get("regular", {})
        regular_open = regular_hours.get("open", "00:00")
        regular_close = regular_hours.get("close", "00:00")
        
        if regular_open <= current_time < regular_close:
            return True
        
        # Check pre-market hours
        pre_market = market.trading_hours.get("pre_market", {})
        if pre_market:
            pre_open = pre_market.get("open", "00:00")
            pre_close = pre_market.get("close", "00:00")
            
            if pre_open <= current_time < pre_close:
                return True
        
        # Check after-hours
        after_hours = market.trading_hours.get("after_hours", {})
        if after_hours:
            after_open = after_hours.get("open", "00:00")
            after_close = after_hours.get("close", "00:00")
            
            if after_open <= current_time < after_close:
                return True
        
        return False
    
    def _get_next_open_close(self, market: MarketConfig) -> Tuple[str, str]:
        """
        Get the next market open and close times.
        
        Args:
            market: Market configuration
            
        Returns:
            Tuple containing (next_open, next_close) in ISO format
        """
        # Get current time in market timezone
        now = datetime.datetime.now(datetime.timezone.utc)
        market_tz = datetime.timezone(datetime.timedelta(hours=0))  # Default to UTC
        
        try:
            import pytz
            market_tz = pytz.timezone(market.timezone)
            now = now.astimezone(market_tz)
        except ImportError:
            logger.warning("pytz not available, using UTC")
        except Exception as e:
            logger.warning(f"Error converting timezone: {e}")
        
        # Get trading hours
        regular_hours = market.trading_hours.get("regular", {})
        regular_open = regular_hours.get("open", "00:00")
        regular_close = regular_hours.get("close", "00:00")
        
        # Get trading days
        trading_days = market.trading_hours.get("days", [])
        
        # Find next trading day
        next_open_datetime = None
        next_close_datetime = None
        
        # Check up to 10 days ahead
        for i in range(10):
            check_date = now.date() + datetime.timedelta(days=i)
            check_datetime = datetime.datetime.combine(check_date, datetime.time.min, tzinfo=market_tz)
            
            # Check if it's a trading day
            weekday = check_datetime.strftime("%A")
            if weekday not in trading_days:
                continue
            
            # Check if it's a holiday
            check_date_str = check_date.strftime("%Y-%m-%d")
            if check_date_str in market.holidays:
                continue
            
            # Parse open and close times
            open_hour, open_minute = map(int, regular_open.split(":"))
            close_hour, close_minute = map(int, regular_close.split(":"))
            
            open_datetime = check_datetime.replace(hour=open_hour, minute=open_minute)
            close_datetime = check_datetime.replace(hour=close_hour, minute=close_minute)
            
            # If we're looking at today and it's already past the open time
            if i == 0 and now > open_datetime:
                # If it's also past the close time, continue to next day
                if now > close_datetime:
                    continue
                # Otherwise, use today's close time and tomorrow's open time
                else:
                    next_close_datetime = close_datetime
                    # Find next trading day for open time
                    for j in range(1, 10):
                        next_date = now.date() + datetime.timedelta(days=j)
                        next_datetime = datetime.datetime.combine(next_date, datetime.time.min, tzinfo=market_tz)
                        
                        # Check if it's a trading day
                        next_weekday = next_datetime.strftime("%A")
                        if next_weekday not in trading_days:
                            continue
                        
                        # Check if it's a holiday
                        next_date_str = next_date.strftime("%Y-%m-%d")
                        if next_date_str in market.holidays:
                            continue
                        
                        next_open_datetime = next_datetime.replace(hour=open_hour, minute=open_minute)
                        break
                    
                    break
            else:
                next_open_datetime = open_datetime
                next_close_datetime = close_datetime
                break
        
        # Format as ISO strings
        next_open = next_open_datetime.isoformat() if next_open_datetime else None
        next_close = next_close_datetime.isoformat() if next_close_datetime else None
        
        return next_open, next_close
    
    def get_all_market_statuses(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status information for all markets.
        
        Returns:
            Dictionary mapping market IDs to status information
        """
        logger.info("Getting status for all markets")
        
        # Get all markets
        markets = self.config_manager.get_all_markets()
        
        # Get status for each market
        market_statuses = {}
        for market_id, market in markets.items():
            is_open = self._is_market_open(market)
            next_open, next_close = self._get_next_open_close(market)
            
            market_statuses[market_id] = {
                "market_id": market_id,
                "name": market.name,
                "region": market.region,
                "country": market.country,
                "currency": market.currency,
                "status": "ACTIVE" if market.enabled else "INACTIVE",
                "is_open": is_open,
                "next_open": next_open,
                "next_close": next_close
            }
        
        logger.info(f"Retrieved status for {len(market_statuses)} markets")
        return market_statuses
    
    def get_market_calendar(self, market_id: str, year: int, month: int) -> Dict[str, Any]:
        """
        Get trading calendar for a market.
        
        Args:
            market_id: Market ID
            year: Year
            month: Month
            
        Returns:
            Trading calendar
        """
        # Get market configuration
        market = self.config_manager.get_market(market_id)
        if not market:
            raise ValueError(f"Market not found: {market_id}")
        
        logger.info(f"Getting trading calendar for market: {market.name} ({market_id})")
        
        # Generate calendar
        import calendar
        cal = calendar.monthcalendar(year, month)
        
        # Get trading days
        trading_days = market.trading_hours.get("days", [])
        
        # Get holidays for the month
        holidays = [day for day in market.holidays if day.startswith(f"{year}-{month:02d}")]
        
        # Generate calendar data
        calendar_data = {
            "market_id": market_id,
            "name": market.name,
            "year": year,
            "month": month,
            "trading_days": trading_days,
            "holidays": holidays,
            "calendar": []
        }
        
        # Fill calendar data
        for week in cal:
            week_data = []
            for day in week:
                if day == 0:
                    # Day outside the month
                    week_data.append(None)
                else:
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    weekday = datetime.date(year, month, day).strftime("%A")
                    
                    day_data = {
                        "day": day,
                        "date": date_str,
                        "weekday": weekday,
                        "is_trading_day": weekday in trading_days and date_str not in holidays,
                        "is_holiday": date_str in holidays
                    }
                    
                    week_data.append(day_data)
            
            calendar_data["calendar"].append(week_data)
        
        logger.info(f"Generated trading calendar for market: {market.name} ({market_id})")
        return calendar_data
    
    def get_market_access_requirements(self, market_id: str) -> Dict[str, Any]:
        """
        Get access requirements for a market.
        
        Args:
            market_id: Market ID
            
        Returns:
            Access requirements
        """
        # Get market configuration
        market = self.config_manager.get_market(market_id)
        if not market:
            raise ValueError(f"Market not found: {market_id}")
        
        logger.info(f"Getting access requirements for market: {market.name} ({market_id})")
        
        # Get access requirements
        access_requirements = {
            "market_id": market_id,
            "name": market.name,
            "region": market.region,
            "country": market.country,
            "regulatory_requirements": market.regulatory_requirements,
            "access_requirements": market.access_requirements,
            "estimated_setup_time_days": 90,
            "estimated_setup_cost_usd": 50000,
            "ongoing_requirements": {
                "reporting_frequency": "DAILY",
                "audit_frequency": "ANNUAL",
                "capital_maintenance": True
            }
        }
        
        logger.info(f"Retrieved access requirements for market: {market.name} ({market_id})")
        return access_requirements
    
    def get_market_fee_analysis(self, market_id: str, monthly_volume: float, avg_trade_size: float) -> Dict[str, Any]:
        """
        Get fee analysis for a market.
        
        Args:
            market_id: Market ID
            monthly_volume: Monthly trading volume
            avg_trade_size: Average trade size
            
        Returns:
            Fee analysis
        """
        # Get market configuration
        market = self.config_manager.get_market(market_id)
        if not market:
            raise ValueError(f"Market not found: {market_id}")
        
        logger.info(f"Generating fee analysis for market: {market.name} ({market_id})")
        
        # Get fee structure
        fee_structure = market.fee_structure
        
        # Calculate number of trades
        num_trades = monthly_volume / avg_trade_size
        
        # Calculate exchange fees
        exchange_fees = {}
        total_exchange_fees = 0
        
        for exchange_id, fees in fee_structure.get("exchange_fees", {}).items():
            # Assume 50% maker, 50% taker for simplicity
            maker_fee = fees.get("maker", 0)
            taker_fee = fees.get("taker", 0)
            
            # Calculate fees for this exchange (assume equal distribution across exchanges)
            exchange_volume = monthly_volume / len(fee_structure.get("exchange_fees", {}))
            maker_volume = exchange_volume * 0.5
            taker_volume = exchange_volume * 0.5
            
            maker_fee_amount = maker_volume * maker_fee
            taker_fee_amount = taker_volume * taker_fee
            total_fee_amount = maker_fee_amount + taker_fee_amount
            
            exchange_fees[exchange_id] = {
                "maker_fee_rate": maker_fee,
                "taker_fee_rate": taker_fee,
                "maker_volume": maker_volume,
                "taker_volume": taker_volume,
                "maker_fee_amount": maker_fee_amount,
                "taker_fee_amount": taker_fee_amount,
                "total_fee_amount": total_fee_amount
            }
            
            total_exchange_fees += total_fee_amount
        
        # Calculate regulatory fees
        regulatory_fees = {}
        total_regulatory_fees = 0
        
        for regulator, fee_rate in fee_structure.get("regulatory_fees", {}).items():
            fee_amount = monthly_volume * fee_rate
            
            regulatory_fees[regulator] = {
                "fee_rate": fee_rate,
                "fee_amount": fee_amount
            }
            
            total_regulatory_fees += fee_amount
        
        # Calculate clearing fees
        clearing_fee_rate = fee_structure.get("clearing_fees", 0)
        clearing_fee_amount = monthly_volume * clearing_fee_rate
        
        # Calculate market data fees
        market_data_fees = 0
        for provider in market.market_data.get("providers", []):
            if "monthly_fee_usd" in provider:
                market_data_fees += provider["monthly_fee_usd"]
            elif "monthly_fee_eur" in provider:
                # Convert EUR to USD (approximate)
                market_data_fees += provider["monthly_fee_eur"] * 1.1
        
        # Calculate total fees
        total_fees = total_exchange_fees + total_regulatory_fees + clearing_fee_amount + market_data_fees
        
        # Generate fee analysis
        fee_analysis = {
            "market_id": market_id,
            "name": market.name,
            "monthly_volume": monthly_volume,
            "avg_trade_size": avg_trade_size,
            "num_trades": num_trades,
            "exchange_fees": exchange_fees,
            "total_exchange_fees": total_exchange_fees,
            "regulatory_fees": regulatory_fees,
            "total_regulatory_fees": total_regulatory_fees,
            "clearing_fee_rate": clearing_fee_rate,
            "clearing_fee_amount": clearing_fee_amount,
            "market_data_fees": market_data_fees,
            "total_fees": total_fees,
            "total_fees_bps": (total_fees / monthly_volume) * 10000,
            "fee_per_trade": total_fees / num_trades
        }
        
        logger.info(f"Generated fee analysis for market: {market.name} ({market_id})")
        return fee_analysis
    
    def generate_market_access_plan(self, market_id: str) -> Dict[str, Any]:
        """
        Generate a market access plan.
        
        Args:
            market_id: Market ID
            
        Returns:
            Market access plan
        """
        # Get market configuration
        market = self.config_manager.get_market(market_id)
        if not market:
            raise ValueError(f"Market not found: {market_id}")
        
        logger.info(f"Generating market access plan for: {market.name} ({market_id})")
        
        # Generate plan
        access_plan = {
            "market_id": market_id,
            "name": market.name,
            "region": market.region,
            "country": market.country,
            "currency": market.currency,
            "phases": [
                {
                    "phase": "PREPARATION",
                    "duration_days": 30,
                    "tasks": [
                        {
                            "task": "Market Research",
                            "description": "Research market structure, regulations, and requirements",
                            "duration_days": 10,
                            "dependencies": []
                        },
                        {
                            "task": "Legal Entity Setup",
                            "description": "Establish legal entity in the market jurisdiction",
                            "duration_days": 30,
                            "dependencies": []
                        },
                        {
                            "task": "Initial Regulatory Consultation",
                            "description": "Consult with regulatory authorities",
                            "duration_days": 15,
                            "dependencies": ["Market Research"]
                        }
                    ]
                },
                {
                    "phase": "REGULATORY_APPROVAL",
                    "duration_days": 90,
                    "tasks": [
                        {
                            "task": "Prepare Regulatory Applications",
                            "description": "Prepare and submit regulatory applications",
                            "duration_days": 30,
                            "dependencies": ["Initial Regulatory Consultation", "Legal Entity Setup"]
                        },
                        {
                            "task": "Regulatory Review Process",
                            "description": "Regulatory authority review process",
                            "duration_days": 60,
                            "dependencies": ["Prepare Regulatory Applications"]
                        },
                        {
                            "task": "Compliance Framework Setup",
                            "description": "Establish compliance framework and policies",
                            "duration_days": 45,
                            "dependencies": ["Prepare Regulatory Applications"]
                        }
                    ]
                },
                {
                    "phase": "EXCHANGE_CONNECTIVITY",
                    "duration_days": 60,
                    "tasks": [
                        {
                            "task": "Exchange Membership Application",
                            "description": "Apply for exchange membership",
                            "duration_days": 30,
                            "dependencies": ["Regulatory Review Process"]
                        },
                        {
                            "task": "Technical Connectivity Setup",
                            "description": "Establish technical connectivity to exchanges",
                            "duration_days": 45,
                            "dependencies": ["Exchange Membership Application"]
                        },
                        {
                            "task": "Market Data Integration",
                            "description": "Integrate market data feeds",
                            "duration_days": 30,
                            "dependencies": ["Technical Connectivity Setup"]
                        },
                        {
                            "task": "Conformance Testing",
                            "description": "Complete exchange conformance testing",
                            "duration_days": 15,
                            "dependencies": ["Technical Connectivity Setup", "Market Data Integration"]
                        }
                    ]
                },
                {
                    "phase": "OPERATIONAL_READINESS",
                    "duration_days": 45,
                    "tasks": [
                        {
                            "task": "Trading Operations Setup",
                            "description": "Establish trading operations and procedures",
                            "duration_days": 30,
                            "dependencies": ["Conformance Testing"]
                        },
                        {
                            "task": "Risk Management Implementation",
                            "description": "Implement risk management systems",
                            "duration_days": 30,
                            "dependencies": ["Conformance Testing"]
                        },
                        {
                            "task": "Reporting Systems Setup",
                            "description": "Establish regulatory reporting systems",
                            "duration_days": 30,
                            "dependencies": ["Conformance Testing"]
                        },
                        {
                            "task": "UAT Testing",
                            "description": "Conduct user acceptance testing",
                            "duration_days": 15,
                            "dependencies": ["Trading Operations Setup", "Risk Management Implementation", "Reporting Systems Setup"]
                        }
                    ]
                },
                {
                    "phase": "GO_LIVE",
                    "duration_days": 15,
                    "tasks": [
                        {
                            "task": "Final Certification",
                            "description": "Obtain final certification from exchanges and regulators",
                            "duration_days": 10,
                            "dependencies": ["UAT Testing"]
                        },
                        {
                            "task": "Production Deployment",
                            "description": "Deploy systems to production",
                            "duration_days": 5,
                            "dependencies": ["Final Certification"]
                        },
                        {
                            "task": "Go-Live",
                            "description": "Begin live trading",
                            "duration_days": 1,
                            "dependencies": ["Production Deployment"]
                        }
                    ]
                }
            ],
            "estimated_timeline": {
                "total_duration_days": 240,
                "expected_start_date": datetime.datetime.now().isoformat(),
                "expected_completion_date": (datetime.datetime.now() + datetime.timedelta(days=240)).isoformat()
            },
            "estimated_costs": {
                "regulatory_fees": 25000,
                "exchange_membership_fees": 50000,
                "technical_connectivity_fees": 30000,
                "market_data_fees": 15000,
                "operational_costs": 30000,
                "total_setup_costs": 150000,
                "annual_recurring_costs": 100000
            },
            "key_risks": [
                {
                    "risk": "Regulatory Approval Delay",
                    "impact": "HIGH",
                    "mitigation": "Early engagement with regulatory authorities"
                },
                {
                    "risk": "Technical Integration Challenges",
                    "impact": "MEDIUM",
                    "mitigation": "Thorough testing and experienced integration team"
                },
                {
                    "risk": "Market Structure Changes",
                    "impact": "MEDIUM",
                    "mitigation": "Ongoing monitoring of regulatory developments"
                },
                {
                    "risk": "Operational Readiness",
                    "impact": "HIGH",
                    "mitigation": "Comprehensive UAT testing and dry runs"
                }
            ]
        }
        
        logger.info(f"Generated market access plan for: {market.name} ({market_id})")
        return access_plan


if __name__ == "__main__":
    # Example usage
    market_access = MarketAccess()
    
    # Get all markets
    markets = market_access.config_manager.get_all_markets()
    print(f"Configured markets: {', '.join(markets.keys())}")
    
    # Get markets for a region
    eu_markets = market_access.config_manager.get_markets_for_region("eu-central")
    print(f"\nMarkets in EU Central: {', '.join(eu_markets.keys())}")
    
    # Get market info
    us_equities_info = market_access.get_market_info("us-equities")
    print("\nUS Equities Market Info:")
    print(f"Name: {us_equities_info['name']}")
    print(f"Region: {us_equities_info['region']}")
    print(f"Currency: {us_equities_info['currency']}")
    print(f"Status: {us_equities_info['status']}")
    print(f"Is Open: {us_equities_info['is_open']}")
    print(f"Next Open: {us_equities_info['next_open']}")
    print(f"Next Close: {us_equities_info['next_close']}")
    
    # Get market access requirements
    access_requirements = market_access.get_market_access_requirements("eu-equities")
    print("\nEU Equities Access Requirements:")
    print(f"Regulatory: {', '.join(access_requirements['regulatory_requirements']['compliance'])}")
    print(f"Capital Requirement: {access_requirements['access_requirements']['capital_requirement_eur']} EUR")
    print(f"Documentation: {', '.join(access_requirements['access_requirements']['documentation'])}")
    
    # Generate fee analysis
    fee_analysis = market_access.get_market_fee_analysis("us-equities", 1000000000, 10000)
    print("\nUS Equities Fee Analysis:")
    print(f"Monthly Volume: ${fee_analysis['monthly_volume']:,.2f}")
    print(f"Total Fees: ${fee_analysis['total_fees']:,.2f}")
    print(f"Total Fees (bps): {fee_analysis['total_fees_bps']:.2f}")
    print(f"Fee per Trade: ${fee_analysis['fee_per_trade']:.2f}")
    
    # Generate market access plan
    access_plan = market_access.generate_market_access_plan("asia-equities")
    print("\nAsia Equities Access Plan:")
    print(f"Total Duration: {access_plan['estimated_timeline']['total_duration_days']} days")
    print(f"Total Setup Costs: ${access_plan['estimated_costs']['total_setup_costs']:,.2f}")
    print(f"Annual Recurring Costs: ${access_plan['estimated_costs']['annual_recurring_costs']:,.2f}")
    print("Phases:")
    for phase in access_plan['phases']:
        print(f"- {phase['phase']} ({phase['duration_days']} days)")