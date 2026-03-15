#!/usr/bin/env python3
"""
R Statistical Computing Integration
Advanced statistical modeling and econometric analysis using R
Following the proven MATLAB integration pattern
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

class RStatisticalIntegrator:
    """R integration for advanced statistical modeling and econometrics"""
    
    def __init__(self, r_executable="R"):
        """Initialize R integration
        
        Args:
            r_executable: Path to R executable (default: "R" if in PATH)
        """
        self.r_executable = r_executable
        self.temp_dir = Path(tempfile.gettempdir()) / "r_integration"
        self.temp_dir.mkdir(exist_ok=True)
        
        # R packages for financial analysis
        self.required_packages = [
            "quantmod",      # Financial data and analysis
            "PerformanceAnalytics",  # Risk and performance metrics
            "rugarch",       # GARCH models
            "forecast",      # Time series forecasting
            "vars",          # Vector autoregression
            "urca",          # Unit root and cointegration tests
            "tseries",       # Time series analysis
            "zoo",           # Time series objects
            "xts",           # Extensible time series
            "TTR",           # Technical trading rules
            "RQuantLib",     # QuantLib R interface
            "fGarch",        # Financial GARCH models
            "rmgarch",       # Multivariate GARCH
            "MTS",           # Multivariate time series
            "tidyquant"      # Tidy financial analysis
        ]
        
        print("🔬 R Statistical Integration Initialized")
        print(f"📁 Temp directory: {self.temp_dir}")
    
    def check_r_installation(self):
        """Check if R is properly installed and accessible"""
        try:
            result = subprocess.run(
                [self.r_executable, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print("✅ R is installed and accessible")
                print(f"Version info: {result.stdout.split('R version')[1].split(',')[0] if 'R version' in result.stdout else 'Unknown'}")
                return True
            else:
                print("❌ R installation issue")
                print(f"Error: {result.stderr}")
                return False
                
        except FileNotFoundError:
            print("❌ R not found in PATH")
            print("Install R from: https://cran.r-project.org/")
            print("Add R/bin to your system PATH")
            return False
        except Exception as e:
            print(f"❌ Error checking R: {e}")
            return False
    
    def install_required_packages(self):
        """Install required R packages for financial analysis"""
        print("📦 Installing required R packages...")
        
        # Create R script for package installation
        install_script = f"""
# Install required packages for financial analysis
packages <- c({', '.join([f'"{pkg}"' for pkg in self.required_packages])})

# Function to install if not already installed
install_if_missing <- function(pkg) {{
    if (!require(pkg, character.only = TRUE, quietly = TRUE)) {{
        cat("Installing", pkg, "\\n")
        install.packages(pkg, repos = "https://cran.rstudio.com/", quiet = TRUE)
        library(pkg, character.only = TRUE)
        return(TRUE)
    }} else {{
        cat(pkg, "already installed\\n")
        return(FALSE)
    }}
}}

# Install all packages
results <- sapply(packages, install_if_missing)
cat("Package installation complete\\n")
print(sessionInfo())
"""
        
        script_path = self.temp_dir / "install_packages.R"
        with open(script_path, 'w') as f:
            f.write(install_script)
        
        try:
            result = subprocess.run(
                [self.r_executable, "--vanilla", "--slave", "-f", str(script_path)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes for package installation
            )
            
            if result.returncode == 0:
                print("✅ R packages installed successfully")
                print("Installed packages for:")
                print("  • Financial data analysis (quantmod)")
                print("  • GARCH volatility modeling (rugarch, fGarch)")
                print("  • Performance analytics (PerformanceAnalytics)")
                print("  • Time series forecasting (forecast)")
                print("  • Econometric modeling (vars, urca)")
                return True
            else:
                print("⚠️ Some packages may not have installed correctly")
                print(f"Output: {result.stdout}")
                print(f"Errors: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error installing packages: {e}")
            return False
    
    def run_garch_analysis(self, price_data, asset_name="Asset"):
        """Run GARCH volatility modeling using R"""
        print(f"📊 Running GARCH volatility analysis for {asset_name}...")
        
        # Prepare data
        if isinstance(price_data, (list, np.ndarray)):
            returns = np.diff(np.log(price_data))
        elif isinstance(price_data, pd.Series):
            returns = np.diff(np.log(price_data.values))
        else:
            returns = price_data
        
        # Save data to CSV for R
        data_path = self.temp_dir / f"returns_data_{int(time.time())}.csv"
        pd.DataFrame({'returns': returns}).to_csv(data_path, index=False)
        
        # Create R script for GARCH analysis
        r_script = f'''
library(rugarch)
library(fGarch)
library(quantmod)

# Load data
data <- read.csv("{data_path.as_posix()}")
returns <- data$returns

# Remove any infinite or NA values
returns <- returns[is.finite(returns)]
returns <- na.omit(returns)

cat("Data loaded:", length(returns), "observations\\n")

# GARCH(1,1) model specification
spec <- ugarchspec(
    variance.model = list(model = "sGARCH", garchOrder = c(1, 1)),
    mean.model = list(armaOrder = c(1, 1), include.mean = TRUE),
    distribution.model = "norm"
)

# Fit GARCH model
tryCatch({{
    fit <- ugarchfit(spec, returns)
    
    # Extract results
    volatility <- sigma(fit)
    conditional_mean <- fitted(fit)
    
    # Model statistics
    cat("\\n=== GARCH(1,1) Model Results ===\\n")
    cat("Log-likelihood:", likelihood(fit), "\\n")
    cat("AIC:", infocriteria(fit)[1], "\\n")
    cat("BIC:", infocriteria(fit)[2], "\\n")
    
    # Current volatility forecast
    forecast_vol <- ugarchforecast(fit, n.ahead = 1)
    next_vol <- sigma(forecast_vol)[1]
    cat("Next period volatility forecast:", next_vol, "\\n")
    
    # Risk metrics
    current_vol <- tail(volatility, 1)
    annualized_vol <- current_vol * sqrt(252)
    cat("Current volatility:", current_vol, "\\n")
    cat("Annualized volatility:", annualized_vol, "\\n")
    
    # VaR calculation (95% confidence)
    var_95 <- quantile(returns, 0.05)
    cat("95% VaR:", var_95, "\\n")
    
    # Save results
    results <- data.frame(
        volatility = as.numeric(volatility),
        conditional_mean = as.numeric(conditional_mean)
    )
    
    write.csv(results, "{self.temp_dir.as_posix()}/garch_results.csv", row.names = FALSE)
    
    # Summary statistics
    summary_stats <- list(
        log_likelihood = likelihood(fit),
        aic = infocriteria(fit)[1],
        bic = infocriteria(fit)[2],
        current_volatility = current_vol,
        annualized_volatility = annualized_vol,
        next_period_forecast = next_vol,
        var_95 = var_95
    )
    
    # Save summary as JSON-like format
    cat("\\n=== SUMMARY JSON ===\\n")
    cat("{{\\n")
    cat('"log_likelihood":', likelihood(fit), ",\\n")
    cat('"aic":', infocriteria(fit)[1], ",\\n")
    cat('"bic":', infocriteria(fit)[2], ",\\n")
    cat('"current_volatility":', current_vol, ",\\n")
    cat('"annualized_volatility":', annualized_vol, ",\\n")
    cat('"next_period_forecast":', next_vol, ",\\n")
    cat('"var_95":', var_95, "\\n")
    cat("}}\\n")
    
}}, error = function(e) {{
    cat("Error in GARCH modeling:", e$message, "\\n")
}})
'''
        
        script_path = self.temp_dir / f"garch_analysis_{int(time.time())}.R"
        with open(script_path, 'w') as f:
            f.write(r_script)
        
        try:
            result = subprocess.run(
                [self.r_executable, "--vanilla", "--slave", "-f", str(script_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                output = result.stdout
                print("✅ GARCH analysis completed successfully")
                
                # Parse results
                if "=== SUMMARY JSON ===" in output:
                    json_start = output.find("{", output.find("=== SUMMARY JSON ==="))
                    json_end = output.find("}", json_start) + 1
                    if json_start > 0 and json_end > json_start:
                        try:
                            json_str = output[json_start:json_end]
                            summary = json.loads(json_str)
                            return {
                                'success': True,
                                'summary': summary,
                                'full_output': output,
                                'data_file': f"{self.temp_dir}/garch_results.csv"
                            }
                        except json.JSONDecodeError:
                            pass
                
                return {
                    'success': True,
                    'summary': {'message': 'GARCH analysis completed'},
                    'full_output': output,
                    'data_file': f"{self.temp_dir}/garch_results.csv"
                }
            else:
                print("❌ Error in GARCH analysis")
                print(f"Error output: {result.stderr}")
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            print(f"❌ Exception in GARCH analysis: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_performance_analytics(self, returns_data, benchmark_returns=None):
        """Run comprehensive performance analytics using R PerformanceAnalytics"""
        print("📈 Running performance analytics...")
        
        # Prepare data
        if isinstance(returns_data, (list, np.ndarray)):
            returns = np.array(returns_data)
        elif isinstance(returns_data, pd.Series):
            returns = returns_data.values
        else:
            returns = returns_data
        
        # Save data
        data_path = self.temp_dir / f"performance_data_{int(time.time())}.csv"
        if benchmark_returns is not None:
            df = pd.DataFrame({
                'portfolio_returns': returns,
                'benchmark_returns': benchmark_returns
            })
        else:
            df = pd.DataFrame({'portfolio_returns': returns})
        
        df.to_csv(data_path, index=False)
        
        # Create R script
        has_benchmark = benchmark_returns is not None
        benchmark_code = '''
benchmark <- data$benchmark_returns
benchmark <- na.omit(benchmark[is.finite(benchmark)])
''' if has_benchmark else 'benchmark <- NULL'
        
        r_script = f'''
library(PerformanceAnalytics)
library(quantmod)

# Load data
data <- read.csv("{data_path.as_posix()}")
returns <- data$portfolio_returns
returns <- na.omit(returns[is.finite(returns)])

{benchmark_code}

cat("Performance Analytics for", length(returns), "observations\\n")

# Basic performance metrics
sharpe_ratio <- SharpeRatio(returns, annualize = TRUE)
sortino_ratio <- SortinoRatio(returns)
calmar_ratio <- CalmarRatio(returns)
max_drawdown <- maxDrawdown(returns)

# Risk metrics
var_95 <- VaR(returns, p = 0.95)
cvar_95 <- CVaR(returns, p = 0.95)
downside_dev <- DownsideDeviation(returns)

# Return metrics
total_return <- Return.cumulative(returns)
annualized_return <- Return.annualized(returns)
annualized_vol <- StdDev.annualized(returns)

cat("\\n=== PERFORMANCE METRICS ===\\n")
cat("Total Return:", total_return, "\\n")
cat("Annualized Return:", annualized_return, "\\n")
cat("Annualized Volatility:", annualized_vol, "\\n")
cat("Sharpe Ratio:", sharpe_ratio, "\\n")
cat("Sortino Ratio:", sortino_ratio, "\\n")
cat("Calmar Ratio:", calmar_ratio, "\\n")
cat("Maximum Drawdown:", max_drawdown, "\\n")
cat("95% VaR:", var_95, "\\n")
cat("95% CVaR:", cvar_95, "\\n")
cat("Downside Deviation:", downside_dev, "\\n")

# JSON output
cat("\\n=== PERFORMANCE JSON ===\\n")
cat("{{\\n")
cat('"total_return":', total_return, ",\\n")
cat('"annualized_return":', annualized_return, ",\\n")
cat('"annualized_volatility":', annualized_vol, ",\\n")
cat('"sharpe_ratio":', sharpe_ratio, ",\\n")
cat('"sortino_ratio":', sortino_ratio, ",\\n")
cat('"calmar_ratio":', calmar_ratio, ",\\n")
cat('"max_drawdown":', max_drawdown, ",\\n")
cat('"var_95":', var_95, ",\\n")
cat('"cvar_95":', cvar_95, ",\\n")
cat('"downside_deviation":', downside_dev, "\\n")
cat("}}\\n")
'''
        
        script_path = self.temp_dir / f"performance_analysis_{int(time.time())}.R"
        with open(script_path, 'w') as f:
            f.write(r_script)
        
        try:
            result = subprocess.run(
                [self.r_executable, "--vanilla", "--slave", "-f", str(script_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                output = result.stdout
                print("✅ Performance analytics completed")
                
                # Parse JSON results
                if "=== PERFORMANCE JSON ===" in output:
                    json_start = output.find("{", output.find("=== PERFORMANCE JSON ==="))
                    json_end = output.find("}", json_start) + 1
                    if json_start > 0 and json_end > json_start:
                        try:
                            json_str = output[json_start:json_end]
                            metrics = json.loads(json_str)
                            return {
                                'success': True,
                                'metrics': metrics,
                                'full_output': output
                            }
                        except json.JSONDecodeError:
                            pass
                
                return {
                    'success': True, 
                    'metrics': {'message': 'Performance analysis completed'},
                    'full_output': output
                }
            else:
                print("❌ Error in performance analytics")
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            print(f"❌ Exception in performance analytics: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_econometric_analysis(self, time_series_data, variable_name="Series"):
        """Run econometric analysis including unit root tests and ARIMA modeling"""
        print(f"🔬 Running econometric analysis for {variable_name}...")
        
        # Prepare data
        if isinstance(time_series_data, (list, np.ndarray)):
            data = np.array(time_series_data)
        elif isinstance(time_series_data, pd.Series):
            data = time_series_data.values
        else:
            data = time_series_data
        
        # Save data
        data_path = self.temp_dir / f"econometric_data_{int(time.time())}.csv"
        pd.DataFrame({'series': data}).to_csv(data_path, index=False)
        
        # Create R script
        r_script = f'''
library(forecast)
library(urca)
library(tseries)
library(vars)

# Load data
data <- read.csv("{data_path.as_posix()}")
series <- ts(data$series)
series <- na.omit(series[is.finite(series)])

cat("Econometric Analysis for", length(series), "observations\\n")

# Unit root tests
adf_test <- adf.test(series, alternative = "stationary")
pp_test <- pp.test(series, alternative = "stationary")
kpss_test <- kpss.test(series, null = "Trend")

cat("\\n=== UNIT ROOT TESTS ===\\n")
cat("ADF Test p-value:", adf_test$p.value, "\\n")
cat("PP Test p-value:", pp_test$p.value, "\\n") 
cat("KPSS Test p-value:", kpss_test$p.value, "\\n")

# Determine stationarity
is_stationary <- (adf_test$p.value < 0.05) && (pp_test$p.value < 0.05) && (kpss_test$p.value > 0.05)
cat("Series is stationary:", is_stationary, "\\n")

# ARIMA modeling
auto_arima <- auto.arima(series, seasonal = FALSE, trace = FALSE)
cat("\\n=== ARIMA MODEL ===\\n")
print(auto_arima)

# Model diagnostics
aic_value <- AIC(auto_arima)
bic_value <- BIC(auto_arima)
cat("AIC:", aic_value, "\\n")
cat("BIC:", bic_value, "\\n")

# Forecast
forecast_result <- forecast(auto_arima, h = 5)
forecast_values <- as.numeric(forecast_result$mean)
forecast_lower <- as.numeric(forecast_result$lower[,2])  # 95% CI
forecast_upper <- as.numeric(forecast_result$upper[,2])  # 95% CI

cat("\\n=== FORECASTS (5 periods) ===\\n")
for(i in 1:5) {{
    cat("Period", i, ":", forecast_values[i], 
        "(", forecast_lower[i], ",", forecast_upper[i], ")\\n")
}}

# JSON output
cat("\\n=== ECONOMETRIC JSON ===\\n")
cat("{{\\n")
cat('"adf_pvalue":', adf_test$p.value, ",\\n")
cat('"pp_pvalue":', pp_test$p.value, ",\\n")
cat('"kpss_pvalue":', kpss_test$p.value, ",\\n")
cat('"is_stationary":', tolower(as.character(is_stationary)), ",\\n")
cat('"arima_order": [', auto_arima$arma[1], ",", auto_arima$arma[2], ",", auto_arima$arma[3], "],\\n")
cat('"aic":', aic_value, ",\\n")
cat('"bic":', bic_value, ",\\n")
cat('"forecast_1":', forecast_values[1], ",\\n")
cat('"forecast_2":', forecast_values[2], ",\\n")
cat('"forecast_3":', forecast_values[3], "\\n")
cat("}}\\n")
'''
        
        script_path = self.temp_dir / f"econometric_analysis_{int(time.time())}.R"
        with open(script_path, 'w') as f:
            f.write(r_script)
        
        try:
            result = subprocess.run(
                [self.r_executable, "--vanilla", "--slave", "-f", str(script_path)],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                output = result.stdout
                print("✅ Econometric analysis completed")
                
                # Parse JSON results
                if "=== ECONOMETRIC JSON ===" in output:
                    json_start = output.find("{", output.find("=== ECONOMETRIC JSON ==="))
                    json_end = output.find("}", json_start) + 1
                    if json_start > 0 and json_end > json_start:
                        try:
                            json_str = output[json_start:json_end]
                            results = json.loads(json_str)
                            return {
                                'success': True,
                                'results': results,
                                'full_output': output
                            }
                        except json.JSONDecodeError:
                            pass
                
                return {
                    'success': True,
                    'results': {'message': 'Econometric analysis completed'},
                    'full_output': output
                }
            else:
                print("❌ Error in econometric analysis")
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            print(f"❌ Exception in econometric analysis: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_comprehensive_demo(self):
        """Create comprehensive demo with synthetic financial data"""
        print("\n" + "="*80)
        print("🚀 R STATISTICAL INTEGRATION COMPREHENSIVE DEMO")
        print("="*80)
        
        # Generate synthetic financial data
        np.random.seed(42)
        n_days = 252  # 1 year of daily data
        
        # Simulate price series with realistic characteristics
        initial_price = 100
        mu = 0.0008  # Daily return mean (about 20% annually)
        sigma = 0.02  # Daily volatility (about 32% annually)
        
        returns = np.random.normal(mu, sigma, n_days)
        prices = [initial_price]
        for r in returns:
            prices.append(prices[-1] * (1 + r))
        
        prices = np.array(prices[1:])  # Remove initial price
        actual_returns = np.diff(np.log(prices))
        
        print(f"📊 Generated {len(prices)} days of synthetic price data")
        print(f"📈 Price range: {prices.min():.2f} - {prices.max():.2f}")
        print(f"📉 Return statistics: Mean={actual_returns.mean():.4f}, Std={actual_returns.std():.4f}")
        
        demo_results = {
            'timestamp': datetime.now().isoformat(),
            'data_points': len(prices),
            'price_range': [float(prices.min()), float(prices.max())],
            'return_stats': {
                'mean': float(actual_returns.mean()),
                'std': float(actual_returns.std())
            }
        }
        
        # Run analyses if R is available
        if self.check_r_installation():
            print("\n📦 Installing R packages...")
            self.install_required_packages()
            
            print("\n🔬 Running GARCH volatility analysis...")
            garch_results = self.run_garch_analysis(prices, "Synthetic Asset")
            demo_results['garch_analysis'] = garch_results
            
            print("\n📈 Running performance analytics...")
            perf_results = self.run_performance_analytics(actual_returns)
            demo_results['performance_analytics'] = perf_results
            
            print("\n🔬 Running econometric analysis...")
            econ_results = self.run_econometric_analysis(prices, "Price Series")
            demo_results['econometric_analysis'] = econ_results
            
        else:
            print("\n⚠️ R not available - showing integration pattern only")
            demo_results['r_status'] = 'not_installed'
            demo_results['installation_guide'] = {
                'url': 'https://cran.r-project.org/',
                'windows_steps': [
                    '1. Download R from https://cran.r-project.org/bin/windows/base/',
                    '2. Run the installer with default settings',
                    '3. Add R/bin to your system PATH',
                    '4. Restart your terminal/IDE',
                    '5. Run this script again'
                ]
            }
        
        return demo_results

def main():
    """Main function to demonstrate R integration"""
    print("🔬 LAUNCHING R STATISTICAL INTEGRATION")
    print("="*60)
    
    # Initialize R integrator
    r_integrator = RStatisticalIntegrator()
    
    # Run comprehensive demo
    results = r_integrator.create_comprehensive_demo()
    
    print("\n" + "="*80)
    print("📊 R INTEGRATION DEMO RESULTS SUMMARY")
    print("="*80)
    
    print(f"🕐 Analysis completed at: {results['timestamp']}")
    print(f"📈 Data points analyzed: {results['data_points']}")
    print(f"💰 Price range: ${results['price_range'][0]:.2f} - ${results['price_range'][1]:.2f}")
    
    if 'garch_analysis' in results and results['garch_analysis']['success']:
        garch = results['garch_analysis']['summary']
        print(f"📊 GARCH Volatility: {garch.get('current_volatility', 'N/A'):.4f}")
        print(f"📈 Annualized Vol: {garch.get('annualized_volatility', 'N/A'):.2%}")
    
    if 'performance_analytics' in results and results['performance_analytics']['success']:
        perf = results['performance_analytics']['metrics']
        print(f"⚡ Sharpe Ratio: {perf.get('sharpe_ratio', 'N/A'):.3f}")
        print(f"📉 Max Drawdown: {perf.get('max_drawdown', 'N/A'):.2%}")
    
    if 'econometric_analysis' in results and results['econometric_analysis']['success']:
        econ = results['econometric_analysis']['results']
        print(f"🔬 Series Stationary: {econ.get('is_stationary', 'N/A')}")
        print(f"📊 ARIMA Order: {econ.get('arima_order', 'N/A')}")
    
    print("\n✅ R Statistical Integration Demo Complete!")
    
    if 'installation_guide' in results:
        print("\n" + "="*60)
        print("📥 R INSTALLATION GUIDE")
        print("="*60)
        print(f"Download R: {results['installation_guide']['url']}")
        print("\nWindows Installation Steps:")
        for step in results['installation_guide']['windows_steps']:
            print(f"  {step}")
    
    print(f"\n🎯 NEXT STEPS:")
    print("1. Install R if not already installed")
    print("2. Run this script again to see full R analytics")
    print("3. Integrate R results with existing MATLAB strategies")
    print("4. Proceed to Phase 2: Enhanced Dashboard Integration")
    
    return results

if __name__ == "__main__":
    main()
