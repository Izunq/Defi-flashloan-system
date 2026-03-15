#!/usr/bin/env python3
"""
Definitive MATLAB Financial Toolbox Test
"""

import subprocess

def test_financial_toolbox():
    matlab_path = r"C:\Program Files\MATLAB\R2025a\bin\matlab.exe"
    
    # Simple direct test
    matlab_cmd = "fprintf('Testing...\\n'); if license('test', 'Financial_Toolbox'), fprintf('Financial Toolbox: AVAILABLE\\n'); [c,p]=blsprice(100,100,0.05,0.25,0.2); fprintf('Black-Scholes Call: %.2f\\n', c); else, fprintf('Financial Toolbox: NOT AVAILABLE\\n'); end; exit;"
    
    print("Testing Financial Toolbox availability...")
    
    result = subprocess.run([
        matlab_path, "-r", matlab_cmd
    ], capture_output=True, text=True, timeout=30)
    
    print(f"MATLAB executed with return code: {result.returncode}")
    print("Output:", result.stdout if result.stdout else "No output")
    print("Errors:", result.stderr if result.stderr else "No errors")
    
    return result.returncode == 0

if __name__ == "__main__":
    test_financial_toolbox()
