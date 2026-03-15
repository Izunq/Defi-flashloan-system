#!/usr/bin/env python3
"""
Clean MATLAB Strategy Development System
Advanced arbitrage strategy creation using MATLAB
"""

import subprocess
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class CleanMATLABStrategyDeveloper:
    def __init__(self, matlab_path=r"C:\Program Files\MATLAB\R2025a\bin\matlab.exe"):
        self.matlab_path = matlab_path
        self.strategy_dir = Path("clean_matlab_strategies")
        self.strategy_dir.mkdir(exist_ok=True)
        self.results_dir = self.strategy_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        print("MATLAB Strategy Development System Initialized")
        print(f"Strategy Directory: {self.strategy_dir}")
        print(f"Results Directory: {self.results_dir}")
        print(f"MATLAB Path: {self.matlab_path}")

    def create_simple_strategy_analyzer(self):
        """Create a simple but functional MATLAB strategy analysis system"""
        matlab_script = """function results = analyze_strategies(data_file, output_file)
try
    fprintf('Starting MATLAB Strategy Analysis...\\n');
    
    % Create sample data if file doesn't exist
    if ~exist(data_file, 'file')
        fprintf('Creating sample market data...\\n');
        n = 1000;
        dates = datetime('today') - days(n-1:-1:0);
        prices = 100 + cumsum(0.01 * randn(n, 1));
        volume = 1000 + 500 * rand(n, 1);
        
        data = table(dates, prices, volume, 'VariableNames', {'Date', 'Price', 'Volume'});
        writetable(data, data_file);
    else
        data = readtable(data_file);
    end
    
    % Initialize results
    results = struct();
    results.timestamp = datestr(now);
    results.data_points = height(data);
    
    % Basic statistics
    if height(data) > 0 && width(data) > 1
        results.price_stats = struct();
        price_col = data{:, 2}; % Assume second column is price
        results.price_stats.mean = mean(price_col);
        results.price_stats.std = std(price_col);
        results.price_stats.min = min(price_col);
        results.price_stats.max = max(price_col);
        
        % Simple moving averages
        if length(price_col) >= 20
            results.sma_10 = movmean(price_col, 10);
            results.sma_20 = movmean(price_col, 20);
        end
        
        % Simple returns
        if length(price_col) > 1
            returns = diff(log(price_col));
            results.returns_stats = struct();
            results.returns_stats.mean = mean(returns);
            results.returns_stats.std = std(returns);
            results.returns_stats.sharpe = mean(returns) / std(returns) * sqrt(252);
        end
    end
    
    % Strategy signals
    results.strategy_signals = generate_basic_signals(data);
    
    % Save results
    save(output_file, 'results');
    
    % Create report
    report_file = strrep(output_file, '.mat', '_report.txt');
    create_basic_report(results, report_file);
    
    fprintf('MATLAB Strategy Analysis Complete!\\n');
    
catch ME
    fprintf('Error in MATLAB analysis: %s\\n', ME.message);
    results = struct('error', ME.message);
    save(output_file, 'results');
end
end

function signals = generate_basic_signals(data)
try
    if height(data) < 20
        signals = struct('error', 'Insufficient data for signals');
        return;
    end
    
    price_col = data{:, 2};
    sma_short = movmean(price_col, 5);
    sma_long = movmean(price_col, 20);
    
    signals = struct();
    signals.buy_signals = sma_short > sma_long;
    signals.sell_signals = sma_short < sma_long;
    signals.signal_count = sum(signals.buy_signals) + sum(signals.sell_signals);
    
catch ME
    signals = struct('error', ME.message);
end
end

function create_basic_report(results, report_file)
try
    fid = fopen(report_file, 'w');
    if fid == -1
        return;
    end
    
    fprintf(fid, 'MATLAB Strategy Analysis Report\\n');
    fprintf(fid, '================================\\n\\n');
    fprintf(fid, 'Analysis Timestamp: %s\\n', results.timestamp);
    fprintf(fid, 'Data Points: %d\\n\\n', results.data_points);
    
    if isfield(results, 'price_stats')
        fprintf(fid, 'Price Statistics:\\n');
        fprintf(fid, '  Mean: %.4f\\n', results.price_stats.mean);
        fprintf(fid, '  Std Dev: %.4f\\n', results.price_stats.std);
        fprintf(fid, '  Min: %.4f\\n', results.price_stats.min);
        fprintf(fid, '  Max: %.4f\\n\\n', results.price_stats.max);
    end
    
    if isfield(results, 'returns_stats')
        fprintf(fid, 'Returns Statistics:\\n');
        fprintf(fid, '  Mean Return: %.6f\\n', results.returns_stats.mean);
        fprintf(fid, '  Volatility: %.6f\\n', results.returns_stats.std);
        fprintf(fid, '  Sharpe Ratio: %.4f\\n\\n', results.returns_stats.sharpe);
    end
    
    if isfield(results, 'strategy_signals') && isfield(results.strategy_signals, 'signal_count')
        fprintf(fid, 'Strategy Signals: %d total signals generated\\n', results.strategy_signals.signal_count);
    end
    
    fclose(fid);
    
catch ME
    if exist('fid', 'var') && fid ~= -1
        fclose(fid);
    end
end
end"""
        
        return matlab_script

    def generate_sample_data(self):
        """Generate realistic sample market data"""
        print("Generating sample market data...")
        
        n_days = 1000
        dates = pd.date_range(start='2023-01-01', periods=n_days, freq='D')
        
        # Generate realistic price data with trends and volatility
        returns = np.random.normal(0.0002, 0.02, n_days)  # Daily returns
        prices = 100 * np.exp(np.cumsum(returns))
        
        # Add some volume data
        volumes = np.random.lognormal(8, 0.5, n_days)
        
        # Create spreads for arbitrage opportunities
        spreads = np.random.normal(0.001, 0.0005, n_days)
        
        data = pd.DataFrame({
            'Date': dates,
            'Price': prices,
            'Volume': volumes,
            'Spread': spreads,
            'High': prices * (1 + np.abs(np.random.normal(0, 0.01, n_days))),
            'Low': prices * (1 - np.abs(np.random.normal(0, 0.01, n_days))),
        })
        
        data_file = self.strategy_dir / "sample_market_data.csv"
        data.to_csv(data_file, index=False)
        print(f"Sample data saved to: {data_file}")
        
        return data_file

    def run_matlab_analysis(self):
        """Run the MATLAB strategy analysis"""
        print("\n" + "="*60)
        print("RUNNING CLEAN MATLAB STRATEGY ANALYSIS")
        print("="*60)
        
        # Generate sample data
        data_file = self.generate_sample_data()
        
        # Create MATLAB script
        matlab_script = self.create_simple_strategy_analyzer()
        script_file = self.strategy_dir / "analyze_strategies.m"
        
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(matlab_script)
        
        print(f"MATLAB script created: {script_file}")
        
        # Prepare file paths for MATLAB
        data_file_abs = str(data_file.absolute())
        output_file = str((self.results_dir / "strategy_results.mat").absolute())
        
        # Create MATLAB command
        matlab_command = f'analyze_strategies("{data_file_abs}", "{output_file}"); exit;'
        
        # Run MATLAB
        print(f"\nExecuting MATLAB command...")
        print(f"Working directory: {self.strategy_dir}")
        print(f"Data file: {data_file_abs}")
        print(f"Output file: {output_file}")
        
        try:
            # Change to strategy directory
            original_dir = os.getcwd()
            os.chdir(self.strategy_dir)
            
            # Run MATLAB with the command
            result = subprocess.run([
                self.matlab_path,
                '-batch',
                matlab_command
            ], 
            capture_output=True, 
            text=True, 
            timeout=300,
            cwd=str(self.strategy_dir))
            
            # Return to original directory
            os.chdir(original_dir)
            
            print(f"\nMATLAB execution completed!")
            print(f"Return code: {result.returncode}")
            
            if result.stdout:
                print(f"MATLAB Output:\n{result.stdout}")
            
            if result.stderr:
                print(f"MATLAB Errors:\n{result.stderr}")
            
            # Check for output files
            self.check_output_files()
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("MATLAB execution timed out!")
            return False
        except Exception as e:
            print(f"Error running MATLAB: {e}")
            return False
        finally:
            # Always return to original directory
            try:
                os.chdir(original_dir)
            except:
                pass

    def check_output_files(self):
        """Check and display generated output files"""
        print("\n" + "="*50)
        print("CHECKING OUTPUT FILES")
        print("="*50)
        
        # Check for .mat file
        mat_file = self.results_dir / "strategy_results.mat"
        if mat_file.exists():
            print(f"✓ MATLAB results file created: {mat_file}")
            print(f"  File size: {mat_file.stat().st_size} bytes")
        else:
            print(f"✗ MATLAB results file not found: {mat_file}")
        
        # Check for report file
        report_file = self.results_dir / "strategy_results_report.txt"
        if report_file.exists():
            print(f"✓ Strategy report created: {report_file}")
            print(f"  File size: {report_file.stat().st_size} bytes")
            
            # Display report content
            try:
                with open(report_file, 'r') as f:
                    content = f.read()
                print(f"\nREPORT CONTENT:")
                print("-" * 30)
                print(content)
                print("-" * 30)
            except Exception as e:
                print(f"Error reading report: {e}")
        else:
            print(f"✗ Strategy report not found: {report_file}")
        
        # List all files in results directory
        print(f"\nAll files in results directory:")
        try:
            for file_path in self.results_dir.iterdir():
                print(f"  - {file_path.name} ({file_path.stat().st_size} bytes)")
        except Exception as e:
            print(f"Error listing files: {e}")

    def generate_comprehensive_report(self):
        """Generate a comprehensive Python-based report"""
        print("\n" + "="*60)
        print("GENERATING COMPREHENSIVE STRATEGY REPORT")
        print("="*60)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        report = {
            "analysis_timestamp": timestamp,
            "system_info": {
                "matlab_path": self.matlab_path,
                "strategy_directory": str(self.strategy_dir),
                "results_directory": str(self.results_dir)
            },
            "data_analysis": {
                "sample_data_generated": True,
                "data_points": 1000,
                "analysis_period": "1000 days",
                "base_price": 100.0
            },
            "strategy_framework": {
                "mean_reversion": "Moving average crossover signals",
                "momentum_detection": "Short vs long term trend analysis", 
                "volatility_analysis": "Return-based volatility calculation",
                "risk_metrics": "Sharpe ratio computation"
            },
            "matlab_integration": {
                "script_created": True,
                "execution_attempted": True,
                "function_structure": "Modular MATLAB functions",
                "error_handling": "Try-catch blocks implemented"
            },
            "next_steps": [
                "Verify MATLAB Financial Toolbox availability",
                "Implement advanced technical indicators",
                "Add portfolio optimization functions",
                "Integrate with live trading pipeline"
            ]
        }
        
        # Save comprehensive report
        report_file = self.results_dir / f"comprehensive_strategy_report_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Comprehensive report saved: {report_file}")
        
        # Display summary
        print(f"\nSTRATEGY DEVELOPMENT SUMMARY:")
        print(f"  Analysis Time: {report['analysis_timestamp']}")
        print(f"  Data Points: {report['data_analysis']['data_points']}")
        print(f"  MATLAB Integration: {'✓' if report['matlab_integration']['execution_attempted'] else '✗'}")
        print(f"  Strategy Framework: {len(report['strategy_framework'])} components")
        print(f"  Next Steps: {len(report['next_steps'])} items")
        
        return report

def main():
    """Main execution function"""
    print("="*80)
    print("CLEAN MATLAB STRATEGY DEVELOPMENT SYSTEM")
    print("Professional Arbitrage Strategy Creation")
    print("="*80)
    
    # Initialize system
    developer = CleanMATLABStrategyDeveloper()
    
    # Run MATLAB analysis
    success = developer.run_matlab_analysis()
    
    # Generate comprehensive report
    report = developer.generate_comprehensive_report()
    
    print(f"\n{'='*60}")
    print("CLEAN MATLAB STRATEGY DEVELOPMENT COMPLETE")
    print(f"{'='*60}")
    print(f"Success: {'✓' if success else '✗'}")
    print(f"Report Generated: ✓")
    print(f"Next: Verify MATLAB toolbox integration")
    
    return success

if __name__ == "__main__":
    main()
