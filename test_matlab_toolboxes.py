#!/usr/bin/env python3
"""
MATLAB Toolbox Verification
Test which MATLAB toolboxes are actually available and working
"""

import subprocess
from pathlib import Path

def test_matlab_toolboxes():
    matlab_path = r"C:\Program Files\MATLAB\R2025a\bin\matlab.exe"
    
    # Create a simple MATLAB test script
    matlab_test = """
fprintf('MATLAB Toolbox Verification Test\\n');
fprintf('================================\\n');

% Test basic MATLAB
fprintf('\\nBasic MATLAB: ');
try
    a = [1 2 3; 4 5 6];
    b = mean(a);
    fprintf('WORKING (mean result: %s)\\n', mat2str(b));
catch ME
    fprintf('FAILED: %s\\n', ME.message);
end

% Test Financial Toolbox
fprintf('Financial Toolbox: ');
try
    if license('test', 'Financial_Toolbox')
        % Test Black-Scholes
        [call, put] = blsprice(100, 100, 0.05, 0.25, 0.2);
        fprintf('AVAILABLE (call=%.2f, put=%.2f)\\n', call, put);
    else
        fprintf('NOT LICENSED\\n');
    end
catch ME
    fprintf('FAILED: %s\\n', ME.message);
end

% Test Econometrics Toolbox
fprintf('Econometrics Toolbox: ');
try
    if license('test', 'Econometrics_Toolbox')
        % Test GARCH
        model = garch(1,1);
        fprintf('AVAILABLE (GARCH model created)\\n');
    else
        fprintf('NOT LICENSED\\n');
    end
catch ME
    fprintf('FAILED: %s\\n', ME.message);
end

% Test Statistics Toolbox
fprintf('Statistics Toolbox: ');
try
    if license('test', 'Statistics_Toolbox')
        % Test distribution fitting
        data = randn(100,1);
        pd = fitdist(data, 'Normal');
        fprintf('AVAILABLE (normal dist fitted)\\n');
    else
        fprintf('NOT LICENSED\\n');
    end
catch ME
    fprintf('FAILED: %s\\n', ME.message);
end

% Test Optimization Toolbox
fprintf('Optimization Toolbox: ');
try
    if license('test', 'Optimization_Toolbox')
        fprintf('AVAILABLE\\n');
    else
        fprintf('NOT LICENSED\\n');
    end
catch ME
    fprintf('FAILED: %s\\n', ME.message);
end

% Test some financial functions
fprintf('\\nTesting Financial Functions:\\n');
fprintf('----------------------------\\n');

% Test technical analysis
fprintf('Technical Analysis: ');
try
    prices = 100 + cumsum(randn(50,1));
    sma = movavg(prices, 'simple', 10);
    fprintf('WORKING (SMA calculated)\\n');
catch ME
    fprintf('FAILED: %s\\n', ME.message);
end

% Test Bollinger Bands
fprintf('Bollinger Bands: ');
try
    prices = 100 + cumsum(randn(50,1));
    [mid, upper, lower] = bollinger(prices, 20, 2);
    fprintf('WORKING\\n');
catch ME
    fprintf('FAILED: %s\\n', ME.message);
end

% Test RSI
fprintf('RSI Indicator: ');
try
    prices = 100 + cumsum(randn(50,1));
    rsi_val = rsindex(prices);
    fprintf('WORKING (RSI=%.2f)\\n', rsi_val(end));
catch ME
    fprintf('FAILED: %s\\n', ME.message);
end

% Test MACD
fprintf('MACD Indicator: ');
try
    prices = 100 + cumsum(randn(50,1));
    [macd_line, signal_line, histogram] = macd(prices);
    fprintf('WORKING\\n');
catch ME
    fprintf('FAILED: %s\\n', ME.message);
end

fprintf('\\nTest Complete!\\n');
exit;
"""
    
    # Save test script
    test_file = Path("matlab_toolbox_test.m")
    with open(test_file, 'w') as f:
        f.write(matlab_test)
    
    print("Testing MATLAB Toolboxes...")
    print("="*40)
    
    # Run MATLAB test
    result = subprocess.run([
        matlab_path, "-r", f"run('{test_file.resolve()}');"
    ], capture_output=True, text=True, timeout=60)
    
    print(f"Return Code: {result.returncode}")
    
    if result.stdout:
        print("\nMATLAB Output:")
        print(result.stdout)
    
    if result.stderr:
        print("\nMATLAB Errors:")
        print(result.stderr)
    
    # Clean up
    if test_file.exists():
        test_file.unlink()
    
    return result.returncode == 0

if __name__ == "__main__":
    test_matlab_toolboxes()
