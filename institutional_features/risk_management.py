"""
Risk Management Console Module
Provides comprehensive risk management capabilities for institutional clients.
"""
import os
import logging
import json
import datetime
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RiskCalculator:
    """
    Calculator for various risk metrics.
    """
    
    @staticmethod
    def calculate_var(returns: np.ndarray, confidence_level: float = 0.95) -> float:
        """
        Calculate Value at Risk (VaR).
        
        Args:
            returns: Array of historical returns
            confidence_level: Confidence level (e.g., 0.95 for 95% confidence)
            
        Returns:
            VaR value
        """
        # Sort returns in ascending order
        sorted_returns = np.sort(returns)
        
        # Find the index corresponding to the confidence level
        index = int((1 - confidence_level) * len(sorted_returns))
        
        # Return the VaR
        return -sorted_returns[index]
    
    @staticmethod
    def calculate_cvar(returns: np.ndarray, confidence_level: float = 0.95) -> float:
        """
        Calculate Conditional Value at Risk (CVaR).
        
        Args:
            returns: Array of historical returns
            confidence_level: Confidence level (e.g., 0.95 for 95% confidence)
            
        Returns:
            CVaR value
        """
        # Calculate VaR
        var = RiskCalculator.calculate_var(returns, confidence_level)
        
        # Find returns that are less than or equal to -VaR
        tail_returns = returns[returns <= -var]
        
        # Calculate CVaR as the average of tail returns
        if len(tail_returns) > 0:
            return -np.mean(tail_returns)
        else:
            return var
    
    @staticmethod
    def calculate_volatility(returns: np.ndarray, annualize: bool = True, trading_days: int = 252) -> float:
        """
        Calculate volatility.
        
        Args:
            returns: Array of historical returns
            annualize: Whether to annualize the volatility
            trading_days: Number of trading days in a year
            
        Returns:
            Volatility value
        """
        # Calculate standard deviation of returns
        volatility = np.std(returns)
        
        # Annualize if requested
        if annualize:
            volatility *= np.sqrt(trading_days)
        
        return volatility
    
    @staticmethod
    def calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.0, 
                             annualize: bool = True, trading_days: int = 252) -> float:
        """
        Calculate Sharpe ratio.
        
        Args:
            returns: Array of historical returns
            risk_free_rate: Risk-free rate
            annualize: Whether to annualize the ratio
            trading_days: Number of trading days in a year
            
        Returns:
            Sharpe ratio
        """
        # Calculate excess returns
        excess_returns = returns - risk_free_rate / trading_days
        
        # Calculate mean excess return
        mean_excess_return = np.mean(excess_returns)
        
        # Calculate volatility
        volatility = RiskCalculator.calculate_volatility(returns, annualize=False)
        
        # Calculate Sharpe ratio
        sharpe_ratio = mean_excess_return / volatility
        
        # Annualize if requested
        if annualize:
            sharpe_ratio *= np.sqrt(trading_days)
        
        return sharpe_ratio
    
    @staticmethod
    def calculate_sortino_ratio(returns: np.ndarray, risk_free_rate: float = 0.0,
                              annualize: bool = True, trading_days: int = 252) -> float:
        """
        Calculate Sortino ratio.
        
        Args:
            returns: Array of historical returns
            risk_free_rate: Risk-free rate
            annualize: Whether to annualize the ratio
            trading_days: Number of trading days in a year
            
        Returns:
            Sortino ratio
        """
        # Calculate excess returns
        excess_returns = returns - risk_free_rate / trading_days
        
        # Calculate mean excess return
        mean_excess_return = np.mean(excess_returns)
        
        # Calculate downside deviation
        downside_returns = returns[returns < 0]
        downside_deviation = np.std(downside_returns) if len(downside_returns) > 0 else 0.0
        
        # Calculate Sortino ratio
        sortino_ratio = mean_excess_return / downside_deviation if downside_deviation > 0 else float('inf')
        
        # Annualize if requested
        if annualize and not np.isinf(sortino_ratio):
            sortino_ratio *= np.sqrt(trading_days)
        
        return sortino_ratio
    
    @staticmethod
    def calculate_max_drawdown(values: np.ndarray) -> float:
        """
        Calculate maximum drawdown.
        
        Args:
            values: Array of portfolio values
            
        Returns:
            Maximum drawdown as a positive percentage
        """
        # Calculate running maximum
        running_max = np.maximum.accumulate(values)
        
        # Calculate drawdowns
        drawdowns = (running_max - values) / running_max
        
        # Return maximum drawdown
        return np.max(drawdowns)
    
    @staticmethod
    def calculate_beta(returns: np.ndarray, market_returns: np.ndarray) -> float:
        """
        Calculate beta.
        
        Args:
            returns: Array of portfolio returns
            market_returns: Array of market returns
            
        Returns:
            Beta value
        """
        # Calculate covariance
        covariance = np.cov(returns, market_returns)[0, 1]
        
        # Calculate market variance
        market_variance = np.var(market_returns)
        
        # Calculate beta
        beta = covariance / market_variance
        
        return beta
    
    @staticmethod
    def calculate_alpha(returns: np.ndarray, market_returns: np.ndarray, 
                      risk_free_rate: float = 0.0, annualize: bool = True, trading_days: int = 252) -> float:
        """
        Calculate alpha.
        
        Args:
            returns: Array of portfolio returns
            market_returns: Array of market returns
            risk_free_rate: Risk-free rate
            annualize: Whether to annualize the alpha
            trading_days: Number of trading days in a year
            
        Returns:
            Alpha value
        """
        # Calculate beta
        beta = RiskCalculator.calculate_beta(returns, market_returns)
        
        # Calculate mean returns
        mean_return = np.mean(returns)
        mean_market_return = np.mean(market_returns)
        
        # Calculate daily risk-free rate
        daily_risk_free_rate = risk_free_rate / trading_days
        
        # Calculate alpha
        alpha = mean_return - (daily_risk_free_rate + beta * (mean_market_return - daily_risk_free_rate))
        
        # Annualize if requested
        if annualize:
            alpha *= trading_days
        
        return alpha
    
    @staticmethod
    def calculate_correlation(returns1: np.ndarray, returns2: np.ndarray) -> float:
        """
        Calculate correlation between two return series.
        
        Args:
            returns1: First array of returns
            returns2: Second array of returns
            
        Returns:
            Correlation coefficient
        """
        return np.corrcoef(returns1, returns2)[0, 1]
    
    @staticmethod
    def calculate_herfindahl_index(weights: np.ndarray) -> float:
        """
        Calculate Herfindahl-Hirschman Index (HHI) for portfolio concentration.
        
        Args:
            weights: Array of portfolio weights
            
        Returns:
            HHI value
        """
        # Square weights and sum
        return np.sum(weights ** 2)
    
    @staticmethod
    def run_stress_test(returns: np.ndarray, positions: Dict[str, Dict[str, Any]], 
                      scenario: Dict[str, float]) -> Dict[str, Any]:
        """
        Run a stress test on a portfolio.
        
        Args:
            returns: Array of historical returns
            positions: Dictionary of positions
            scenario: Dictionary mapping assets to stress returns
            
        Returns:
            Stress test results
        """
        # Calculate portfolio value
        portfolio_value = sum(position["value"] for position in positions.values())
        
        # Calculate position weights
        weights = {asset: position["value"] / portfolio_value for asset, position in positions.items()}
        
        # Calculate stressed returns
        stressed_returns = {}
        for asset, weight in weights.items():
            if asset in scenario:
                stressed_returns[asset] = scenario[asset]
            else:
                # Use historical worst case if asset not in scenario
                asset_returns = returns[:, list(positions.keys()).index(asset)]
                stressed_returns[asset] = np.min(asset_returns)
        
        # Calculate portfolio stressed return
        portfolio_stressed_return = sum(weights[asset] * stressed_returns[asset] for asset in weights)
        
        # Calculate stressed value
        stressed_value = portfolio_value * (1 + portfolio_stressed_return)
        
        # Calculate loss
        loss = portfolio_value - stressed_value
        loss_percentage = loss / portfolio_value
        
        return {
            "scenario": scenario,
            "portfolio_value": portfolio_value,
            "stressed_value": stressed_value,
            "loss": loss,
            "loss_percentage": loss_percentage,
            "asset_stressed_returns": stressed_returns
        }


class RiskManager:
    """
    Manager for risk management functions.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize risk manager.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config = self._load_config(config_path)
        self.calculator = RiskCalculator()
        
        # Initialize risk limits
        self.risk_limits = self.config.get("risk_limits", {})
        
        # Initialize scenarios
        self.scenarios = self.config.get("scenarios", {})
        
        logger.info("Initialized Risk Manager")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        Load configuration from file or use defaults.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        default_config = {
            "risk_limits": {
                "var_limit": 0.05,
                "position_limit": 0.25,
                "concentration_limit": 0.5,
                "correlation_limit": 0.7,
                "drawdown_limit": 0.15,
                "leverage_limit": 2.0
            },
            "scenarios": {
                "market_crash_2008": {
                    "BTC": -0.5,
                    "ETH": -0.6,
                    "SOL": -0.7,
                    "AVAX": -0.65,
                    "DOT": -0.55
                },
                "covid_march_2020": {
                    "BTC": -0.4,
                    "ETH": -0.45,
                    "SOL": -0.5,
                    "AVAX": -0.48,
                    "DOT": -0.42
                },
                "rate_hike_100bp": {
                    "BTC": -0.1,
                    "ETH": -0.12,
                    "SOL": -0.15,
                    "AVAX": -0.14,
                    "DOT": -0.11
                },
                "crypto_winter": {
                    "BTC": -0.7,
                    "ETH": -0.75,
                    "SOL": -0.85,
                    "AVAX": -0.8,
                    "DOT": -0.72
                }
            },
            "risk_free_rate": 0.03,
            "trading_days": 252,
            "var_confidence_level": 0.95,
            "cvar_confidence_level": 0.95,
            "historical_window_days": 252,
            "stress_test_frequency": "DAILY",
            "risk_report_frequency": "DAILY"
        }
        
        if not config_path or not os.path.exists(config_path):
            logger.info("Using default risk manager configuration")
            return default_config
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Merge with defaults for any missing keys
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            
            logger.info(f"Loaded risk manager configuration from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
            return default_config
    
    def calculate_portfolio_risk(self, positions: Dict[str, Dict[str, Any]], 
                               returns: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """
        Calculate comprehensive risk metrics for a portfolio.
        
        Args:
            positions: Dictionary mapping assets to position information
            returns: Dictionary mapping assets to historical returns
            
        Returns:
            Dictionary of risk metrics
        """
        logger.info("Calculating portfolio risk metrics")
        
        # Calculate portfolio value
        portfolio_value = sum(position["value"] for position in positions.values())
        
        # Calculate position weights
        weights = {asset: position["value"] / portfolio_value for asset, position in positions.items()}
        
        # Convert to numpy arrays
        assets = list(positions.keys())
        weights_array = np.array([weights[asset] for asset in assets])
        
        # Create returns matrix
        returns_matrix = np.column_stack([returns[asset] for asset in assets])
        
        # Calculate portfolio returns
        portfolio_returns = returns_matrix.dot(weights_array)
        
        # Calculate risk metrics
        risk_free_rate = self.config.get("risk_free_rate", 0.03)
        trading_days = self.config.get("trading_days", 252)
        var_confidence_level = self.config.get("var_confidence_level", 0.95)
        cvar_confidence_level = self.config.get("cvar_confidence_level", 0.95)
        
        var = self.calculator.calculate_var(portfolio_returns, var_confidence_level)
        cvar = self.calculator.calculate_cvar(portfolio_returns, cvar_confidence_level)
        volatility = self.calculator.calculate_volatility(portfolio_returns, True, trading_days)
        sharpe_ratio = self.calculator.calculate_sharpe_ratio(portfolio_returns, risk_free_rate, True, trading_days)
        sortino_ratio = self.calculator.calculate_sortino_ratio(portfolio_returns, risk_free_rate, True, trading_days)
        
        # Calculate portfolio values
        portfolio_values = np.cumprod(1 + portfolio_returns)
        max_drawdown = self.calculator.calculate_max_drawdown(portfolio_values)
        
        # Calculate concentration metrics
        herfindahl_index = self.calculator.calculate_herfindahl_index(weights_array)
        top_asset = max(weights.items(), key=lambda x: x[1])
        top_3_assets = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:3]
        top_3_concentration = sum(weight for _, weight in top_3_assets)
        
        # Calculate correlation matrix
        correlation_matrix = np.corrcoef(returns_matrix.T)
        
        # Run stress tests
        stress_test_results = {}
        for scenario_name, scenario in self.scenarios.items():
            stress_test_results[scenario_name] = self.calculator.run_stress_test(
                returns_matrix, positions, scenario
            )
        
        # Compile risk metrics
        risk_metrics = {
            "var": var,
            "cvar": cvar,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "max_drawdown": max_drawdown,
            "concentration": {
                "herfindahl_index": herfindahl_index,
                "top_asset": {
                    "asset": top_asset[0],
                    "weight": top_asset[1]
                },
                "top_3_concentration": top_3_concentration,
                "top_3_assets": [
                    {"asset": asset, "weight": weight}
                    for asset, weight in top_3_assets
                ]
            },
            "correlation": {
                "matrix": correlation_matrix.tolist(),
                "assets": assets
            },
            "stress_tests": stress_test_results
        }
        
        logger.info("Calculated portfolio risk metrics")
        return risk_metrics
    
    def check_risk_limits(self, positions: Dict[str, Dict[str, Any]], 
                        risk_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if portfolio risk metrics exceed defined limits.
        
        Args:
            positions: Dictionary mapping assets to position information
            risk_metrics: Dictionary of risk metrics
            
        Returns:
            Dictionary of risk limit checks
        """
        logger.info("Checking risk limits")
        
        # Get risk limits
        risk_limits = self.risk_limits
        
        # Check VaR limit
        var_limit = risk_limits.get("var_limit", 0.05)
        var_check = {
            "limit": var_limit,
            "value": risk_metrics["var"],
            "status": "OK" if risk_metrics["var"] <= var_limit else "EXCEEDED",
            "percentage_of_limit": risk_metrics["var"] / var_limit * 100
        }
        
        # Check position limit
        position_limit = risk_limits.get("position_limit", 0.25)
        top_asset_weight = risk_metrics["concentration"]["top_asset"]["weight"]
        position_check = {
            "limit": position_limit,
            "value": top_asset_weight,
            "status": "OK" if top_asset_weight <= position_limit else "EXCEEDED",
            "percentage_of_limit": top_asset_weight / position_limit * 100,
            "asset": risk_metrics["concentration"]["top_asset"]["asset"]
        }
        
        # Check concentration limit
        concentration_limit = risk_limits.get("concentration_limit", 0.5)
        top_3_concentration = risk_metrics["concentration"]["top_3_concentration"]
        concentration_check = {
            "limit": concentration_limit,
            "value": top_3_concentration,
            "status": "OK" if top_3_concentration <= concentration_limit else "EXCEEDED",
            "percentage_of_limit": top_3_concentration / concentration_limit * 100,
            "assets": [asset["asset"] for asset in risk_metrics["concentration"]["top_3_assets"]]
        }
        
        # Check correlation limit
        correlation_limit = risk_limits.get("correlation_limit", 0.7)
        correlation_matrix = np.array(risk_metrics["correlation"]["matrix"])
        assets = risk_metrics["correlation"]["assets"]
        
        # Find highest correlation (excluding self-correlations)
        np.fill_diagonal(correlation_matrix, 0)
        max_correlation_index = np.unravel_index(np.argmax(correlation_matrix), correlation_matrix.shape)
        max_correlation = correlation_matrix[max_correlation_index]
        max_correlation_assets = (assets[max_correlation_index[0]], assets[max_correlation_index[1]])
        
        correlation_check = {
            "limit": correlation_limit,
            "value": max_correlation,
            "status": "OK" if max_correlation <= correlation_limit else "EXCEEDED",
            "percentage_of_limit": max_correlation / correlation_limit * 100,
            "assets": max_correlation_assets
        }
        
        # Check drawdown limit
        drawdown_limit = risk_limits.get("drawdown_limit", 0.15)
        max_drawdown = risk_metrics["max_drawdown"]
        drawdown_check = {
            "limit": drawdown_limit,
            "value": max_drawdown,
            "status": "OK" if max_drawdown <= drawdown_limit else "EXCEEDED",
            "percentage_of_limit": max_drawdown / drawdown_limit * 100
        }
        
        # Check stress test limits
        stress_test_checks = {}
        for scenario_name, stress_test in risk_metrics["stress_tests"].items():
            loss_percentage = stress_test["loss_percentage"]
            stress_limit = risk_limits.get(f"{scenario_name}_limit", 0.25)
            
            stress_test_checks[scenario_name] = {
                "limit": stress_limit,
                "value": loss_percentage,
                "status": "OK" if loss_percentage <= stress_limit else "EXCEEDED",
                "percentage_of_limit": loss_percentage / stress_limit * 100
            }
        
        # Compile limit checks
        limit_checks = {
            "var": var_check,
            "position": position_check,
            "concentration": concentration_check,
            "correlation": correlation_check,
            "drawdown": drawdown_check,
            "stress_tests": stress_test_checks,
            "overall_status": "OK"
        }
        
        # Determine overall status
        for check_name, check in limit_checks.items():
            if check_name != "overall_status" and check_name != "stress_tests":
                if check["status"] == "EXCEEDED":
                    limit_checks["overall_status"] = "EXCEEDED"
                    break
        
        if limit_checks["overall_status"] == "OK":
            for stress_check in limit_checks["stress_tests"].values():
                if stress_check["status"] == "EXCEEDED":
                    limit_checks["overall_status"] = "EXCEEDED"
                    break
        
        logger.info(f"Risk limit check completed: overall status is {limit_checks['overall_status']}")
        return limit_checks
    
    def generate_risk_recommendations(self, positions: Dict[str, Dict[str, Any]], 
                                    risk_metrics: Dict[str, Any], 
                                    limit_checks: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate risk management recommendations based on risk metrics and limit checks.
        
        Args:
            positions: Dictionary mapping assets to position information
            risk_metrics: Dictionary of risk metrics
            limit_checks: Dictionary of risk limit checks
            
        Returns:
            List of risk management recommendations
        """
        logger.info("Generating risk management recommendations")
        
        recommendations = []
        
        # Check if any limits are exceeded
        if limit_checks["overall_status"] == "EXCEEDED":
            # VaR recommendations
            if limit_checks["var"]["status"] == "EXCEEDED":
                recommendations.append({
                    "type": "REDUCE_RISK",
                    "severity": "HIGH",
                    "description": f"VaR ({limit_checks['var']['value']:.2%}) exceeds limit ({limit_checks['var']['limit']:.2%})",
                    "action": "Reduce overall portfolio risk by decreasing positions in high-volatility assets"
                })
            
            # Position limit recommendations
            if limit_checks["position"]["status"] == "EXCEEDED":
                asset = limit_checks["position"]["asset"]
                recommendations.append({
                    "type": "REDUCE_POSITION",
                    "severity": "HIGH",
                    "description": f"Position in {asset} ({limit_checks['position']['value']:.2%}) exceeds limit ({limit_checks['position']['limit']:.2%})",
                    "action": f"Reduce position in {asset} to below {limit_checks['position']['limit']:.2%} of portfolio"
                })
            
            # Concentration recommendations
            if limit_checks["concentration"]["status"] == "EXCEEDED":
                assets = limit_checks["concentration"]["assets"]
                recommendations.append({
                    "type": "DIVERSIFY",
                    "severity": "MEDIUM",
                    "description": f"Concentration in top 3 assets ({limit_checks['concentration']['value']:.2%}) exceeds limit ({limit_checks['concentration']['limit']:.2%})",
                    "action": f"Diversify away from {', '.join(assets)} to reduce concentration risk"
                })
            
            # Correlation recommendations
            if limit_checks["correlation"]["status"] == "EXCEEDED":
                assets = limit_checks["correlation"]["assets"]
                recommendations.append({
                    "type": "REDUCE_CORRELATION",
                    "severity": "MEDIUM",
                    "description": f"Correlation between {assets[0]} and {assets[1]} ({limit_checks['correlation']['value']:.2f}) exceeds limit ({limit_checks['correlation']['limit']:.2f})",
                    "action": f"Reduce positions in either {assets[0]} or {assets[1]} to decrease correlation risk"
                })
            
            # Drawdown recommendations
            if limit_checks["drawdown"]["status"] == "EXCEEDED":
                recommendations.append({
                    "type": "MANAGE_DRAWDOWN",
                    "severity": "HIGH",
                    "description": f"Maximum drawdown ({limit_checks['drawdown']['value']:.2%}) exceeds limit ({limit_checks['drawdown']['limit']:.2%})",
                    "action": "Implement stop-loss orders and reduce position sizes to manage drawdown risk"
                })
            
            # Stress test recommendations
            for scenario_name, stress_check in limit_checks["stress_tests"].items():
                if stress_check["status"] == "EXCEEDED":
                    recommendations.append({
                        "type": "STRESS_TEST_FAILURE",
                        "severity": "HIGH",
                        "description": f"Portfolio loss in {scenario_name} scenario ({stress_check['value']:.2%}) exceeds limit ({stress_check['limit']:.2%})",
                        "action": f"Adjust portfolio to reduce potential losses in {scenario_name} scenario"
                    })
        
        # Additional recommendations based on risk metrics
        
        # Sharpe ratio recommendations
        sharpe_ratio = risk_metrics["sharpe_ratio"]
        if sharpe_ratio < 1.0:
            recommendations.append({
                "type": "IMPROVE_SHARPE",
                "severity": "MEDIUM",
                "description": f"Sharpe ratio ({sharpe_ratio:.2f}) is below target (1.0)",
                "action": "Adjust portfolio to improve risk-adjusted returns"
            })
        
        # Sortino ratio recommendations
        sortino_ratio = risk_metrics["sortino_ratio"]
        if sortino_ratio < 1.5:
            recommendations.append({
                "type": "IMPROVE_SORTINO",
                "severity": "LOW",
                "description": f"Sortino ratio ({sortino_ratio:.2f}) is below target (1.5)",
                "action": "Focus on reducing downside risk while maintaining returns"
            })
        
        # Herfindahl index recommendations
        herfindahl_index = risk_metrics["concentration"]["herfindahl_index"]
        if herfindahl_index > 0.25:
            recommendations.append({
                "type": "REDUCE_CONCENTRATION",
                "severity": "MEDIUM",
                "description": f"Herfindahl index ({herfindahl_index:.2f}) indicates high concentration",
                "action": "Diversify portfolio across more assets to reduce concentration risk"
            })
        
        logger.info(f"Generated {len(recommendations)} risk management recommendations")
        return recommendations
    
    def optimize_portfolio(self, positions: Dict[str, Dict[str, Any]], 
                         returns: Dict[str, np.ndarray],
                         risk_metrics: Dict[str, Any],
                         target_risk: Optional[float] = None) -> Dict[str, Any]:
        """
        Optimize portfolio to achieve target risk level or maximize risk-adjusted returns.
        
        Args:
            positions: Dictionary mapping assets to position information
            returns: Dictionary mapping assets to historical returns
            risk_metrics: Dictionary of risk metrics
            target_risk: Target risk level (volatility) (optional)
            
        Returns:
            Optimized portfolio weights
        """
        logger.info(f"Optimizing portfolio{' for target risk ' + str(target_risk) if target_risk else ''}")
        
        # Convert to numpy arrays
        assets = list(positions.keys())
        current_weights = np.array([positions[asset]["value"] / sum(p["value"] for p in positions.values()) for asset in assets])
        
        # Create returns matrix
        returns_matrix = np.column_stack([returns[asset] for asset in assets])
        
        # Calculate mean returns and covariance matrix
        mean_returns = np.mean(returns_matrix, axis=0)
        cov_matrix = np.cov(returns_matrix.T)
        
        # In a real implementation, this would use optimization algorithms
        # This is a placeholder that simulates optimization
        
        # If target risk is specified, optimize for maximum return at that risk level
        if target_risk:
            # Simulate optimization by adjusting weights to reach target risk
            current_volatility = risk_metrics["volatility"]
            
            if current_volatility > target_risk:
                # Need to reduce risk
                # Increase weight of lowest volatility asset, decrease highest
                asset_volatilities = np.sqrt(np.diag(cov_matrix))
                min_vol_idx = np.argmin(asset_volatilities)
                max_vol_idx = np.argmax(asset_volatilities)
                
                # Adjust weights (simple heuristic)
                adjustment = min(0.1, current_weights[max_vol_idx])
                optimized_weights = current_weights.copy()
                optimized_weights[max_vol_idx] -= adjustment
                optimized_weights[min_vol_idx] += adjustment
            else:
                # Need to increase risk
                # Increase weight of highest Sharpe ratio asset
                asset_sharpe_ratios = mean_returns / np.sqrt(np.diag(cov_matrix))
                max_sharpe_idx = np.argmax(asset_sharpe_ratios)
                
                # Adjust weights (simple heuristic)
                adjustment = 0.1
                optimized_weights = current_weights.copy()
                optimized_weights = optimized_weights * (1 - adjustment)
                optimized_weights[max_sharpe_idx] += adjustment
        else:
            # Optimize for maximum Sharpe ratio
            # In a real implementation, this would use mean-variance optimization
            # This is a simplified heuristic
            
            # Calculate Sharpe ratios for individual assets
            risk_free_rate = self.config.get("risk_free_rate", 0.03) / self.config.get("trading_days", 252)
            asset_sharpe_ratios = (mean_returns - risk_free_rate) / np.sqrt(np.diag(cov_matrix))
            
            # Rank assets by Sharpe ratio
            ranked_indices = np.argsort(asset_sharpe_ratios)[::-1]
            
            # Allocate more weight to higher Sharpe ratio assets
            optimized_weights = np.zeros_like(current_weights)
            for i, idx in enumerate(ranked_indices):
                # Simple allocation scheme: weight proportional to rank
                optimized_weights[idx] = (len(ranked_indices) - i) / sum(range(1, len(ranked_indices) + 1))
        
        # Normalize weights to sum to 1
        optimized_weights = optimized_weights / np.sum(optimized_weights)
        
        # Calculate expected metrics for optimized portfolio
        optimized_returns = returns_matrix.dot(optimized_weights)
        optimized_volatility = np.sqrt(optimized_weights.T.dot(cov_matrix).dot(optimized_weights))
        optimized_sharpe = (np.mean(optimized_returns) - risk_free_rate) / optimized_volatility
        
        # Calculate changes from current portfolio
        changes = {}
        for i, asset in enumerate(assets):
            current_weight = current_weights[i]
            new_weight = optimized_weights[i]
            change_percentage = (new_weight - current_weight) / current_weight * 100 if current_weight > 0 else float('inf')
            
            changes[asset] = {
                "current_weight": current_weight,
                "new_weight": new_weight,
                "absolute_change": new_weight - current_weight,
                "percentage_change": change_percentage
            }
        
        optimization_result = {
            "optimized_weights": {asset: optimized_weights[i] for i, asset in enumerate(assets)},
            "expected_metrics": {
                "volatility": optimized_volatility,
                "sharpe_ratio": optimized_sharpe,
                "mean_return": np.mean(optimized_returns)
            },
            "changes": changes
        }
        
        logger.info("Portfolio optimization completed")
        return optimization_result


class RiskManagementConsole:
    """
    Console for institutional risk management.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize risk management console.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config = self._load_config(config_path)
        self.risk_manager = RiskManager(config_path)
        
        # Initialize historical data
        self.historical_data = {
            "positions": {},
            "returns": {},
            "risk_metrics": {},
            "limit_checks": {}
        }
        
        logger.info("Initialized Risk Management Console")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        Load configuration from file or use defaults.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        default_config = {
            "console_title": "Institutional Risk Management Console",
            "refresh_interval_seconds": 300,
            "historical_data_retention_days": 90,
            "alert_thresholds": {
                "var_threshold": 0.8,  # 80% of limit
                "position_threshold": 0.8,
                "concentration_threshold": 0.8,
                "correlation_threshold": 0.8,
                "drawdown_threshold": 0.8
            },
            "alert_channels": ["console", "email", "sms"],
            "email_recipients": [],
            "sms_recipients": [],
            "dashboard_sections": [
                "risk_overview", "position_risk", "market_risk", "stress_tests", "optimization"
            ],
            "user_preferences": {}
        }
        
        if not config_path or not os.path.exists(config_path):
            logger.info("Using default risk management console configuration")
            return default_config
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Merge with defaults for any missing keys
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            
            logger.info(f"Loaded risk management console configuration from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
            return default_config
    
    def update_positions(self, positions: Dict[str, Dict[str, Any]]) -> None:
        """
        Update portfolio positions.
        
        Args:
            positions: Dictionary mapping assets to position information
        """
        logger.info(f"Updating positions for {len(positions)} assets")
        
        # Store positions with timestamp
        timestamp = datetime.datetime.now().isoformat()
        self.historical_data["positions"][timestamp] = positions
        
        # Clean up old data
        retention_days = self.config.get("historical_data_retention_days", 90)
        cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=retention_days)).isoformat()
        
        self.historical_data["positions"] = {
            ts: pos for ts, pos in self.historical_data["positions"].items() if ts >= cutoff_date
        }
    
    def update_returns(self, returns: Dict[str, np.ndarray]) -> None:
        """
        Update historical returns data.
        
        Args:
            returns: Dictionary mapping assets to historical returns
        """
        logger.info(f"Updating returns data for {len(returns)} assets")
        
        # Store returns with timestamp
        timestamp = datetime.datetime.now().isoformat()
        
        # Convert numpy arrays to lists for storage
        returns_dict = {asset: returns_array.tolist() for asset, returns_array in returns.items()}
        self.historical_data["returns"][timestamp] = returns_dict
        
        # Clean up old data
        retention_days = self.config.get("historical_data_retention_days", 90)
        cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=retention_days)).isoformat()
        
        self.historical_data["returns"] = {
            ts: ret for ts, ret in self.historical_data["returns"].items() if ts >= cutoff_date
        }
    
    def analyze_risk(self, positions: Optional[Dict[str, Dict[str, Any]]] = None,
                   returns: Optional[Dict[str, np.ndarray]] = None) -> Dict[str, Any]:
        """
        Analyze portfolio risk.
        
        Args:
            positions: Dictionary mapping assets to position information (optional)
            returns: Dictionary mapping assets to historical returns (optional)
            
        Returns:
            Risk analysis results
        """
        # Use provided data or latest from historical data
        if positions is None:
            if not self.historical_data["positions"]:
                raise ValueError("No position data available")
            latest_timestamp = max(self.historical_data["positions"].keys())
            positions = self.historical_data["positions"][latest_timestamp]
        
        if returns is None:
            if not self.historical_data["returns"]:
                raise ValueError("No returns data available")
            latest_timestamp = max(self.historical_data["returns"].keys())
            returns_dict = self.historical_data["returns"][latest_timestamp]
            returns = {asset: np.array(returns_array) for asset, returns_array in returns_dict.items()}
        
        logger.info("Analyzing portfolio risk")
        
        # Calculate risk metrics
        risk_metrics = self.risk_manager.calculate_portfolio_risk(positions, returns)
        
        # Check risk limits
        limit_checks = self.risk_manager.check_risk_limits(positions, risk_metrics)
        
        # Generate recommendations
        recommendations = self.risk_manager.generate_risk_recommendations(positions, risk_metrics, limit_checks)
        
        # Store results with timestamp
        timestamp = datetime.datetime.now().isoformat()
        self.historical_data["risk_metrics"][timestamp] = risk_metrics
        self.historical_data["limit_checks"][timestamp] = limit_checks
        
        # Clean up old data
        retention_days = self.config.get("historical_data_retention_days", 90)
        cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=retention_days)).isoformat()
        
        self.historical_data["risk_metrics"] = {
            ts: metrics for ts, metrics in self.historical_data["risk_metrics"].items() if ts >= cutoff_date
        }
        
        self.historical_data["limit_checks"] = {
            ts: checks for ts, checks in self.historical_data["limit_checks"].items() if ts >= cutoff_date
        }
        
        # Check for alerts
        alerts = self._check_for_alerts(limit_checks)
        
        # Compile analysis results
        analysis_results = {
            "timestamp": timestamp,
            "risk_metrics": risk_metrics,
            "limit_checks": limit_checks,
            "recommendations": recommendations,
            "alerts": alerts
        }
        
        logger.info("Portfolio risk analysis completed")
        return analysis_results
    
    def _check_for_alerts(self, limit_checks: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check for risk alerts based on limit checks.
        
        Args:
            limit_checks: Dictionary of risk limit checks
            
        Returns:
            List of alerts
        """
        alerts = []
        alert_thresholds = self.config.get("alert_thresholds", {})
        
        # VaR alert
        var_threshold = alert_thresholds.get("var_threshold", 0.8)
        var_check = limit_checks["var"]
        if var_check["percentage_of_limit"] >= var_threshold * 100:
            alerts.append({
                "type": "VAR_ALERT",
                "severity": "HIGH" if var_check["status"] == "EXCEEDED" else "MEDIUM",
                "description": f"VaR at {var_check['percentage_of_limit']:.1f}% of limit",
                "details": var_check
            })
        
        # Position alert
        position_threshold = alert_thresholds.get("position_threshold", 0.8)
        position_check = limit_checks["position"]
        if position_check["percentage_of_limit"] >= position_threshold * 100:
            alerts.append({
                "type": "POSITION_ALERT",
                "severity": "HIGH" if position_check["status"] == "EXCEEDED" else "MEDIUM",
                "description": f"Position in {position_check['asset']} at {position_check['percentage_of_limit']:.1f}% of limit",
                "details": position_check
            })
        
        # Concentration alert
        concentration_threshold = alert_thresholds.get("concentration_threshold", 0.8)
        concentration_check = limit_checks["concentration"]
        if concentration_check["percentage_of_limit"] >= concentration_threshold * 100:
            alerts.append({
                "type": "CONCENTRATION_ALERT",
                "severity": "HIGH" if concentration_check["status"] == "EXCEEDED" else "MEDIUM",
                "description": f"Concentration at {concentration_check['percentage_of_limit']:.1f}% of limit",
                "details": concentration_check
            })
        
        # Correlation alert
        correlation_threshold = alert_thresholds.get("correlation_threshold", 0.8)
        correlation_check = limit_checks["correlation"]
        if correlation_check["percentage_of_limit"] >= correlation_threshold * 100:
            alerts.append({
                "type": "CORRELATION_ALERT",
                "severity": "HIGH" if correlation_check["status"] == "EXCEEDED" else "MEDIUM",
                "description": f"Correlation between {correlation_check['assets'][0]} and {correlation_check['assets'][1]} at {correlation_check['percentage_of_limit']:.1f}% of limit",
                "details": correlation_check
            })
        
        # Drawdown alert
        drawdown_threshold = alert_thresholds.get("drawdown_threshold", 0.8)
        drawdown_check = limit_checks["drawdown"]
        if drawdown_check["percentage_of_limit"] >= drawdown_threshold * 100:
            alerts.append({
                "type": "DRAWDOWN_ALERT",
                "severity": "HIGH" if drawdown_check["status"] == "EXCEEDED" else "MEDIUM",
                "description": f"Drawdown at {drawdown_check['percentage_of_limit']:.1f}% of limit",
                "details": drawdown_check
            })
        
        # Stress test alerts
        for scenario_name, stress_check in limit_checks["stress_tests"].items():
            if stress_check["status"] == "EXCEEDED":
                alerts.append({
                    "type": "STRESS_TEST_ALERT",
                    "severity": "HIGH",
                    "description": f"{scenario_name} stress test exceeds limit",
                    "details": stress_check
                })
        
        # Send alerts if configured
        if alerts:
            self._send_alerts(alerts)
        
        return alerts
    
    def _send_alerts(self, alerts: List[Dict[str, Any]]) -> None:
        """
        Send alerts through configured channels.
        
        Args:
            alerts: List of alerts
        """
        alert_channels = self.config.get("alert_channels", ["console"])
        
        for channel in alert_channels:
            if channel == "console":
                for alert in alerts:
                    logger.warning(f"RISK ALERT: {alert['description']} (Severity: {alert['severity']})")
            elif channel == "email":
                # In a real implementation, this would send email alerts
                # This is a placeholder
                recipients = self.config.get("email_recipients", [])
                if recipients:
                    logger.info(f"Would send {len(alerts)} email alerts to {len(recipients)} recipients")
            elif channel == "sms":
                # In a real implementation, this would send SMS alerts
                # This is a placeholder
                recipients = self.config.get("sms_recipients", [])
                if recipients:
                    logger.info(f"Would send {len(alerts)} SMS alerts to {len(recipients)} recipients")
    
    def optimize_portfolio(self, target_risk: Optional[float] = None) -> Dict[str, Any]:
        """
        Optimize portfolio to achieve target risk level or maximize risk-adjusted returns.
        
        Args:
            target_risk: Target risk level (volatility) (optional)
            
        Returns:
            Optimization results
        """
        # Get latest data
        if not self.historical_data["positions"] or not self.historical_data["returns"]:
            raise ValueError("No position or returns data available")
        
        latest_positions_timestamp = max(self.historical_data["positions"].keys())
        positions = self.historical_data["positions"][latest_positions_timestamp]
        
        latest_returns_timestamp = max(self.historical_data["returns"].keys())
        returns_dict = self.historical_data["returns"][latest_returns_timestamp]
        returns = {asset: np.array(returns_array) for asset, returns_array in returns_dict.items()}
        
        latest_metrics_timestamp = max(self.historical_data["risk_metrics"].keys())
        risk_metrics = self.historical_data["risk_metrics"][latest_metrics_timestamp]
        
        logger.info(f"Optimizing portfolio{' for target risk ' + str(target_risk) if target_risk else ''}")
        
        # Optimize portfolio
        optimization_result = self.risk_manager.optimize_portfolio(positions, returns, risk_metrics, target_risk)
        
        logger.info("Portfolio optimization completed")
        return optimization_result
    
    def run_stress_test(self, scenario_name: str) -> Dict[str, Any]:
        """
        Run a specific stress test on the portfolio.
        
        Args:
            scenario_name: Name of the stress test scenario
            
        Returns:
            Stress test results
        """
        # Check if scenario exists
        if scenario_name not in self.risk_manager.scenarios:
            raise ValueError(f"Stress test scenario not found: {scenario_name}")
        
        # Get latest data
        if not self.historical_data["positions"] or not self.historical_data["returns"]:
            raise ValueError("No position or returns data available")
        
        latest_positions_timestamp = max(self.historical_data["positions"].keys())
        positions = self.historical_data["positions"][latest_positions_timestamp]
        
        latest_returns_timestamp = max(self.historical_data["returns"].keys())
        returns_dict = self.historical_data["returns"][latest_returns_timestamp]
        returns = {asset: np.array(returns_array) for asset, returns_array in returns_dict.items()}
        
        # Get scenario
        scenario = self.risk_manager.scenarios[scenario_name]
        
        logger.info(f"Running stress test: {scenario_name}")
        
        # Create returns matrix
        assets = list(positions.keys())
        returns_matrix = np.column_stack([returns.get(asset, np.zeros(1)) for asset in assets])
        
        # Run stress test
        stress_test_result = self.risk_manager.calculator.run_stress_test(returns_matrix, positions, scenario)
        
        logger.info(f"Stress test completed: {scenario_name}")
        return stress_test_result
    
    def get_risk_dashboard_data(self) -> Dict[str, Any]:
        """
        Get data for the risk management dashboard.
        
        Returns:
            Dashboard data
        """
        # Check if data is available
        if not self.historical_data["risk_metrics"] or not self.historical_data["limit_checks"]:
            raise ValueError("No risk metrics or limit checks available")
        
        logger.info("Getting risk dashboard data")
        
        # Get latest data
        latest_metrics_timestamp = max(self.historical_data["risk_metrics"].keys())
        risk_metrics = self.historical_data["risk_metrics"][latest_metrics_timestamp]
        
        latest_checks_timestamp = max(self.historical_data["limit_checks"].keys())
        limit_checks = self.historical_data["limit_checks"][latest_checks_timestamp]
        
        latest_positions_timestamp = max(self.historical_data["positions"].keys())
        positions = self.historical_data["positions"][latest_positions_timestamp]
        
        # Get historical metrics for time series
        historical_metrics = {}
        for timestamp, metrics in sorted(self.historical_data["risk_metrics"].items())[-30:]:  # Last 30 data points
            date = datetime.datetime.fromisoformat(timestamp).strftime("%Y-%m-%d")
            if date not in historical_metrics:
                historical_metrics[date] = {
                    "var": metrics["var"],
                    "volatility": metrics["volatility"],
                    "sharpe_ratio": metrics["sharpe_ratio"]
                }
        
        # Generate dashboard data
        dashboard_sections = self.config.get("dashboard_sections", [])
        dashboard_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "sections": {}
        }
        
        # Risk overview section
        if "risk_overview" in dashboard_sections:
            dashboard_data["sections"]["risk_overview"] = {
                "var": risk_metrics["var"],
                "cvar": risk_metrics["cvar"],
                "volatility": risk_metrics["volatility"],
                "sharpe_ratio": risk_metrics["sharpe_ratio"],
                "sortino_ratio": risk_metrics["sortino_ratio"],
                "max_drawdown": risk_metrics["max_drawdown"],
                "overall_status": limit_checks["overall_status"],
                "historical_metrics": historical_metrics
            }
        
        # Position risk section
        if "position_risk" in dashboard_sections:
            dashboard_data["sections"]["position_risk"] = {
                "concentration": risk_metrics["concentration"],
                "position_limit_check": limit_checks["position"],
                "concentration_limit_check": limit_checks["concentration"],
                "positions": positions
            }
        
        # Market risk section
        if "market_risk" in dashboard_sections:
            dashboard_data["sections"]["market_risk"] = {
                "correlation": risk_metrics["correlation"],
                "correlation_limit_check": limit_checks["correlation"]
            }
        
        # Stress tests section
        if "stress_tests" in dashboard_sections:
            dashboard_data["sections"]["stress_tests"] = {
                "stress_tests": risk_metrics["stress_tests"],
                "stress_test_limit_checks": limit_checks["stress_tests"]
            }
        
        # Optimization section
        if "optimization" in dashboard_sections:
            # Run optimization
            try:
                optimization_result = self.optimize_portfolio()
                dashboard_data["sections"]["optimization"] = optimization_result
            except Exception as e:
                logger.error(f"Error running optimization for dashboard: {e}")
                dashboard_data["sections"]["optimization"] = {"error": str(e)}
        
        logger.info("Generated risk dashboard data")
        return dashboard_data


if __name__ == "__main__":
    # Example usage
    console = RiskManagementConsole()
    
    # Create sample positions
    positions = {
        "BTC": {
            "quantity": 100.0,
            "price": 55000.0,
            "value": 5500000.0
        },
        "ETH": {
            "quantity": 1000.0,
            "price": 3500.0,
            "value": 3500000.0
        },
        "SOL": {
            "quantity": 5000.0,
            "price": 200.0,
            "value": 1000000.0
        }
    }
    
    # Create sample returns (random for this example)
    np.random.seed(42)  # For reproducibility
    returns = {
        "BTC": np.random.normal(0.001, 0.03, 252),
        "ETH": np.random.normal(0.001, 0.04, 252),
        "SOL": np.random.normal(0.002, 0.05, 252)
    }
    
    # Update data
    console.update_positions(positions)
    console.update_returns(returns)
    
    # Analyze risk
    analysis = console.analyze_risk()
    print("Risk Analysis:")
    print(f"VaR: {analysis['risk_metrics']['var']:.2%}")
    print(f"Volatility: {analysis['risk_metrics']['volatility']:.2%}")
    print(f"Sharpe Ratio: {analysis['risk_metrics']['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {analysis['risk_metrics']['max_drawdown']:.2%}")
    print(f"Overall Status: {analysis['limit_checks']['overall_status']}")
    
    if analysis['alerts']:
        print("\nAlerts:")
        for alert in analysis['alerts']:
            print(f"- {alert['description']} (Severity: {alert['severity']})")
    
    if analysis['recommendations']:
        print("\nRecommendations:")
        for recommendation in analysis['recommendations']:
            print(f"- {recommendation['description']}")
            print(f"  Action: {recommendation['action']}")
    
    # Run stress test
    stress_test = console.run_stress_test("market_crash_2008")
    print("\nStress Test (Market Crash 2008):")
    print(f"Loss: {stress_test['loss']:.2f} ({stress_test['loss_percentage']:.2%})")
    
    # Optimize portfolio
    optimization = console.optimize_portfolio()
    print("\nPortfolio Optimization:")
    print("Optimized Weights:")
    for asset, weight in optimization["optimized_weights"].items():
        print(f"- {asset}: {weight:.2%}")
    print(f"Expected Volatility: {optimization['expected_metrics']['volatility']:.2%}")
    print(f"Expected Sharpe Ratio: {optimization['expected_metrics']['sharpe_ratio']:.2f}")