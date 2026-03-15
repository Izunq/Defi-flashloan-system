#!/usr/bin/env python3
"""
Direct MATLAB Test - Simplified approach
Testing MATLAB functionality directly with basic commands
"""

import subprocess
import os
from pathlib import Path

def test_matlab_direct():
    """Test MATLAB with direct commands"""
    matlab_path = r"C:\Program Files\MATLAB\R2025a\bin\matlab.exe"
    
    print("="*60)
    print("DIRECT MATLAB FUNCTIONALITY TEST")
    print("="*60)
    
    # Test 1: Basic MATLAB execution
    print("\nTest 1: Basic MATLAB Version Check")
    try:
        result = subprocess.run([
            matlab_path,
            '-batch', 
            'disp("MATLAB is working!"); version; exit;'
        ], 
        capture_output=True, 
        text=True, 
        timeout=60)
        
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Errors: {result.stderr}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Basic Math Operations
    print("\nTest 2: Basic Math Operations")
    try:
        result = subprocess.run([
            matlab_path,
            '-batch', 
            'x = [1, 2, 3, 4, 5]; y = mean(x); fprintf("Mean: %.2f\\n", y); exit;'
        ], 
        capture_output=True, 
        text=True, 
        timeout=60)
        
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Errors: {result.stderr}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Toolbox Detection
    print("\nTest 3: Toolbox Detection")
    try:
        matlab_cmd = """
        toolboxes = ver;
        fprintf('Available Toolboxes:\\n');
        for i = 1:length(toolboxes)
            fprintf('  %s - %s\\n', toolboxes(i).Name, toolboxes(i).Version);
        end
        exit;
        """
        
        result = subprocess.run([
            matlab_path,
            '-batch', 
            matlab_cmd
        ], 
        capture_output=True, 
        text=True, 
        timeout=60)
        
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Errors: {result.stderr}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: Financial Functions Test
    print("\nTest 4: Financial Functions Test")
    try:
        matlab_cmd = """
        try
            % Test basic financial calculations
            fprintf('Testing financial calculations...\\n');
            
            % Simple interest calculation
            principal = 1000;
            rate = 0.05;
            time = 2;
            simple_interest = principal * rate * time;
            fprintf('Simple Interest: %.2f\\n', simple_interest);
            
            % Moving average
            prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109];
            ma5 = movmean(prices, 5);
            fprintf('5-period moving average (last value): %.2f\\n', ma5(end));
            
            % Check if Financial Toolbox is available
            if exist('blsprice', 'file')
                fprintf('Financial Toolbox detected - blsprice function available\\n');
            else
                fprintf('Financial Toolbox not detected\\n');
            end
            
        catch ME
            fprintf('Error in financial calculations: %s\\n', ME.message);
        end
        exit;
        """
        
        result = subprocess.run([
            matlab_path,
            '-batch', 
            matlab_cmd
        ], 
        capture_output=True, 
        text=True, 
        timeout=60)
        
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Errors: {result.stderr}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 5: Strategy Development Template
    print("\nTest 5: Strategy Development Template")
    try:
        matlab_cmd = """
        try
            fprintf('Developing basic arbitrage strategy...\\n');
            
            % Generate sample price data
            n = 100;
            prices = 100 + cumsum(0.01 * randn(n, 1));
            
            % Calculate returns
            returns = diff(log(prices));
            
            % Basic statistics
            mean_return = mean(returns);
            std_return = std(returns);
            sharpe_ratio = mean_return / std_return * sqrt(252);
            
            fprintf('Strategy Statistics:\\n');
            fprintf('  Mean Return: %.6f\\n', mean_return);
            fprintf('  Volatility: %.6f\\n', std_return);
            fprintf('  Sharpe Ratio: %.4f\\n', sharpe_ratio);
            
            % Simple moving average strategy
            short_ma = movmean(prices, 5);
            long_ma = movmean(prices, 20);
            
            signals = short_ma > long_ma;
            signal_changes = diff([0; signals]);
            buy_signals = sum(signal_changes == 1);
            sell_signals = sum(signal_changes == -1);
            
            fprintf('  Buy Signals: %d\\n', buy_signals);
            fprintf('  Sell Signals: %d\\n', sell_signals);
            
            fprintf('Strategy development template completed successfully!\\n');
            
        catch ME
            fprintf('Error in strategy development: %s\\n', ME.message);
        end
        exit;
        """
        
        result = subprocess.run([
            matlab_path,
            '-batch', 
            matlab_cmd
        ], 
        capture_output=True, 
        text=True, 
        timeout=60)
        
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Errors: {result.stderr}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "="*60)
    print("DIRECT MATLAB TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_matlab_direct()
