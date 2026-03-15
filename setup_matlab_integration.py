#!/usr/bin/env python3
"""
🧮 MATLAB Integration Setup for DeFi Arbitrage System
Complete setup and testing of MATLAB Engine integration
"""

import os
import sys
import subprocess
from pathlib import Path

def check_matlab_installation():
    """Check if MATLAB is installed"""
    print("🔍 Checking MATLAB installation...")
    
    # Common MATLAB installation paths
    matlab_paths = [
        r"C:\Program Files\MATLAB",
        r"C:\Program Files (x86)\MATLAB",
        "/usr/local/MATLAB",  # Linux
        "/Applications/MATLAB_R*.app"  # macOS
    ]
    
    for path in matlab_paths:
        if os.path.exists(path):
            print(f"✅ MATLAB found at: {path}")
            return True
    
    print("❌ MATLAB not found on system")
    print("💡 Install MATLAB from MathWorks or use campus license")
    return False

def test_matlab_engine():
    """Test MATLAB Engine for Python"""
    print("\n🔧 Testing MATLAB Engine...")
    
    try:
        import matlab.engine
        print("✅ MATLAB Engine module available")
        
        # Start MATLAB
        print("🚀 Starting MATLAB engine...")
        eng = matlab.engine.start_matlab()
        
        # Test basic functionality
        result = eng.sqrt(16.0)
        print(f"✅ Basic test: sqrt(16) = {result}")
        
        # Test matrix operations
        import matlab
        test_matrix = matlab.double([[1, 2], [3, 4]])
        det_result = eng.det(test_matrix)
        print(f"✅ Matrix test: det([[1,2],[3,4]]) = {det_result}")
        
        # Close MATLAB
        eng.quit()
        print("✅ MATLAB Engine: FULLY OPERATIONAL!")
        return True
        
    except ImportError:
        print("❌ MATLAB Engine not installed")
        print("📋 Installation steps:")
        print("   1. Open MATLAB")
        print("   2. Run: cd(fullfile(matlabroot,'extern','engines','python'))")
        print("   3. Run: system('python setup.py install')")
        return False
    except Exception as e:
        print(f"❌ MATLAB Engine error: {e}")
        return False

def setup_arbitrage_matlab_models():
    """Setup MATLAB models for arbitrage"""
    print("\n📊 Setting up arbitrage MATLAB models...")
    
    models_dir = Path("matlab/arbitrage_models")
    models_dir.mkdir(exist_ok=True)
    
    # Portfolio optimization model
    portfolio_optimizer = """function [optimal_weights, expected_return, risk] = portfolio_optimization(returns_data, risk_tolerance, max_positions)
    % Advanced Portfolio Optimization for DeFi Arbitrage
    % 
    % Inputs:
    %   returns_data - Historical returns matrix (time x assets)
    %   risk_tolerance - Risk tolerance parameter (0-1)
    %   max_positions - Maximum number of positions
    %
    % Outputs:
    %   optimal_weights - Optimal portfolio weights
    %   expected_return - Expected portfolio return
    %   risk - Portfolio risk (standard deviation)
    
    [T, N] = size(returns_data);
    
    % Calculate expected returns and covariance matrix
    mu = mean(returns_data)';
    Sigma = cov(returns_data);
    
    % Setup optimization problem
    H = 2 * Sigma;  % Quadratic term (risk)
    f = -risk_tolerance * mu;  % Linear term (return)
    
    % Constraints
    Aeq = ones(1, N);  % Sum of weights = 1
    beq = 1;
    
    % Bounds: weights between 0 and 1/max_positions
    lb = zeros(N, 1);
    ub = (1/max_positions) * ones(N, 1);
    
    % Additional constraint: at most max_positions non-zero weights
    A = [];
    b = [];
    
    % Solve quadratic programming problem
    options = optimoptions('quadprog', 'Display', 'off');
    [optimal_weights, fval] = quadprog(H, f, A, b, Aeq, beq, lb, ub, [], options);
    
    % Calculate portfolio metrics
    expected_return = mu' * optimal_weights;
    risk = sqrt(optimal_weights' * Sigma * optimal_weights);
    
    % Apply sparsity constraint (keep only top max_positions)
    [~, idx] = sort(optimal_weights, 'descend');
    sparse_weights = zeros(N, 1);
    sparse_weights(idx(1:max_positions)) = optimal_weights(idx(1:max_positions));
    
    % Renormalize
    optimal_weights = sparse_weights / sum(sparse_weights);
    expected_return = mu' * optimal_weights;
    risk = sqrt(optimal_weights' * Sigma * optimal_weights);
end"""
    
    with open(models_dir / "portfolio_optimization.m", "w") as f:
        f.write(portfolio_optimizer)
    
    # Arbitrage opportunity detector
    arbitrage_detector = """function [opportunities, profit_estimates] = detect_arbitrage_opportunities(price_data, exchanges, threshold)
    % Detect Cross-Exchange Arbitrage Opportunities
    %
    % Inputs:
    %   price_data - Price matrix (time x exchanges)
    %   exchanges - Cell array of exchange names
    %   threshold - Minimum profit threshold (e.g., 0.02 for 2%)
    %
    % Outputs:
    %   opportunities - Binary matrix indicating opportunities
    %   profit_estimates - Estimated profit for each opportunity
    
    [T, E] = size(price_data);
    opportunities = zeros(T, E, E);  % Time x Exchange1 x Exchange2
    profit_estimates = zeros(T, E, E);
    
    for t = 1:T
        current_prices = price_data(t, :);
        
        for i = 1:E
            for j = 1:E
                if i ~= j
                    % Calculate potential profit: buy on i, sell on j
                    buy_price = current_prices(i);
                    sell_price = current_prices(j);
                    
                    if buy_price > 0 && sell_price > 0
                        profit_rate = (sell_price - buy_price) / buy_price;
                        
                        if profit_rate > threshold
                            opportunities(t, i, j) = 1;
                            profit_estimates(t, i, j) = profit_rate;
                        end
                    end
                end
            end
        end
    end
    
    % Summary statistics
    total_opportunities = sum(opportunities, 'all');
    avg_profit = mean(profit_estimates(profit_estimates > 0));
    
    fprintf('Arbitrage Analysis Summary:\\n');
    fprintf('Total opportunities found: %d\\n', total_opportunities);
    fprintf('Average profit rate: %.4f (%.2f%%)\\n', avg_profit, avg_profit * 100);
end"""
    
    with open(models_dir / "detect_arbitrage_opportunities.m", "w") as f:
        f.write(arbitrage_detector)
    
    print("✅ MATLAB arbitrage models created")
    print(f"   📁 Models directory: {models_dir}")
    print("   📊 portfolio_optimization.m")
    print("   🔍 detect_arbitrage_opportunities.m")

def create_matlab_integration_bridge():
    """Create Python-MATLAB integration bridge"""
    print("\n🌉 Creating MATLAB integration bridge...")
    
    bridge_code = '''"""
MATLAB Integration Bridge for DeFi Arbitrage System
Provides seamless integration between Python arbitrage system and MATLAB analytics
"""

import matlab.engine
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class MATLABArbitrageEngine:
    """Advanced MATLAB integration for arbitrage analytics"""
    
    def __init__(self):
        self.eng = None
        self.connect()
    
    def connect(self):
        """Connect to MATLAB engine"""
        try:
            logger.info("Starting MATLAB engine...")
            self.eng = matlab.engine.start_matlab()
            
            # Add model paths
            self.eng.addpath('matlab/arbitrage_models/', nargout=0)
            self.eng.addpath('matlab/', nargout=0)
            
            logger.info("✅ MATLAB engine connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to MATLAB: {e}")
            raise
    
    def optimize_portfolio(self, returns_data: np.ndarray, 
                          risk_tolerance: float = 0.5,
                          max_positions: int = 10) -> Dict:
        """
        Optimize portfolio using MATLAB advanced algorithms
        
        Args:
            returns_data: Historical returns matrix (time x assets)
            risk_tolerance: Risk tolerance (0-1, higher = more aggressive)
            max_positions: Maximum number of positions
            
        Returns:
            Dictionary with optimal_weights, expected_return, risk
        """
        try:
            # Convert to MATLAB format
            matlab_returns = matlab.double(returns_data.tolist())
            
            # Run optimization
            result = self.eng.portfolio_optimization(
                matlab_returns,
                float(risk_tolerance),
                int(max_positions),
                nargout=3
            )
            
            return {
                'optimal_weights': np.array(result[0]).flatten(),
                'expected_return': float(result[1]),
                'risk': float(result[2])
            }
            
        except Exception as e:
            logger.error(f"Portfolio optimization failed: {e}")
            raise
    
    def detect_arbitrage(self, price_data: np.ndarray, 
                        exchanges: List[str],
                        threshold: float = 0.02) -> Dict:
        """
        Detect arbitrage opportunities using MATLAB
        
        Args:
            price_data: Price matrix (time x exchanges)
            exchanges: List of exchange names
            threshold: Minimum profit threshold
            
        Returns:
            Dictionary with opportunities and profit estimates
        """
        try:
            # Convert to MATLAB format
            matlab_prices = matlab.double(price_data.tolist())
            matlab_exchanges = matlab.cellstr(exchanges)
            
            # Run arbitrage detection
            result = self.eng.detect_arbitrage_opportunities(
                matlab_prices,
                matlab_exchanges,
                float(threshold),
                nargout=2
            )
            
            return {
                'opportunities': np.array(result[0]),
                'profit_estimates': np.array(result[1])
            }
            
        except Exception as e:
            logger.error(f"Arbitrage detection failed: {e}")
            raise
    
    def close(self):
        """Close MATLAB engine"""
        if self.eng:
            self.eng.quit()
            logger.info("MATLAB engine closed")

# Global MATLAB engine instance
matlab_engine = None

def get_matlab_engine():
    """Get or create MATLAB engine instance"""
    global matlab_engine
    if matlab_engine is None:
        matlab_engine = MATLABArbitrageEngine()
    return matlab_engine

def matlab_portfolio_optimization(returns_data: pd.DataFrame, 
                                 risk_tolerance: float = 0.5) -> Dict:
    """Convenient wrapper for portfolio optimization"""
    engine = get_matlab_engine()
    return engine.optimize_portfolio(
        returns_data.values, 
        risk_tolerance=risk_tolerance
    )

def matlab_arbitrage_scan(price_data: pd.DataFrame, 
                         threshold: float = 0.02) -> Dict:
    """Convenient wrapper for arbitrage detection"""
    engine = get_matlab_engine()
    exchanges = list(price_data.columns)
    return engine.detect_arbitrage(
        price_data.values,
        exchanges=exchanges,
        threshold=threshold
    )
'''
    
    with open("matlab/matlab_arbitrage_bridge.py", "w") as f:
        f.write(bridge_code)
    
    print("✅ MATLAB integration bridge created")
    print("   📁 File: matlab/matlab_arbitrage_bridge.py")

def main():
    """Main setup function"""
    print("🧮 MATLAB INTEGRATION SETUP FOR DEFI ARBITRAGE")
    print("=" * 50)
    
    # Check MATLAB installation
    if not check_matlab_installation():
        return False
    
    # Test MATLAB Engine
    if not test_matlab_engine():
        return False
    
    # Setup models and bridge
    setup_arbitrage_matlab_models()
    create_matlab_integration_bridge()
    
    print("\n🎉 MATLAB INTEGRATION SETUP COMPLETE!")
    print("=" * 50)
    print("✅ MATLAB Engine: Operational")
    print("✅ Arbitrage Models: Created")
    print("✅ Python Bridge: Ready")
    print("\n📋 Next Steps:")
    print("1. Test integration: python -c 'from matlab.matlab_arbitrage_bridge import get_matlab_engine; get_matlab_engine()'")
    print("2. Run portfolio optimization with your data")
    print("3. Setup SPSS and NVivo integrations")
    
    return True

if __name__ == "__main__":
    main()
