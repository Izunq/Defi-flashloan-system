#!/usr/bin/env python3
"""
Direct MATLAB Strategy Execution with Immediate Output
"""

import subprocess
import pandas as pd
import numpy as np
from pathlib import Path

def create_direct_matlab_strategy():
    """Create a MATLAB strategy that produces immediate output"""
    
    # First, create test data
    np.random.seed(42)
    
    # Generate realistic arbitrage data
    n = 100
    price_spreads = np.maximum(0.0001, np.random.normal(0.003, 0.001, n))
    volatility = np.random.exponential(0.02, n)
    gas_costs = np.random.lognormal(np.log(0.01), 0.3, n)
    liquidity = np.random.beta(2, 2, n)
    profits = price_spreads * 1000 - gas_costs * 100 + np.random.normal(0, 0.5, n)
    
    df = pd.DataFrame({
        'price_spread': price_spreads,
        'volatility': volatility,
        'gas_cost': gas_costs,
        'liquidity_score': liquidity,
        'profit': profits
    })
    
    df.to_csv('arbitrage_data.csv', index=False)
    print(f"Created test data: {len(df)} opportunities")
    print(f"Profitable: {(df['profit'] > 0).sum()} ({(df['profit'] > 0).mean()*100:.1f}%)")
    
    # Create simple MATLAB strategy
    matlab_code = """
% Direct MATLAB Arbitrage Strategy Execution
fprintf('\\n=== MATLAB ARBITRAGE STRATEGY ANALYSIS ===\\n');

% Load data
try
    data = readtable('arbitrage_data.csv');
    fprintf('Data loaded successfully: %d opportunities\\n', height(data));
    
    % Extract variables
    spreads = data.price_spread;
    profits = data.profit;
    volatility = data.volatility;
    
    % Strategy 1: Simple Mean Reversion
    fprintf('\\n--- Mean Reversion Strategy ---\\n');
    window = 20;
    spread_mean = movmean(spreads, window);
    spread_std = movstd(spreads, window);
    z_scores = (spreads - spread_mean) ./ (spread_std + 1e-8);
    
    % Signals: buy when underpriced, sell when overpriced
    mr_signals = zeros(size(z_scores));
    mr_signals(z_scores > 1.5) = -1;  % Sell signal
    mr_signals(z_scores < -1.5) = 1;  % Buy signal
    
    % Calculate returns
    mr_returns = mr_signals .* profits;
    mr_trades = sum(mr_signals ~= 0);
    mr_total_return = sum(mr_returns);
    mr_win_rate = sum(mr_returns > 0) / mr_trades * 100;
    
    fprintf('Mean Reversion Results:\\n');
    fprintf('  Total Trades: %d\\n', mr_trades);
    fprintf('  Total Return: $%.2f\\n', mr_total_return);
    fprintf('  Win Rate: %.1f%%\\n', mr_win_rate);
    
    % Strategy 2: Volatility-Based
    fprintf('\\n--- Volatility Strategy ---\\n');
    vol_threshold = prctile(volatility, 75); % Top 25% volatility
    vol_signals = zeros(size(volatility));
    vol_signals(volatility > vol_threshold & profits > 0) = 1;
    
    vol_returns = vol_signals .* profits;
    vol_trades = sum(vol_signals > 0);
    vol_total_return = sum(vol_returns);
    vol_win_rate = sum(vol_returns > 0) / vol_trades * 100;
    
    fprintf('Volatility Strategy Results:\\n');
    fprintf('  Total Trades: %d\\n', vol_trades);
    fprintf('  Total Return: $%.2f\\n', vol_total_return);
    fprintf('  Win Rate: %.1f%%\\n', vol_win_rate);
    
    % Combined Portfolio
    fprintf('\\n--- Combined Portfolio ---\\n');
    combined_returns = (mr_returns + vol_returns) / 2;
    combined_trades = sum((mr_signals ~= 0) | (vol_signals > 0));
    combined_total = sum(combined_returns);
    combined_win_rate = sum(combined_returns > 0) / combined_trades * 100;
    
    fprintf('Portfolio Results:\\n');
    fprintf('  Total Return: $%.2f\\n', combined_total);
    fprintf('  Win Rate: %.1f%%\\n', combined_win_rate);
    
    % Current Recommendation
    fprintf('\\n--- Current Market Signal ---\\n');
    current_z = z_scores(end);
    current_vol = volatility(end);
    
    if current_z > 1.5
        recommendation = 'SELL - Overpriced';
    elseif current_z < -1.5
        recommendation = 'BUY - Underpriced';
    elseif current_vol > vol_threshold
        recommendation = 'MONITOR - High Volatility';
    else
        recommendation = 'HOLD - Wait for Signal';
    end
    
    fprintf('Current Z-Score: %.2f\\n', current_z);
    fprintf('Current Volatility: %.4f\\n', current_vol);
    fprintf('RECOMMENDATION: %s\\n', recommendation);
    
    % Write results to file
    fid = fopen('matlab_strategy_results.txt', 'w');
    fprintf(fid, 'MATLAB ARBITRAGE STRATEGY RESULTS\\n');
    fprintf(fid, '=================================\\n\\n');
    fprintf(fid, 'Mean Reversion Strategy:\\n');
    fprintf(fid, '  Trades: %d\\n', mr_trades);
    fprintf(fid, '  Return: $%.2f\\n', mr_total_return);
    fprintf(fid, '  Win Rate: %.1f%%\\n\\n', mr_win_rate);
    fprintf(fid, 'Volatility Strategy:\\n');
    fprintf(fid, '  Trades: %d\\n', vol_trades);
    fprintf(fid, '  Return: $%.2f\\n', vol_total_return);
    fprintf(fid, '  Win Rate: %.1f%%\\n\\n', vol_win_rate);
    fprintf(fid, 'Portfolio Return: $%.2f\\n', combined_total);
    fprintf(fid, 'Current Recommendation: %s\\n', recommendation);
    fclose(fid);
    
    fprintf('\\nResults saved to: matlab_strategy_results.txt\\n');
    fprintf('\\n=== ANALYSIS COMPLETE ===\\n');
    
catch ME
    fprintf('ERROR: %s\\n', ME.message);
end

exit;
"""
    
    with open('direct_matlab_strategy.m', 'w') as f:
        f.write(matlab_code)
    
    print("MATLAB strategy script created: direct_matlab_strategy.m")
    return 'direct_matlab_strategy.m'

def run_direct_matlab():
    """Run MATLAB strategy directly"""
    matlab_path = r"C:\Program Files\MATLAB\R2025a\bin\matlab.exe"
    
    # Create strategy
    script_file = create_direct_matlab_strategy()
    
    print("\n" + "="*50)
    print("EXECUTING MATLAB ARBITRAGE STRATEGY")
    print("="*50)
    
    # Run MATLAB
    result = subprocess.run([
        matlab_path, "-r", f"run('{script_file}')"
    ], capture_output=True, text=True, timeout=120)
    
    print(f"MATLAB Return Code: {result.returncode}")
    
    if result.stdout:
        print("\nMATLAB Output:")
        print(result.stdout)
    
    if result.stderr:
        print("\nMATLAB Errors/Warnings:")
        print(result.stderr)
    
    # Check for results file
    results_file = Path('matlab_strategy_results.txt')
    if results_file.exists():
        print("\n" + "="*50)
        print("MATLAB STRATEGY RESULTS")
        print("="*50)
        with open(results_file) as f:
            print(f.read())
        return True
    else:
        print("No results file generated")
        return False

if __name__ == "__main__":
    run_direct_matlab()
