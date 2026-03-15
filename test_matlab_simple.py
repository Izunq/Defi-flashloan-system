#!/usr/bin/env python3
"""
Simple MATLAB Test
"""

import subprocess
import tempfile
from pathlib import Path

def test_matlab():
    matlab_path = r"C:\Program Files\MATLAB\R2025a\bin\matlab.exe"
    
    # Simple MATLAB test
    matlab_cmd = "fprintf('MATLAB Test Successful!\\n'); a = [1 2 3; 4 5 6]; b = sum(a); fprintf('Sum result: %s\\n', mat2str(b)); exit;"
    
    print("Testing MATLAB...")
    result = subprocess.run([
        matlab_path, "-r", matlab_cmd
    ], capture_output=True, text=True, timeout=60)
    
    print(f"Return code: {result.returncode}")
    print(f"STDOUT: {result.stdout}")
    print(f"STDERR: {result.stderr}")
    
    return result.returncode == 0

if __name__ == "__main__":
    test_matlab()
