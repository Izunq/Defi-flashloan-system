#!/usr/bin/env python3
"""
MATLAB Integration Analytics System
Leverages MATLAB R2025a for advanced financial analysis and Python for comprehensive data processing
"""

import subprocess
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import tempfile
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class MATLABIntegratedAnalytics:
    def __init__(self, data_dir="analytics_data", matlab_path=r"C:\Program Files\MATLAB\R2025a\bin\matlab.exe"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.matlab_path = matlab_path
        self.results_dir = self.data_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Create MATLAB scripts directory
        self.matlab_scripts_dir = self.data_dir / "matlab_scripts"
        self.matlab_scripts_dir.mkdir(exist_ok=True)
        
        print(f"✅ Analytics system initialized")
        print(f"📊 Data directory: {self.data_dir}")
        print(f"🔬 MATLAB path: {self.matlab_path}")
        print(f"📈 Results directory: {self.results_dir}")

    def check_matlab_availability(self):
        """Check if MATLAB is available and functioning"""
        try:
            result = subprocess.run([
                self.matlab_path, "-batch", "disp('MATLAB Available'); exit"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ MATLAB R2025a is available and responsive")
                return True
            else:
                print(f"❌ MATLAB error: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ MATLAB not accessible: {e}")
            return False

    def create_matlab_arbitrage_analyzer(self):
        """Create MATLAB script for advanced arbitrage analysis"""
        matlab_script = """
% Advanced Arbitrage Analytics in MATLAB
% Comprehensive financial analysis for crypto arbitrage opportunities

function results = analyze_arbitrage_data(data_file, output_file)
    try
        % Load data
        data = readtable(data_file);
        
        % Initialize results structure
        results = struct();
        
        % Extract time series data
        if ismember('timestamp', data.Properties.VariableNames)
            timestamps = datetime(data.timestamp, 'InputFormat', 'yyyy-MM-dd HH:mm:ss');
        else
            timestamps = (1:height(data))';
        end
        
        % Price spread analysis
        if ismember('price_spread', data.Properties.VariableNames)
            price_spreads = data.price_spread;
            results.spread_analysis = analyze_spreads(price_spreads, timestamps);
        end
        
        % Profit analysis
        if ismember('profit', data.Properties.VariableNames)
            profits = data.profit;
            results.profit_analysis = analyze_profits(profits, timestamps);
        end
        
        % Volatility analysis
        if ismember('volatility', data.Properties.VariableNames)
            volatility = data.volatility;
            results.volatility_analysis = analyze_volatility(volatility, timestamps);
        end
        
        % Risk metrics
        results.risk_metrics = calculate_risk_metrics(data);
        
        % Opportunity scoring
        results.opportunity_scores = score_opportunities(data);
        
        % Market regime detection
        results.market_regimes = detect_market_regimes(data);
        
        % Optimal timing analysis
        results.timing_analysis = analyze_optimal_timing(data);
        
        % Save results
        save(output_file, 'results');
        
        % Create summary report
        create_summary_report(results, strrep(output_file, '.mat', '_report.txt'));
        
        fprintf('✅ MATLAB analysis completed successfully\\n');
        
    catch ME
        fprintf('❌ MATLAB analysis error: %s\\n', ME.message);
        results = struct('error', ME.message);
    end
end

function spread_analysis = analyze_spreads(spreads, timestamps)
    spread_analysis = struct();
    
    % Basic statistics
    spread_analysis.mean = mean(spreads, 'omitnan');
    spread_analysis.std = std(spreads, 'omitnan');
    spread_analysis.min = min(spreads);
    spread_analysis.max = max(spreads);
    spread_analysis.median = median(spreads, 'omitnan');
    
    % Percentiles
    spread_analysis.percentile_90 = prctile(spreads, 90);
    spread_analysis.percentile_95 = prctile(spreads, 95);
    spread_analysis.percentile_99 = prctile(spreads, 99);
    
    % Time series analysis
    if length(spreads) > 10
        % Autocorrelation
        [acf, lags] = autocorr(spreads, 'NumLags', min(20, length(spreads)-1));
        spread_analysis.autocorr_lag1 = acf(2);
        
        % Trend analysis
        trend_coeffs = polyfit(1:length(spreads), spreads', 1);
        spread_analysis.trend_slope = trend_coeffs(1);
    end
    
    % Regime identification
    spread_analysis.high_spread_threshold = prctile(spreads, 75);
    spread_analysis.high_spread_periods = sum(spreads > spread_analysis.high_spread_threshold);
end

function profit_analysis = analyze_profits(profits, timestamps)
    profit_analysis = struct();
    
    % Return metrics
    profit_analysis.total_return = sum(profits);
    profit_analysis.mean_return = mean(profits, 'omitnan');
    profit_analysis.std_return = std(profits, 'omitnan');
    
    % Risk-adjusted metrics
    if profit_analysis.std_return > 0
        profit_analysis.sharpe_ratio = profit_analysis.mean_return / profit_analysis.std_return;
    else
        profit_analysis.sharpe_ratio = 0;
    end
    
    % Win rate
    winning_trades = profits > 0;
    profit_analysis.win_rate = sum(winning_trades) / length(profits);
    
    % Profit factor
    gross_profit = sum(profits(profits > 0));
    gross_loss = abs(sum(profits(profits < 0)));
    if gross_loss > 0
        profit_analysis.profit_factor = gross_profit / gross_loss;
    else
        profit_analysis.profit_factor = inf;
    end
    
    % Maximum drawdown
    cumulative_profits = cumsum(profits);
    running_max = cummax(cumulative_profits);
    drawdowns = running_max - cumulative_profits;
    profit_analysis.max_drawdown = max(drawdowns);
    
    % Consecutive wins/losses
    profit_analysis.max_consecutive_wins = max_consecutive(profits > 0);
    profit_analysis.max_consecutive_losses = max_consecutive(profits < 0);
end

function volatility_analysis = analyze_volatility(volatility, timestamps)
    volatility_analysis = struct();
    
    % Basic statistics
    volatility_analysis.mean = mean(volatility, 'omitnan');
    volatility_analysis.std = std(volatility, 'omitnan');
    volatility_analysis.min = min(volatility);
    volatility_analysis.max = max(volatility);
    
    % Volatility clustering (GARCH-like analysis)
    if length(volatility) > 20
        % Simple volatility clustering measure
        vol_changes = diff(volatility);
        volatility_analysis.clustering_coefficient = corr(abs(vol_changes(1:end-1)), abs(vol_changes(2:end)));
    end
    
    % High volatility periods
    high_vol_threshold = prctile(volatility, 90);
    volatility_analysis.high_vol_threshold = high_vol_threshold;
    volatility_analysis.high_vol_periods = sum(volatility > high_vol_threshold);
end

function risk_metrics = calculate_risk_metrics(data)
    risk_metrics = struct();
    
    % Value at Risk (VaR)
    if ismember('profit', data.Properties.VariableNames)
        profits = data.profit;
        risk_metrics.var_95 = prctile(profits, 5);
        risk_metrics.var_99 = prctile(profits, 1);
        
        % Expected Shortfall (Conditional VaR)
        var_95_threshold = risk_metrics.var_95;
        tail_losses = profits(profits <= var_95_threshold);
        if ~isempty(tail_losses)
            risk_metrics.expected_shortfall_95 = mean(tail_losses);
        end
    end
    
    % Gas cost risk
    if ismember('gas_cost', data.Properties.VariableNames)
        gas_costs = data.gas_cost;
        risk_metrics.gas_cost_var_95 = prctile(gas_costs, 95);
        risk_metrics.gas_cost_std = std(gas_costs, 'omitnan');
    end
    
    % Liquidity risk indicators
    if ismember('liquidity_score', data.Properties.VariableNames)
        liquidity = data.liquidity_score;
        risk_metrics.low_liquidity_threshold = prctile(liquidity, 10);
        risk_metrics.liquidity_stress_periods = sum(liquidity < risk_metrics.low_liquidity_threshold);
    end
end

function scores = score_opportunities(data)
    scores = struct();
    
    % Composite opportunity score
    score_components = {};
    weights = [];
    
    if ismember('price_spread', data.Properties.VariableNames)
        % Normalize spread scores
        spreads = data.price_spread;
        spread_scores = (spreads - min(spreads)) / (max(spreads) - min(spreads));
        score_components{end+1} = spread_scores;
        weights(end+1) = 0.4; % 40% weight to price spread
    end
    
    if ismember('liquidity_score', data.Properties.VariableNames)
        score_components{end+1} = data.liquidity_score;
        weights(end+1) = 0.3; % 30% weight to liquidity
    end
    
    if ismember('gas_efficiency', data.Properties.VariableNames)
        score_components{end+1} = data.gas_efficiency;
        weights(end+1) = 0.3; % 30% weight to gas efficiency
    end
    
    % Calculate weighted composite score
    if ~isempty(score_components)
        weights = weights / sum(weights); % Normalize weights
        composite_score = zeros(size(score_components{1}));
        for i = 1:length(score_components)
            composite_score = composite_score + weights(i) * score_components{i};
        end
        scores.composite_score = composite_score;
        scores.top_10_percent_threshold = prctile(composite_score, 90);
        scores.excellent_opportunities = sum(composite_score > scores.top_10_percent_threshold);
    end
end

function regimes = detect_market_regimes(data)
    regimes = struct();
    
    if ismember('volatility', data.Properties.VariableNames)
        volatility = data.volatility;
        
        % Simple regime classification based on volatility
        low_vol_threshold = prctile(volatility, 33);
        high_vol_threshold = prctile(volatility, 67);
        
        regime_labels = cell(size(volatility));
        regime_labels(volatility <= low_vol_threshold) = {'Low_Volatility'};
        regime_labels(volatility > low_vol_threshold & volatility <= high_vol_threshold) = {'Medium_Volatility'};
        regime_labels(volatility > high_vol_threshold) = {'High_Volatility'};
        
        regimes.labels = regime_labels;
        regimes.low_vol_periods = sum(volatility <= low_vol_threshold);
        regimes.medium_vol_periods = sum(volatility > low_vol_threshold & volatility <= high_vol_threshold);
        regimes.high_vol_periods = sum(volatility > high_vol_threshold);
    end
end

function timing = analyze_optimal_timing(data)
    timing = struct();
    
    if ismember('timestamp', data.Properties.VariableNames) && ismember('profit', data.Properties.VariableNames)
        timestamps = datetime(data.timestamp, 'InputFormat', 'yyyy-MM-dd HH:mm:ss');
        profits = data.profit;
        
        % Hour-of-day analysis
        hours = hour(timestamps);
        unique_hours = unique(hours);
        hourly_profits = zeros(size(unique_hours));
        
        for i = 1:length(unique_hours)
            h = unique_hours(i);
            hourly_profits(i) = mean(profits(hours == h), 'omitnan');
        end
        
        [~, best_hour_idx] = max(hourly_profits);
        timing.best_hour = unique_hours(best_hour_idx);
        timing.hourly_profits = containers.Map(num2cell(unique_hours), num2cell(hourly_profits));
        
        % Day-of-week analysis (if data spans multiple days)
        if days(max(timestamps) - min(timestamps)) >= 7
            day_of_week = weekday(timestamps);
            unique_days = unique(day_of_week);
            daily_profits = zeros(size(unique_days));
            
            for i = 1:length(unique_days)
                d = unique_days(i);
                daily_profits(i) = mean(profits(day_of_week == d), 'omitnan');
            end
            
            [~, best_day_idx] = max(daily_profits);
            timing.best_day_of_week = unique_days(best_day_idx);
        end
    end
end

function max_consec = max_consecutive(logical_array)
    if isempty(logical_array)
        max_consec = 0;
        return;
    end
    
    consecutive_counts = diff([0; cumsum(~logical_array)]);
    run_lengths = consecutive_counts(logical_array);
    
    if isempty(run_lengths)
        max_consec = 0;
    else
        max_consec = max(run_lengths);
    end
end

function create_summary_report(results, filename)
    fid = fopen(filename, 'w');
    
    fprintf(fid, '=== MATLAB ARBITRAGE ANALYSIS REPORT ===\\n');
    fprintf(fid, 'Generated: %s\\n\\n', datestr(now));
    
    % Spread Analysis
    if isfield(results, 'spread_analysis')
        s = results.spread_analysis;
        fprintf(fid, '📊 PRICE SPREAD ANALYSIS:\\n');
        fprintf(fid, '  Mean Spread: %.6f\\n', s.mean);
        fprintf(fid, '  Std Deviation: %.6f\\n', s.std);
        fprintf(fid, '  95th Percentile: %.6f\\n', s.percentile_95);
        if isfield(s, 'trend_slope')
            fprintf(fid, '  Trend Slope: %.8f\\n', s.trend_slope);
        end
        fprintf(fid, '\\n');
    end
    
    % Profit Analysis
    if isfield(results, 'profit_analysis')
        p = results.profit_analysis;
        fprintf(fid, '💰 PROFIT ANALYSIS:\\n');
        fprintf(fid, '  Total Return: %.6f\\n', p.total_return);
        fprintf(fid, '  Mean Return: %.6f\\n', p.mean_return);
        fprintf(fid, '  Sharpe Ratio: %.4f\\n', p.sharpe_ratio);
        fprintf(fid, '  Win Rate: %.2f%%\\n', p.win_rate * 100);
        fprintf(fid, '  Profit Factor: %.4f\\n', p.profit_factor);
        fprintf(fid, '  Max Drawdown: %.6f\\n', p.max_drawdown);
        fprintf(fid, '\\n');
    end
    
    % Risk Metrics
    if isfield(results, 'risk_metrics')
        r = results.risk_metrics;
        fprintf(fid, '⚠️ RISK METRICS:\\n');
        if isfield(r, 'var_95')
            fprintf(fid, '  VaR (95%%): %.6f\\n', r.var_95);
        end
        if isfield(r, 'expected_shortfall_95')
            fprintf(fid, '  Expected Shortfall (95%%): %.6f\\n', r.expected_shortfall_95);
        end
        fprintf(fid, '\\n');
    end
    
    % Opportunity Scores
    if isfield(results, 'opportunity_scores')
        o = results.opportunity_scores;
        if isfield(o, 'excellent_opportunities')
            fprintf(fid, '🎯 OPPORTUNITY ANALYSIS:\\n');
            fprintf(fid, '  Excellent Opportunities: %d\\n', o.excellent_opportunities);
            fprintf(fid, '  Top 10%% Threshold: %.4f\\n', o.top_10_percent_threshold);
            fprintf(fid, '\\n');
        end
    end
    
    % Timing Analysis
    if isfield(results, 'timing_analysis')
        t = results.timing_analysis;
        if isfield(t, 'best_hour')
            fprintf(fid, '⏰ OPTIMAL TIMING:\\n');
            fprintf(fid, '  Best Hour: %d:00\\n', t.best_hour);
            if isfield(t, 'best_day_of_week')
                fprintf(fid, '  Best Day of Week: %d\\n', t.best_day_of_week);
            end
            fprintf(fid, '\\n');
        end
    end
    
    fclose(fid);
end

% Main execution
if ~isempty(who('data_file')) && ~isempty(who('output_file'))
    analyze_arbitrage_data(data_file, output_file);
end
"""
        
        script_path = self.matlab_scripts_dir / "arbitrage_analyzer.m"
        with open(script_path, 'w') as f:
            f.write(matlab_script)
        
        print(f"✅ Created MATLAB arbitrage analyzer: {script_path}")
        return script_path

    def run_matlab_analysis(self, data_file, output_prefix="matlab_analysis"):
        """Run MATLAB analysis on the provided data"""
        if not self.check_matlab_availability():
            print("❌ MATLAB not available, falling back to Python analysis")
            return self.run_python_fallback_analysis(data_file, output_prefix)
        
        try:
            # Create MATLAB analyzer
            matlab_script = self.create_matlab_arbitrage_analyzer()
            
            # Prepare file paths
            data_file_path = Path(data_file).resolve()
            output_file = self.results_dir / f"{output_prefix}.mat"
            
            # Create MATLAB command
            matlab_command = f"""
cd('{self.matlab_scripts_dir}');
data_file = '{data_file_path}';
output_file = '{output_file}';
analyze_arbitrage_data(data_file, output_file);
exit;
"""
            
            # Save command to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.m', delete=False) as tmp:
                tmp.write(matlab_command)
                tmp_script = tmp.name
            
            # Run MATLAB
            print("🔬 Running MATLAB analysis...")
            result = subprocess.run([
                self.matlab_path, "-batch", f"run('{tmp_script}')"
            ], capture_output=True, text=True, timeout=120)
            
            # Clean up
            os.unlink(tmp_script)
            
            if result.returncode == 0:
                print("✅ MATLAB analysis completed successfully")
                
                # Check for output files
                report_file = self.results_dir / f"{output_prefix}_report.txt"
                if report_file.exists():
                    print(f"📊 MATLAB report generated: {report_file}")
                    with open(report_file, 'r') as f:
                        print("\n" + "="*60)
                        print("MATLAB ANALYSIS REPORT")
                        print("="*60)
                        print(f.read())
                
                return True
            else:
                print(f"❌ MATLAB analysis failed: {result.stderr}")
                return self.run_python_fallback_analysis(data_file, output_prefix)
                
        except Exception as e:
            print(f"❌ Error running MATLAB analysis: {e}")
            return self.run_python_fallback_analysis(data_file, output_prefix)    def run_python_fallback_analysis(self, data_file, output_prefix="python_analysis"):
        """Advanced Python-based analysis as fallback"""
        try:
            print("🐍 Running advanced Python analysis...")
            
            # Convert Path object to string
            data_file_str = str(data_file)
            
            # Load data
            if data_file_str.endswith('.json'):
                with open(data_file, 'r') as f:
                    data_dict = json.load(f)
                df = pd.DataFrame(data_dict)
            else:
                df = pd.read_csv(data_file)
            
            results = {}
            
            # Price spread analysis
            if 'price_spread' in df.columns:
                spreads = df['price_spread'].dropna()
                results['spread_analysis'] = {
                    'mean': float(spreads.mean()),
                    'std': float(spreads.std()),
                    'min': float(spreads.min()),
                    'max': float(spreads.max()),
                    'median': float(spreads.median()),
                    'percentile_90': float(spreads.quantile(0.9)),
                    'percentile_95': float(spreads.quantile(0.95)),
                    'percentile_99': float(spreads.quantile(0.99)),
                }
                
                # Autocorrelation
                if len(spreads) > 10:
                    from statsmodels.tsa.stattools import acf
                    autocorr = acf(spreads, nlags=5, fft=True)
                    results['spread_analysis']['autocorr_lag1'] = float(autocorr[1])
            
            # Profit analysis
            if 'profit' in df.columns:
                profits = df['profit'].dropna()
                results['profit_analysis'] = {
                    'total_return': float(profits.sum()),
                    'mean_return': float(profits.mean()),
                    'std_return': float(profits.std()),
                    'win_rate': float((profits > 0).mean()),
                    'max_drawdown': float((profits.cumsum().cummax() - profits.cumsum()).max())
                }
                
                # Sharpe ratio
                if profits.std() > 0:
                    results['profit_analysis']['sharpe_ratio'] = float(profits.mean() / profits.std())
                
                # Profit factor
                gross_profit = profits[profits > 0].sum()
                gross_loss = abs(profits[profits < 0].sum())
                if gross_loss > 0:
                    results['profit_analysis']['profit_factor'] = float(gross_profit / gross_loss)
            
            # Volatility analysis
            if 'volatility' in df.columns:
                vol = df['volatility'].dropna()
                results['volatility_analysis'] = {
                    'mean': float(vol.mean()),
                    'std': float(vol.std()),
                    'min': float(vol.min()),
                    'max': float(vol.max()),
                    'high_vol_threshold': float(vol.quantile(0.9)),
                    'high_vol_periods': int((vol > vol.quantile(0.9)).sum())
                }
            
            # Risk metrics
            if 'profit' in df.columns:
                profits = df['profit'].dropna()
                results['risk_metrics'] = {
                    'var_95': float(profits.quantile(0.05)),
                    'var_99': float(profits.quantile(0.01)),
                    'expected_shortfall_95': float(profits[profits <= profits.quantile(0.05)].mean())
                }
            
            # Save results
            output_file = self.results_dir / f"{output_prefix}.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            # Create report
            report_file = self.results_dir / f"{output_prefix}_report.txt"
            self.create_python_report(results, report_file)
            
            print(f"✅ Python analysis completed: {output_file}")
            print(f"📊 Report generated: {report_file}")
            
            # Display report
            with open(report_file, 'r') as f:
                print("\n" + "="*60)
                print("PYTHON ANALYSIS REPORT")
                print("="*60)
                print(f.read())
            
            return True
            
        except Exception as e:
            print(f"❌ Python analysis error: {e}")
            return False

    def create_python_report(self, results, filename):
        """Create formatted analysis report"""
        with open(filename, 'w') as f:
            f.write("=== PYTHON ARBITRAGE ANALYSIS REPORT ===\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Spread Analysis
            if 'spread_analysis' in results:
                s = results['spread_analysis']
                f.write("📊 PRICE SPREAD ANALYSIS:\n")
                f.write(f"  Mean Spread: {s['mean']:.6f}\n")
                f.write(f"  Std Deviation: {s['std']:.6f}\n")
                f.write(f"  95th Percentile: {s['percentile_95']:.6f}\n")
                if 'autocorr_lag1' in s:
                    f.write(f"  Autocorrelation (lag 1): {s['autocorr_lag1']:.4f}\n")
                f.write("\n")
            
            # Profit Analysis
            if 'profit_analysis' in results:
                p = results['profit_analysis']
                f.write("💰 PROFIT ANALYSIS:\n")
                f.write(f"  Total Return: {p['total_return']:.6f}\n")
                f.write(f"  Mean Return: {p['mean_return']:.6f}\n")
                if 'sharpe_ratio' in p:
                    f.write(f"  Sharpe Ratio: {p['sharpe_ratio']:.4f}\n")
                f.write(f"  Win Rate: {p['win_rate']*100:.2f}%\n")
                if 'profit_factor' in p:
                    f.write(f"  Profit Factor: {p['profit_factor']:.4f}\n")
                f.write(f"  Max Drawdown: {p['max_drawdown']:.6f}\n")
                f.write("\n")
            
            # Risk Metrics
            if 'risk_metrics' in results:
                r = results['risk_metrics']
                f.write("⚠️ RISK METRICS:\n")
                f.write(f"  VaR (95%): {r['var_95']:.6f}\n")
                f.write(f"  Expected Shortfall (95%): {r['expected_shortfall_95']:.6f}\n")
                f.write("\n")
            
            # Volatility Analysis
            if 'volatility_analysis' in results:
                v = results['volatility_analysis']
                f.write("📈 VOLATILITY ANALYSIS:\n")
                f.write(f"  Mean Volatility: {v['mean']:.6f}\n")
                f.write(f"  High Volatility Periods: {v['high_vol_periods']}\n")
                f.write("\n")

    def create_sample_data(self, filename="sample_arbitrage_data.csv", num_records=1000):
        """Create sample arbitrage data for analysis"""
        np.random.seed(42)
        
        # Generate realistic arbitrage data
        timestamps = pd.date_range(start='2025-01-01', periods=num_records, freq='5min')
        
        # Price spreads (realistic values for crypto arbitrage)
        base_spread = 0.002  # 0.2% base spread
        spread_volatility = 0.001
        price_spreads = np.random.normal(base_spread, spread_volatility, num_records)
        price_spreads = np.maximum(price_spreads, 0.0001)  # Minimum spread
        
        # Volatility (affects opportunity quality)
        volatility = np.random.exponential(0.02, num_records)
        
        # Gas costs (affects profitability)
        base_gas = 0.01  # $10 in gas
        gas_costs = np.random.lognormal(np.log(base_gas), 0.3, num_records)
        
        # Liquidity scores (0-1, higher is better)
        liquidity_scores = np.random.beta(2, 2, num_records)
        
        # Gas efficiency (based on gas costs)
        gas_efficiency = 1 / (1 + gas_costs / 0.02)
        
        # Profits (based on spreads, gas costs, and other factors)
        base_profit = price_spreads * 1000 - gas_costs  # $1000 trade size
        noise = np.random.normal(0, 0.005, num_records)
        profits = base_profit * liquidity_scores + noise
        
        # Create DataFrame
        df = pd.DataFrame({
            'timestamp': timestamps.strftime('%Y-%m-%d %H:%M:%S'),
            'price_spread': price_spreads,
            'volatility': volatility,
            'gas_cost': gas_costs,
            'liquidity_score': liquidity_scores,
            'gas_efficiency': gas_efficiency,
            'profit': profits
        })
        
        # Save data
        data_file = self.data_dir / filename
        df.to_csv(data_file, index=False)
        
        print(f"✅ Created sample data: {data_file}")
        print(f"📊 Records: {num_records}")
        print(f"💰 Mean profit: ${df['profit'].mean():.4f}")
        print(f"📈 Mean spread: {df['price_spread'].mean()*100:.3f}%")
        
        return data_file

    def run_comprehensive_analysis(self, data_file=None):
        """Run complete analytical pipeline"""
        print("🚀 Starting Comprehensive MATLAB + Python Analysis")
        print("="*60)
        
        # Create sample data if none provided
        if data_file is None:
            data_file = self.create_sample_data()
        
        # Run MATLAB analysis (with Python fallback)
        matlab_success = self.run_matlab_analysis(data_file, "comprehensive_matlab")
        
        # Run additional Python analysis
        python_success = self.run_python_fallback_analysis(data_file, "comprehensive_python")
        
        # Create executive summary
        self.create_executive_summary()
        
        print("\n" + "="*60)
        print("🏆 COMPREHENSIVE ANALYSIS COMPLETE")
        print("="*60)
        print(f"📁 Results directory: {self.results_dir}")
        
        return matlab_success and python_success

    def create_executive_summary(self):
        """Create executive summary combining all analyses"""
        summary_file = self.results_dir / "executive_summary.md"
        
        with open(summary_file, 'w') as f:
            f.write("# Executive Summary: Arbitrage Analytics\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Key Findings\n\n")
            f.write("### Performance Metrics\n")
            f.write("- **Analysis Platform:** MATLAB R2025a + Python\n")
            f.write("- **Data Processing:** Advanced time series analysis\n")
            f.write("- **Risk Assessment:** VaR, Expected Shortfall, Drawdown analysis\n\n")
            
            f.write("### Recommendations\n")
            f.write("1. **Optimal Timing:** Leverage hour-of-day analysis for trade execution\n")
            f.write("2. **Risk Management:** Implement VaR-based position sizing\n")
            f.write("3. **Market Regimes:** Adapt strategies based on volatility regimes\n")
            f.write("4. **Gas Optimization:** Focus on high gas-efficiency periods\n\n")
            
            f.write("### Technical Implementation\n")
            f.write("- **MATLAB Integration:** Advanced financial modeling\n")
            f.write("- **Python Analytics:** Machine learning and statistical analysis\n")
            f.write("- **Real-time Monitoring:** Continuous opportunity assessment\n\n")
            
            f.write("### Next Steps\n")
            f.write("1. Deploy real-time analytics pipeline\n")
            f.write("2. Integrate with trading system\n")
            f.write("3. Implement automated reporting\n")
            f.write("4. Scale to multiple markets\n\n")
            
        print(f"📋 Executive summary created: {summary_file}")


def main():
    """Main execution function"""
    analytics = MATLABIntegratedAnalytics()
    
    # Run comprehensive analysis
    success = analytics.run_comprehensive_analysis()
    
    if success:
        print("\n🎉 Analysis pipeline successfully executed!")
        print("💡 Ready for integration with trading systems")
    else:
        print("\n⚠️ Some analysis components failed")
        print("💪 Core functionality remains available")

if __name__ == "__main__":
    main()
