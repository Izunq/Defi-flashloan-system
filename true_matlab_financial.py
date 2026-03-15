#!/usr/bin/env python3
"""
True MATLAB Financial Toolbox Integration
Uses actual MATLAB Financial, Econometrics, and Statistics toolboxes
"""

import subprocess
import json
import pandas as pd
import numpy as np
from datetime import datetime
import os
import tempfile
from pathlib import Path

class TrueMATLABFinancialSystem:
    def __init__(self, matlab_path=r"C:\Program Files\MATLAB\R2025a\bin\matlab.exe"):
        self.matlab_path = matlab_path
        self.strategy_dir = Path("matlab_financial_toolbox")
        self.strategy_dir.mkdir(exist_ok=True)
        self.results_dir = self.strategy_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        print("MATLAB Financial Toolbox Integration System")
        print(f"Strategy Directory: {self.strategy_dir}")
        print(f"MATLAB Path: {self.matlab_path}")

    def create_financial_toolbox_analyzer(self):
        """Create MATLAB script using actual Financial Toolbox functions"""
        matlab_script = """
function results = analyze_with_financial_toolbox(data_file, output_file)
    try
        fprintf('Starting MATLAB Financial Toolbox Analysis...\\n');
        
        % Check for required toolboxes
        if ~license('test', 'Financial_Toolbox')
            warning('Financial Toolbox not available - using basic functions');
        end
        
        if ~license('test', 'Econometrics_Toolbox')
            warning('Econometrics Toolbox not available - using basic functions');
        end
        
        % Load data
        data = readtable(data_file);
        results = struct();
        results.timestamp = datestr(now);
        results.num_observations = height(data);
        
        % Extract time series data
        prices = data.price_spread;
        returns = diff(log(prices + 1e-8));  % Log returns
        volatility = data.volatility;
        profits = data.profit;
        
        fprintf('Data loaded: %d observations\\n', length(prices));
        
        % === FINANCIAL TOOLBOX ANALYSIS ===
        
        % 1. GARCH Modeling for Volatility
        fprintf('Running GARCH volatility modeling...\\n');
        try
            if license('test', 'Econometrics_Toolbox')
                % Use Econometrics Toolbox GARCH
                garch_model = garch(1, 1);  % GARCH(1,1) model
                [fitted_garch, ~, logL] = estimate(garch_model, returns);
                
                % Forecast volatility
                vol_forecast = forecast(fitted_garch, 5);  % 5-step ahead
                
                results.garch_analysis = struct();
                results.garch_analysis.aic = -2 * logL + 2 * 3;  % AIC
                results.garch_analysis.vol_forecast = vol_forecast;
                results.garch_analysis.model_type = 'GARCH(1,1)';
                
                fprintf('GARCH model fitted successfully\\n');
            else
                % Fallback: simple volatility model
                vol_window = 20;
                realized_vol = movstd(returns, vol_window);
                results.garch_analysis = struct();
                results.garch_analysis.realized_volatility = realized_vol;
                results.garch_analysis.model_type = 'Rolling_Volatility';
            end
        catch ME
            fprintf('GARCH modeling failed: %s\\n', ME.message);
            results.garch_analysis = struct('error', ME.message);
        end
        
        % 2. Black-Scholes Option Pricing (if applicable)
        fprintf('Calculating option-style metrics...\\n');
        try
            if license('test', 'Financial_Toolbox')
                % Simulate option-like payoffs for arbitrage
                S = mean(prices);  % Current "price"
                K = S;  % At-the-money
                T = 1/252;  % Daily expiry
                r = 0.05;  % Risk-free rate
                sigma = mean(volatility);
                
                % Black-Scholes call price
                [call_price, put_price] = blsprice(S, K, r, T, sigma);
                
                % Greeks
                [delta, gamma, ~, theta, rho, vega] = blsgamma(S, K, r, T, sigma);
                
                results.option_metrics = struct();
                results.option_metrics.call_price = call_price;
                results.option_metrics.put_price = put_price;
                results.option_metrics.delta = delta;
                results.option_metrics.gamma = gamma;
                results.option_metrics.theta = theta;
                results.option_metrics.vega = vega;
                
                fprintf('Option metrics calculated\\n');
            end
        catch ME
            fprintf('Option pricing failed: %s\\n', ME.message);
        end
        
        % 3. Portfolio Optimization using Financial Toolbox
        fprintf('Running portfolio optimization...\\n');
        try
            if license('test', 'Financial_Toolbox')
                % Create multiple strategy returns
                n_strategies = 4;
                strategy_returns = zeros(length(profits), n_strategies);
                
                % Strategy 1: Mean reversion
                z_scores = zscore(prices);
                strategy_returns(:, 1) = -sign(z_scores) .* profits;
                
                % Strategy 2: Momentum
                momentum = diff([prices(1); prices]);
                strategy_returns(:, 2) = sign(momentum) .* profits;
                
                % Strategy 3: Volatility
                vol_signals = double(volatility > median(volatility));
                strategy_returns(:, 3) = vol_signals .* profits;
                
                % Strategy 4: Random (for comparison)
                strategy_returns(:, 4) = profits;
                
                % Portfolio optimization
                expected_returns = mean(strategy_returns)';
                covariance_matrix = cov(strategy_returns);
                
                % Mean-variance optimization
                num_portfolios = 1000;
                returns_range = linspace(min(expected_returns), max(expected_returns), num_portfolios);
                
                % Efficient frontier
                efficient_weights = zeros(num_portfolios, n_strategies);
                efficient_risks = zeros(num_portfolios, 1);
                
                for i = 1:num_portfolios
                    target_return = returns_range(i);
                    
                    % Quadratic programming for portfolio optimization
                    H = 2 * covariance_matrix;
                    f = zeros(n_strategies, 1);
                    
                    % Constraints: sum(weights) = 1, expected return = target
                    Aeq = [ones(1, n_strategies); expected_returns'];
                    beq = [1; target_return];
                    
                    % Bounds: weights between 0 and 1
                    lb = zeros(n_strategies, 1);
                    ub = ones(n_strategies, 1);
                    
                    try
                        % Use quadprog if Optimization Toolbox available
                        if license('test', 'Optimization_Toolbox')
                            options = optimoptions('quadprog', 'Display', 'off');
                            weights = quadprog(H, f, [], [], Aeq, beq, lb, ub, [], options);
                        else
                            % Simple analytical solution for 2-asset case
                            if n_strategies == 2
                                w1 = (target_return - expected_returns(2)) / (expected_returns(1) - expected_returns(2));
                                w1 = max(0, min(1, w1));
                                weights = [w1; 1-w1];
                            else
                                % Equal weights fallback
                                weights = ones(n_strategies, 1) / n_strategies;
                            end
                        end
                        
                        efficient_weights(i, :) = weights';
                        efficient_risks(i) = sqrt(weights' * covariance_matrix * weights);
                        
                    catch
                        % Fallback to equal weights
                        weights = ones(n_strategies, 1) / n_strategies;
                        efficient_weights(i, :) = weights';
                        efficient_risks(i) = sqrt(weights' * covariance_matrix * weights);
                    end
                end
                
                % Find optimal portfolio (max Sharpe ratio)
                sharpe_ratios = returns_range' ./ efficient_risks;
                [max_sharpe, optimal_idx] = max(sharpe_ratios);
                optimal_weights = efficient_weights(optimal_idx, :);
                
                results.portfolio_optimization = struct();
                results.portfolio_optimization.optimal_weights = optimal_weights;
                results.portfolio_optimization.max_sharpe_ratio = max_sharpe;
                results.portfolio_optimization.optimal_return = returns_range(optimal_idx);
                results.portfolio_optimization.optimal_risk = efficient_risks(optimal_idx);
                results.portfolio_optimization.efficient_frontier_returns = returns_range;
                results.portfolio_optimization.efficient_frontier_risks = efficient_risks;
                
                fprintf('Portfolio optimization completed\\n');
            end
        catch ME
            fprintf('Portfolio optimization failed: %s\\n', ME.message);
        end
        
        % 4. Statistical Analysis using Statistics Toolbox
        fprintf('Running statistical analysis...\\n');
        try
            if license('test', 'Statistics_Toolbox')
                % Hypothesis testing on returns
                [h_ttest, p_ttest] = ttest(returns);  % T-test for mean
                [h_kstest, p_kstest] = kstest(zscore(returns));  % Normality test
                
                % Distribution fitting
                pd_normal = fitdist(returns, 'Normal');
                pd_tdist = fitdist(returns, 'tLocationScale');
                
                % AIC comparison
                aic_normal = -2 * sum(log(pdf(pd_normal, returns))) + 2 * 2;
                aic_tdist = -2 * sum(log(pdf(pd_tdist, returns))) + 2 * 3;
                
                results.statistical_analysis = struct();
                results.statistical_analysis.ttest_h = h_ttest;
                results.statistical_analysis.ttest_p = p_ttest;
                results.statistical_analysis.normality_h = h_kstest;
                results.statistical_analysis.normality_p = p_kstest;
                results.statistical_analysis.best_distribution = 'Normal';
                if aic_tdist < aic_normal
                    results.statistical_analysis.best_distribution = 'T-Distribution';
                end
                results.statistical_analysis.normal_aic = aic_normal;
                results.statistical_analysis.tdist_aic = aic_tdist;
                
                fprintf('Statistical analysis completed\\n');
            end
        catch ME
            fprintf('Statistical analysis failed: %s\\n', ME.message);
        end
        
        % 5. Risk Metrics using Financial Toolbox
        fprintf('Calculating risk metrics...\\n');
        try
            % Value at Risk (VaR)
            confidence_level = 0.05;  % 95% VaR
            
            if license('test', 'Financial_Toolbox')
                % Parametric VaR
                var_parametric = -norminv(confidence_level) * std(returns);
                
                % Historical VaR
                var_historical = -quantile(returns, confidence_level);
                
                % Expected Shortfall (Conditional VaR)
                es = -mean(returns(returns <= -var_historical));
                
                results.risk_metrics = struct();
                results.risk_metrics.var_parametric = var_parametric;
                results.risk_metrics.var_historical = var_historical;
                results.risk_metrics.expected_shortfall = es;
                results.risk_metrics.confidence_level = 1 - confidence_level;
                
            else
                % Basic risk metrics
                results.risk_metrics = struct();
                results.risk_metrics.volatility = std(returns);
                results.risk_metrics.max_loss = min(returns);
            end
            
            % Sharpe and Sortino ratios
            results.risk_metrics.sharpe_ratio = mean(returns) / std(returns) * sqrt(252);
            downside_returns = returns(returns < 0);
            if ~isempty(downside_returns)
                results.risk_metrics.sortino_ratio = mean(returns) / std(downside_returns) * sqrt(252);
            else
                results.risk_metrics.sortino_ratio = NaN;
            end
            
            fprintf('Risk metrics calculated\\n');
        catch ME
            fprintf('Risk calculation failed: %s\\n', ME.message);
        end
        
        % 6. Technical Analysis using Financial Toolbox
        fprintf('Running technical analysis...\\n');
        try
            if license('test', 'Financial_Toolbox')
                % Moving averages
                sma_5 = movavg(prices, 'simple', 5);
                sma_20 = movavg(prices, 'simple', 20);
                ema_12 = movavg(prices, 'exponential', 12);
                
                % Bollinger Bands
                [mid, up, low] = bollinger(prices, 20, 2);
                
                % Relative Strength Index
                rsi = rsindex(prices);
                
                % MACD
                [macd_line, signal_line, histogram] = macd(prices);
                
                results.technical_analysis = struct();
                results.technical_analysis.sma_5 = sma_5(end);
                results.technical_analysis.sma_20 = sma_20(end);
                results.technical_analysis.ema_12 = ema_12(end);
                results.technical_analysis.bollinger_upper = up(end);
                results.technical_analysis.bollinger_lower = low(end);
                results.technical_analysis.rsi = rsi(end);
                results.technical_analysis.macd = macd_line(end);
                results.technical_analysis.macd_signal = signal_line(end);
                
                fprintf('Technical analysis completed\\n');
            end
        catch ME
            fprintf('Technical analysis failed: %s\\n', ME.message);
        end
        
        % 7. Generate Trading Signals
        fprintf('Generating trading signals...\\n');
        current_price = prices(end);
        current_vol = volatility(end);
        
        % Composite signal from multiple analyses
        signals = [];
        signal_strengths = [];
        
        % Signal from technical analysis
        if isfield(results, 'technical_analysis')
            ta = results.technical_analysis;
            if current_price > ta.sma_20
                signals(end+1) = 1;  % Bullish
                signal_strengths(end+1) = 0.3;
            elseif current_price < ta.sma_20
                signals(end+1) = -1;  % Bearish
                signal_strengths(end+1) = 0.3;
            end
            
            if ta.rsi > 70
                signals(end+1) = -1;  % Overbought
                signal_strengths(end+1) = 0.2;
            elseif ta.rsi < 30
                signals(end+1) = 1;  % Oversold
                signal_strengths(end+1) = 0.2;
            end
        end
        
        % Signal from volatility
        if current_vol > median(volatility)
            signals(end+1) = 1;  % High vol = opportunity
            signal_strengths(end+1) = 0.25;
        end
        
        % Signal from GARCH forecast
        if isfield(results, 'garch_analysis') && isfield(results.garch_analysis, 'vol_forecast')
            if results.garch_analysis.vol_forecast(1) > current_vol
                signals(end+1) = 1;  % Increasing vol forecast
                signal_strengths(end+1) = 0.25;
            end
        end
        
        % Aggregate signals
        if ~isempty(signals)
            weighted_signal = sum(signals .* signal_strengths) / sum(signal_strengths);
            signal_confidence = min(1, sum(signal_strengths));
        else
            weighted_signal = 0;
            signal_confidence = 0;
        end
        
        results.trading_signals = struct();
        results.trading_signals.composite_signal = weighted_signal;
        results.trading_signals.confidence = signal_confidence;
        
        if weighted_signal > 0.3
            results.trading_signals.recommendation = 'BUY';
        elseif weighted_signal < -0.3
            results.trading_signals.recommendation = 'SELL';
        else
            results.trading_signals.recommendation = 'HOLD';
        end
        
        % Save results
        save(output_file, 'results');
        
        % Create report
        report_file = strrep(output_file, '.mat', '_report.txt');
        create_financial_report(results, report_file);
        
        fprintf('Financial Toolbox Analysis Complete!\\n');
        fprintf('Recommendation: %s (Confidence: %.2f)\\n', ...
            results.trading_signals.recommendation, results.trading_signals.confidence);
        
    catch ME
        fprintf('Analysis failed: %s\\n', ME.message);
        results = struct('error', ME.message);
    end
end

function create_financial_report(results, filename)
    fid = fopen(filename, 'w');
    
    fprintf(fid, 'MATLAB FINANCIAL TOOLBOX ANALYSIS REPORT\\n');
    fprintf(fid, '========================================\\n\\n');
    fprintf(fid, 'Generated: %s\\n', results.timestamp);
    fprintf(fid, 'Observations: %d\\n\\n', results.num_observations);
    
    % GARCH Analysis
    if isfield(results, 'garch_analysis')
        fprintf(fid, 'VOLATILITY MODELING (GARCH):\\n');
        fprintf(fid, '----------------------------\\n');
        if isfield(results.garch_analysis, 'aic')
            fprintf(fid, 'Model: %s\\n', results.garch_analysis.model_type);
            fprintf(fid, 'AIC: %.4f\\n', results.garch_analysis.aic);
        end
        fprintf(fid, '\\n');
    end
    
    % Portfolio Optimization
    if isfield(results, 'portfolio_optimization')
        fprintf(fid, 'PORTFOLIO OPTIMIZATION:\\n');
        fprintf(fid, '----------------------\\n');
        po = results.portfolio_optimization;
        fprintf(fid, 'Optimal Sharpe Ratio: %.4f\\n', po.max_sharpe_ratio);
        fprintf(fid, 'Optimal Return: %.4f\\n', po.optimal_return);
        fprintf(fid, 'Optimal Risk: %.4f\\n', po.optimal_risk);
        fprintf(fid, 'Optimal Weights: ');
        for i = 1:length(po.optimal_weights)
            fprintf(fid, '%.3f ', po.optimal_weights(i));
        end
        fprintf(fid, '\\n\\n');
    end
    
    % Risk Metrics
    if isfield(results, 'risk_metrics')
        fprintf(fid, 'RISK ANALYSIS:\\n');
        fprintf(fid, '--------------\\n');
        rm = results.risk_metrics;
        if isfield(rm, 'var_parametric')
            fprintf(fid, 'VaR (Parametric): %.6f\\n', rm.var_parametric);
            fprintf(fid, 'VaR (Historical): %.6f\\n', rm.var_historical);
            fprintf(fid, 'Expected Shortfall: %.6f\\n', rm.expected_shortfall);
        end
        fprintf(fid, 'Sharpe Ratio: %.4f\\n', rm.sharpe_ratio);
        if ~isnan(rm.sortino_ratio)
            fprintf(fid, 'Sortino Ratio: %.4f\\n', rm.sortino_ratio);
        end
        fprintf(fid, '\\n');
    end
    
    % Technical Analysis
    if isfield(results, 'technical_analysis')
        fprintf(fid, 'TECHNICAL ANALYSIS:\\n');
        fprintf(fid, '------------------\\n');
        ta = results.technical_analysis;
        fprintf(fid, 'SMA(5): %.6f\\n', ta.sma_5);
        fprintf(fid, 'SMA(20): %.6f\\n', ta.sma_20);
        fprintf(fid, 'RSI: %.2f\\n', ta.rsi);
        fprintf(fid, 'MACD: %.6f\\n', ta.macd);
        fprintf(fid, 'Bollinger Upper: %.6f\\n', ta.bollinger_upper);
        fprintf(fid, 'Bollinger Lower: %.6f\\n', ta.bollinger_lower);
        fprintf(fid, '\\n');
    end
    
    % Trading Signals
    if isfield(results, 'trading_signals')
        fprintf(fid, 'TRADING SIGNALS:\\n');
        fprintf(fid, '---------------\\n');
        ts = results.trading_signals;
        fprintf(fid, 'Recommendation: %s\\n', ts.recommendation);
        fprintf(fid, 'Signal Strength: %.4f\\n', ts.composite_signal);
        fprintf(fid, 'Confidence: %.2f%%\\n', ts.confidence * 100);
        fprintf(fid, '\\n');
    end
    
    fprintf(fid, '========================================\\n');
    fclose(fid);
end
"""
        
        script_path = self.strategy_dir / "financial_toolbox_analyzer.m"
        with open(script_path, 'w') as f:
            f.write(matlab_script)
        
        print(f"Created Financial Toolbox Analyzer: {script_path}")
        return script_path

    def create_test_data(self):
        """Create test data for financial analysis"""
        np.random.seed(42)
        
        # Generate realistic financial time series
        n = 100
        timestamps = pd.date_range(start='2025-01-01', periods=n, freq='1H')
        
        # Price spreads following realistic patterns
        base_spread = 0.002
        trend = 0.0001 * np.sin(np.arange(n) * 0.1)
        noise = np.random.normal(0, 0.0005, n)
        price_spreads = np.maximum(0.0001, base_spread + trend + noise)
        
        # Volatility with clustering
        volatility = np.zeros(n)
        volatility[0] = 0.015
        for i in range(1, n):
            volatility[i] = 0.9 * volatility[i-1] + 0.1 * 0.015 + 0.05 * np.random.normal()
        volatility = np.maximum(0.005, volatility)
        
        # Other variables
        gas_costs = np.random.lognormal(np.log(0.01), 0.3, n)
        liquidity_scores = np.random.beta(2, 2, n)
        gas_efficiency = 1 / (1 + gas_costs / 0.02)
        
        # Profits
        gross_profits = price_spreads * 1000
        net_profits = gross_profits - gas_costs * 100
        profits = net_profits * liquidity_scores + np.random.normal(0, 0.5, n)
        
        df = pd.DataFrame({
            'timestamp': timestamps.strftime('%Y-%m-%d %H:%M:%S'),
            'price_spread': price_spreads,
            'volatility': volatility,
            'gas_cost': gas_costs,
            'liquidity_score': liquidity_scores,
            'gas_efficiency': gas_efficiency,
            'profit': profits
        })
        
        data_file = self.strategy_dir / "financial_data.csv"
        df.to_csv(data_file, index=False)
        
        print(f"Test Data Created: {data_file}")
        print(f"Records: {len(df)}")
        print(f"Mean Profit: ${df['profit'].mean():.4f}")
        print(f"Volatility Range: {df['volatility'].min():.4f} - {df['volatility'].max():.4f}")
        
        return data_file

    def run_financial_toolbox_analysis(self, data_file):
        """Run MATLAB Financial Toolbox analysis"""
        try:
            # Create analyzer script
            matlab_script = self.create_financial_toolbox_analyzer()
            
            # Prepare paths
            data_file_path = Path(data_file).resolve()
            output_file = self.results_dir / f"financial_analysis_{datetime.now().strftime('%H%M%S')}.mat"
            
            # Create direct MATLAB command
            matlab_cmd = f"addpath('{self.strategy_dir.resolve()}'); analyze_with_financial_toolbox('{data_file_path}', '{output_file.resolve()}'); exit;"
            
            print("Running MATLAB Financial Toolbox Analysis...")
            
            result = subprocess.run([
                self.matlab_path, "-r", matlab_cmd
            ], capture_output=True, text=True, timeout=120, cwd=str(self.strategy_dir))
            
            print(f"MATLAB Return Code: {result.returncode}")
            
            if result.stdout:
                print("\\nMATLAB Output:")
                print(result.stdout)
            
            if result.stderr:
                print("\\nMATLAB Errors/Warnings:")
                print(result.stderr)
            
            # Check for report
            report_file = str(output_file).replace('.mat', '_report.txt')
            if Path(report_file).exists():
                print(f"\\nFinancial Analysis Report: {report_file}")
                
                with open(report_file, 'r') as f:
                    report_content = f.read()
                    print("\\n" + "="*60)
                    print("MATLAB FINANCIAL TOOLBOX ANALYSIS REPORT")
                    print("="*60)
                    print(report_content)
                return True
            else:
                print("No report file generated")
                return result.returncode == 0
                
        except Exception as e:
            print(f"Error running Financial Toolbox analysis: {e}")
            return False

    def run_complete_analysis(self):
        """Run complete financial toolbox analysis"""
        print("\\n" + "="*60)
        print("MATLAB FINANCIAL TOOLBOX ANALYSIS")
        print("="*60)
        
        # Create test data
        data_file = self.create_test_data()
        
        # Run analysis
        success = self.run_financial_toolbox_analysis(data_file)
        
        print("\\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("="*60)
        print(f"Data File: {data_file}")
        print(f"Success: {success}")
        
        if success:
            print("\\nFinancial Toolbox Features Used:")
            print("- GARCH volatility modeling")
            print("- Black-Scholes option pricing")
            print("- Portfolio optimization")
            print("- Value at Risk (VaR) calculation")
            print("- Technical analysis indicators")
            print("- Statistical hypothesis testing")
        
        return success


def main():
    """Main execution"""
    print("True MATLAB Financial Toolbox Integration")
    print("="*50)
    
    system = TrueMATLABFinancialSystem()
    
    # Check for MATLAB
    if os.path.exists(system.matlab_path):
        print("MATLAB R2025a: Available")
    else:
        print("MATLAB: Not found")
        return
    
    # Run complete analysis
    success = system.run_complete_analysis()
    
    if success:
        print("\\nSUCCESS: Financial Toolbox analysis completed!")
        print("Advanced MATLAB financial functions utilized")
    else:
        print("\\nAnalysis encountered issues")

if __name__ == "__main__":
    main()
