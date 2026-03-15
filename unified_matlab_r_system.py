#!/usr/bin/env python3
"""
Unified MATLAB + R Analytics System
Combining MATLAB's optimization power with R's statistical expertise
"""

import subprocess
import json
import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import time
from datetime import datetime
import traceback

class UnifiedAnalyticsSystem:
    """Unified system combining MATLAB and R analytics"""
    
    def __init__(self, matlab_path="matlab", r_path="R"):
        """Initialize unified analytics system"""
        self.matlab_path = matlab_path
        self.r_path = r_path
        self.temp_dir = Path(tempfile.gettempdir()) / "unified_analytics"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Check tool availability
        self.matlab_available = self._check_matlab()
        self.r_available = self._check_r()
        
        print("🏗️ UNIFIED MATLAB + R ANALYTICS SYSTEM")
        print(f"🔧 MATLAB Status: {'✅ Available' if self.matlab_available else '❌ Not Available'}")
        print(f"🔬 R Status: {'✅ Available' if self.r_available else '❌ Not Available'}")
        print(f"📁 Temp directory: {self.temp_dir}")
    
    def _check_matlab(self):
        """Check MATLAB availability"""
        try:
            result = subprocess.run(
                [self.matlab_path, "-batch", "disp('MATLAB OK'); exit"],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
        except:
            return False
    
    def _check_r(self):
        """Check R availability"""
        try:
            result = subprocess.run(
                [self.r_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def run_matlab_optimization(self, returns_data, risk_free_rate=0.02):
        """Run MATLAB portfolio optimization"""
        print("🔧 Running MATLAB portfolio optimization...")
        
        if not self.matlab_available:
            print("❌ MATLAB not available - using synthetic results")
            return self._generate_synthetic_matlab_results()
        
        # Prepare data for MATLAB
        if isinstance(returns_data, pd.DataFrame):
            returns_matrix = returns_data.values
        else:
            returns_matrix = np.array(returns_data)
        
        if len(returns_matrix.shape) == 1:
            # Single asset - create synthetic multi-asset scenario
            n_assets = 5
            returns_matrix = np.column_stack([
                returns_matrix,
                returns_matrix + np.random.normal(0, 0.01, len(returns_matrix)),
                returns_matrix + np.random.normal(0, 0.015, len(returns_matrix)),
                returns_matrix + np.random.normal(0, 0.02, len(returns_matrix)),
                returns_matrix + np.random.normal(0, 0.008, len(returns_matrix))
            ])
        
        # Save data for MATLAB
        data_file = self.temp_dir / "returns_data.csv"
        pd.DataFrame(returns_matrix).to_csv(data_file, index=False)
        
        # Create MATLAB script
        matlab_script = f"""
% Portfolio Optimization with MATLAB
data = readtable('{data_file.as_posix()}');
returns = table2array(data);

% Remove any NaN or infinite values
returns = returns(all(isfinite(returns), 2), :);

fprintf('Portfolio optimization with %d assets and %d observations\\n', size(returns, 2), size(returns, 1));

% Calculate expected returns and covariance
mu = mean(returns)';
sigma = cov(returns);

% Risk-free rate
rf = {risk_free_rate};

% Portfolio optimization using Financial Toolbox
try
    % Create portfolio object
    p = Portfolio('AssetMean', mu, 'AssetCovar', sigma, 'RiskFreeRate', rf);
    
    % Add constraints (long-only, fully invested)
    p = setDefaultConstraints(p);
    
    % Find efficient frontier
    nPorts = 20;
    frontier_weights = estimateFrontier(p, nPorts);
    frontier_risks = estimatePortRisk(p, frontier_weights);
    frontier_returns = estimatePortReturn(p, frontier_weights);
    
    % Find optimal portfolios
    max_sharpe_weights = estimateMaxSharpeRatio(p);
    min_var_weights = estimateMinVariance(p);
    
    % Calculate metrics for optimal portfolios
    max_sharpe_return = estimatePortReturn(p, max_sharpe_weights);
    max_sharpe_risk = estimatePortRisk(p, max_sharpe_weights);
    max_sharpe_ratio = (max_sharpe_return - rf) / max_sharpe_risk;
    
    min_var_return = estimatePortReturn(p, min_var_weights);
    min_var_risk = estimatePortRisk(p, min_var_weights);
    min_var_ratio = (min_var_return - rf) / min_var_risk;
    
    fprintf('\\n=== PORTFOLIO OPTIMIZATION RESULTS ===\\n');
    fprintf('Max Sharpe Portfolio:\\n');
    fprintf('  Expected Return: %.4f (%.2f%%)\\n', max_sharpe_return, max_sharpe_return*100);
    fprintf('  Risk (Volatility): %.4f (%.2f%%)\\n', max_sharpe_risk, max_sharpe_risk*100);
    fprintf('  Sharpe Ratio: %.4f\\n', max_sharpe_ratio);
    
    fprintf('Min Variance Portfolio:\\n');
    fprintf('  Expected Return: %.4f (%.2f%%)\\n', min_var_return, min_var_return*100);
    fprintf('  Risk (Volatility): %.4f (%.2f%%)\\n', min_var_risk, min_var_risk*100);
    fprintf('  Sharpe Ratio: %.4f\\n', min_var_ratio);
    
    % Save results
    results_file = '{self.temp_dir.as_posix()}/matlab_results.json';
    results = struct();
    results.max_sharpe_return = max_sharpe_return;
    results.max_sharpe_risk = max_sharpe_risk;
    results.max_sharpe_ratio = max_sharpe_ratio;
    results.max_sharpe_weights = max_sharpe_weights';
    results.min_var_return = min_var_return;
    results.min_var_risk = min_var_risk;
    results.min_var_ratio = min_var_ratio;
    results.min_var_weights = min_var_weights';
    results.frontier_returns = frontier_returns';
    results.frontier_risks = frontier_risks';
    results.success = true;
    
    % Convert to JSON-like output
    fprintf('\\n=== MATLAB JSON RESULTS ===\\n');
    fprintf('{{\\n');
    fprintf('  "max_sharpe_return": %.6f,\\n', max_sharpe_return);
    fprintf('  "max_sharpe_risk": %.6f,\\n', max_sharpe_risk);
    fprintf('  "max_sharpe_ratio": %.6f,\\n', max_sharpe_ratio);
    fprintf('  "min_var_return": %.6f,\\n', min_var_return);
    fprintf('  "min_var_risk": %.6f,\\n', min_var_risk);
    fprintf('  "min_var_ratio": %.6f,\\n', min_var_ratio);
    fprintf('  "success": true\\n');
    fprintf('}}\\n');
    
    % Save weights to file
    writematrix(max_sharpe_weights, '{self.temp_dir.as_posix()}/max_sharpe_weights.csv');
    writematrix(min_var_weights, '{self.temp_dir.as_posix()}/min_var_weights.csv');
    
catch ME
    fprintf('Error in portfolio optimization: %s\\n', ME.message);
    fprintf('{{\\n');
    fprintf('  "success": false,\\n');
    fprintf('  "error": "%s"\\n', ME.message);
    fprintf('}}\\n');
end

exit;
"""
        
        script_file = self.temp_dir / "matlab_optimization.m"
        with open(script_file, 'w') as f:
            f.write(matlab_script)
        
        try:
            result = subprocess.run(
                [self.matlab_path, "-batch", f"run('{script_file.as_posix()}')"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                output = result.stdout
                print("✅ MATLAB optimization completed")
                
                # Parse JSON results
                if "=== MATLAB JSON RESULTS ===" in output:
                    json_start = output.find("{", output.find("=== MATLAB JSON RESULTS ==="))
                    json_end = output.find("}", json_start) + 1
                    if json_start > 0 and json_end > json_start:
                        try:
                            json_str = output[json_start:json_end]
                            results = json.loads(json_str)
                            results['full_output'] = output
                            return results
                        except json.JSONDecodeError:
                            pass
                
                return {'success': True, 'message': 'Optimization completed', 'full_output': output}
            else:
                print("❌ MATLAB optimization failed")
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            print(f"❌ MATLAB optimization exception: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_r_garch_analysis(self, returns_data):
        """Run R GARCH volatility analysis"""
        print("🔬 Running R GARCH volatility analysis...")
        
        if not self.r_available:
            print("❌ R not available - using synthetic results")
            return self._generate_synthetic_r_results()
        
        # Prepare data
        if isinstance(returns_data, pd.DataFrame):
            returns = returns_data.iloc[:, 0].values  # Use first column
        else:
            returns = np.array(returns_data)
        
        if len(returns.shape) > 1:
            returns = returns[:, 0]  # Use first column
        
        # Save data
        data_file = self.temp_dir / "r_returns_data.csv"
        pd.DataFrame({'returns': returns}).to_csv(data_file, index=False)
        
        # Create R script
        r_script = f'''
# Load required packages (install if needed)
packages <- c("rugarch", "forecast", "PerformanceAnalytics")
for(pkg in packages) {{
    if(!require(pkg, character.only=TRUE, quietly=TRUE)) {{
        install.packages(pkg, repos="https://cran.rstudio.com/", quiet=TRUE)
        library(pkg, character.only=TRUE)
    }}
}}

# Load data
data <- read.csv("{data_file.as_posix()}")
returns <- data$returns
returns <- na.omit(returns[is.finite(returns)])

cat("R GARCH Analysis for", length(returns), "observations\\n")

# GARCH(1,1) specification and fitting
spec <- ugarchspec(
    variance.model = list(model = "sGARCH", garchOrder = c(1, 1)),
    mean.model = list(armaOrder = c(1, 1), include.mean = TRUE),
    distribution.model = "norm"
)

tryCatch({{
    # Fit GARCH model
    fit <- ugarchfit(spec, returns, solver = "hybrid")
    
    # Extract key metrics
    volatility <- sigma(fit)
    current_vol <- tail(volatility, 1)
    annualized_vol <- current_vol * sqrt(252)
    
    # Forecast
    forecast_vol <- ugarchforecast(fit, n.ahead = 1)
    next_vol <- sigma(forecast_vol)[1]
    
    # Performance metrics
    sharpe <- SharpeRatio(returns, annualize = TRUE)
    sortino <- SortinoRatio(returns)
    max_dd <- maxDrawdown(returns)
    var_95 <- VaR(returns, p = 0.95)
    
    cat("\\n=== R GARCH RESULTS ===\\n")
    cat("Current Volatility:", current_vol, "\\n")
    cat("Annualized Volatility:", annualized_vol, "\\n")
    cat("Next Period Forecast:", next_vol, "\\n")
    cat("Sharpe Ratio:", sharpe, "\\n")
    cat("Sortino Ratio:", sortino, "\\n")
    cat("Max Drawdown:", max_dd, "\\n")
    cat("95% VaR:", var_95, "\\n")
    
    # JSON output
    cat("\\n=== R JSON RESULTS ===\\n")
    cat("{{\\n")
    cat('"current_volatility":', current_vol, ",\\n")
    cat('"annualized_volatility":', annualized_vol, ",\\n")
    cat('"volatility_forecast":', next_vol, ",\\n")
    cat('"sharpe_ratio":', sharpe, ",\\n")
    cat('"sortino_ratio":', sortino, ",\\n")
    cat('"max_drawdown":', max_dd, ",\\n")
    cat('"var_95":', var_95, ",\\n")
    cat('"success": true\\n')
    cat("}}\\n")
    
}}, error = function(e) {{
    cat("Error in R GARCH analysis:", e$message, "\\n")
    cat("{{\\n")
    cat('"success": false,\\n')
    cat('"error": "', e$message, '"\\n')
    cat("}}\\n")
}})
'''
        
        script_file = self.temp_dir / "r_garch_analysis.R"
        with open(script_file, 'w') as f:
            f.write(r_script)
        
        try:
            result = subprocess.run(
                [self.r_path, "--vanilla", "--slave", "-f", str(script_file)],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                output = result.stdout
                print("✅ R GARCH analysis completed")
                
                # Parse JSON results
                if "=== R JSON RESULTS ===" in output:
                    json_start = output.find("{", output.find("=== R JSON RESULTS ==="))
                    json_end = output.find("}", json_start) + 1
                    if json_start > 0 and json_end > json_start:
                        try:
                            json_str = output[json_start:json_end]
                            results = json.loads(json_str)
                            results['full_output'] = output
                            return results
                        except json.JSONDecodeError:
                            pass
                
                return {'success': True, 'message': 'GARCH analysis completed', 'full_output': output}
            else:
                print("❌ R GARCH analysis failed")
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            print(f"❌ R GARCH exception: {e}")
            return {'success': False, 'error': str(e)}
    
    def _generate_synthetic_matlab_results(self):
        """Generate synthetic MATLAB results for demo purposes"""
        return {
            'success': True,
            'max_sharpe_return': 0.1247,
            'max_sharpe_risk': 0.0823,
            'max_sharpe_ratio': 1.2583,
            'min_var_return': 0.0891,
            'min_var_risk': 0.0654,
            'min_var_ratio': 1.0564,
            'synthetic': True,
            'message': 'Synthetic MATLAB results (install MATLAB for real analysis)'
        }
    
    def _generate_synthetic_r_results(self):
        """Generate synthetic R results for demo purposes"""
        return {
            'success': True,
            'current_volatility': 0.0187,
            'annualized_volatility': 0.2968,
            'volatility_forecast': 0.0195,
            'sharpe_ratio': 0.9834,
            'sortino_ratio': 1.2456,
            'max_drawdown': -0.0834,
            'var_95': -0.0312,
            'synthetic': True,
            'message': 'Synthetic R results (install R for real analysis)'
        }
    
    def run_combined_analysis(self, returns_data):
        """Run combined MATLAB + R analysis"""
        print("\n" + "="*80)
        print("🔗 COMBINED MATLAB + R ANALYSIS")
        print("="*80)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'data_summary': {
                'observations': len(returns_data),
                'mean_return': float(np.mean(returns_data)),
                'volatility': float(np.std(returns_data)),
                'min_return': float(np.min(returns_data)),
                'max_return': float(np.max(returns_data))
            }
        }
        
        # Run MATLAB optimization
        matlab_results = self.run_matlab_optimization(returns_data)
        results['matlab_optimization'] = matlab_results
        
        # Run R GARCH analysis
        r_results = self.run_r_garch_analysis(returns_data)
        results['r_garch_analysis'] = r_results
        
        # Combine insights
        results['combined_insights'] = self._generate_combined_insights(matlab_results, r_results)
        
        return results
    
    def _generate_combined_insights(self, matlab_results, r_results):
        """Generate insights from combined MATLAB + R analysis"""
        insights = {
            'risk_assessment': 'Unknown',
            'opportunity_rating': 'Unknown',
            'recommendations': []
        }
        
        try:
            if matlab_results.get('success') and r_results.get('success'):
                matlab_sharpe = matlab_results.get('max_sharpe_ratio', 0)
                r_sharpe = r_results.get('sharpe_ratio', 0)
                r_vol = r_results.get('annualized_volatility', 0)
                
                # Risk assessment
                if r_vol < 0.15:
                    insights['risk_assessment'] = 'LOW'
                elif r_vol < 0.30:
                    insights['risk_assessment'] = 'MEDIUM'
                else:
                    insights['risk_assessment'] = 'HIGH'
                
                # Opportunity rating
                avg_sharpe = (matlab_sharpe + r_sharpe) / 2
                if avg_sharpe > 1.5:
                    insights['opportunity_rating'] = 'EXCELLENT'
                elif avg_sharpe > 1.0:
                    insights['opportunity_rating'] = 'GOOD'
                elif avg_sharpe > 0.5:
                    insights['opportunity_rating'] = 'MODERATE'
                else:
                    insights['opportunity_rating'] = 'POOR'
                
                # Recommendations
                if matlab_sharpe > 1.0:
                    insights['recommendations'].append('Portfolio optimization shows strong risk-adjusted returns')
                if r_vol > 0.25:
                    insights['recommendations'].append('High volatility detected - consider hedging strategies')
                if r_results.get('var_95', 0) < -0.03:
                    insights['recommendations'].append('Significant downside risk - implement stop-loss mechanisms')
                
        except Exception as e:
            insights['error'] = str(e)
        
        return insights
    
    def create_comprehensive_demo(self):
        """Create comprehensive demo showing MATLAB + R integration"""
        print("\n" + "="*100)
        print("🚀 UNIFIED MATLAB + R ANALYTICS COMPREHENSIVE DEMO")
        print("="*100)
        
        # Generate synthetic financial data
        np.random.seed(42)
        n_days = 252
        
        # Create realistic return series with volatility clustering
        returns = []
        vol = 0.02  # Initial volatility
        
        for i in range(n_days):
            # GARCH-like volatility process
            vol = 0.0001 + 0.05 * (returns[-1]**2 if returns else 0.0004) + 0.9 * vol
            return_today = np.random.normal(0.0008, vol)  # Slight positive drift
            returns.append(return_today)
        
        returns = np.array(returns)
        
        print(f"📊 Generated {len(returns)} days of synthetic return data")
        print(f"📈 Return statistics: Mean={returns.mean():.4f}, Std={returns.std():.4f}")
        print(f"📉 Return range: {returns.min():.4f} to {returns.max():.4f}")
        
        # Run combined analysis
        combined_results = self.run_combined_analysis(returns)
        
        # Display results
        self._display_results(combined_results)
        
        return combined_results
    
    def _display_results(self, results):
        """Display comprehensive results"""
        print("\n" + "="*100)
        print("📊 UNIFIED ANALYTICS RESULTS SUMMARY")
        print("="*100)
        
        print(f"🕐 Analysis Time: {results['timestamp']}")
        print(f"📈 Data Points: {results['data_summary']['observations']}")
        print(f"📊 Mean Return: {results['data_summary']['mean_return']:.4f}")
        print(f"📉 Volatility: {results['data_summary']['volatility']:.4f}")
        
        # MATLAB Results
        matlab = results.get('matlab_optimization', {})
        if matlab.get('success'):
            print(f"\n🔧 MATLAB PORTFOLIO OPTIMIZATION:")
            print(f"  📈 Max Sharpe Return: {matlab.get('max_sharpe_return', 0):.2%}")
            print(f"  📊 Max Sharpe Risk: {matlab.get('max_sharpe_risk', 0):.2%}")
            print(f"  ⚡ Max Sharpe Ratio: {matlab.get('max_sharpe_ratio', 0):.3f}")
            print(f"  🛡️ Min Var Return: {matlab.get('min_var_return', 0):.2%}")
            print(f"  📉 Min Var Risk: {matlab.get('min_var_risk', 0):.2%}")
            if matlab.get('synthetic'):
                print(f"  ⚠️ {matlab.get('message', 'Synthetic results')}")
        
        # R Results
        r_results = results.get('r_garch_analysis', {})
        if r_results.get('success'):
            print(f"\n🔬 R GARCH VOLATILITY ANALYSIS:")
            print(f"  📊 Current Volatility: {r_results.get('current_volatility', 0):.4f}")
            print(f"  📈 Annualized Volatility: {r_results.get('annualized_volatility', 0):.2%}")
            print(f"  🔮 Volatility Forecast: {r_results.get('volatility_forecast', 0):.4f}")
            print(f"  ⚡ Sharpe Ratio: {r_results.get('sharpe_ratio', 0):.3f}")
            print(f"  📉 Max Drawdown: {r_results.get('max_drawdown', 0):.2%}")
            print(f"  🚨 95% VaR: {r_results.get('var_95', 0):.3f}")
            if r_results.get('synthetic'):
                print(f"  ⚠️ {r_results.get('message', 'Synthetic results')}")
        
        # Combined Insights
        insights = results.get('combined_insights', {})
        if insights:
            print(f"\n🔗 COMBINED INSIGHTS:")
            print(f"  🛡️ Risk Assessment: {insights.get('risk_assessment', 'Unknown')}")
            print(f"  🎯 Opportunity Rating: {insights.get('opportunity_rating', 'Unknown')}")
            if insights.get('recommendations'):
                print(f"  💡 Recommendations:")
                for rec in insights['recommendations']:
                    print(f"    • {rec}")
        
        print(f"\n✅ UNIFIED MATLAB + R ANALYSIS COMPLETE!")
        
        # Tool status and next steps
        print(f"\n🔧 TOOL STATUS:")
        print(f"  MATLAB: {'✅ Operational' if self.matlab_available else '❌ Not Available'}")
        print(f"  R: {'✅ Operational' if self.r_available else '❌ Not Available'}")
        
        if not self.matlab_available or not self.r_available:
            print(f"\n📥 INSTALLATION GUIDES:")
            if not self.matlab_available:
                print("  MATLAB: https://www.mathworks.com/products/matlab.html")
            if not self.r_available:
                print("  R: https://cran.r-project.org/")
        
        print(f"\n🎯 PHASE 1 COMPLETE - NEXT STEPS:")
        print("1. Install missing tools (MATLAB/R) for full functionality")
        print("2. Proceed to Phase 2: Enhanced Dashboard Integration")
        print("3. Phase 3: AI/ML Enhancement (TensorFlow/QuantLib)")
        print("4. Phase 4: Professional Analytics (SPSS)")

def main():
    """Main function"""
    print("🚀 LAUNCHING UNIFIED MATLAB + R ANALYTICS SYSTEM")
    print("="*80)
    
    # Initialize system
    system = UnifiedAnalyticsSystem()
    
    # Run comprehensive demo
    results = system.create_comprehensive_demo()
    
    # Save results
    results_file = system.temp_dir / f"unified_results_{int(time.time())}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {results_file}")
    print("🎯 Phase 1 (R Integration) demonstration complete!")
    
    return results

if __name__ == "__main__":
    main()
