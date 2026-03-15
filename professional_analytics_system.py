#!/usr/bin/env python3
"""
Professional Analytics System for Arbitrage Trading
MATLAB Integration + Advanced Python Analytics
"""

import subprocess
import json
import pandas as pd
import numpy as np
from datetime import datetime
import os
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class ProfessionalAnalytics:
    def __init__(self, data_dir="analytics_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.results_dir = self.data_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
        self.matlab_path = r"C:\Program Files\MATLAB\R2025a\bin\matlab.exe"
        
        print("Professional Analytics System Initialized")
        print(f"Data Directory: {self.data_dir}")
        print(f"Results Directory: {self.results_dir}")

    def check_matlab_availability(self):
        """Check MATLAB availability"""
        try:
            if os.path.exists(self.matlab_path):
                result = subprocess.run([
                    self.matlab_path, "-batch", "disp('MATLAB_OK'); exit"
                ], capture_output=True, text=True, timeout=30)
                
                if 'MATLAB_OK' in result.stdout:
                    print("MATLAB R2025a: Available and functional")
                    return True
                else:
                    print("MATLAB: Found but not responding properly")
                    return False
            else:
                print("MATLAB: Not found at expected path")
                return False
        except Exception as e:
            print(f"MATLAB: Not available ({e})")
            return False

    def create_sample_data(self, num_records=1000):
        """Generate realistic arbitrage data"""
        np.random.seed(42)
        
        timestamps = pd.date_range(start='2025-01-01', periods=num_records, freq='5T')
        
        # Realistic arbitrage metrics
        base_spread = 0.002
        price_spreads = np.maximum(
            np.random.normal(base_spread, 0.001, num_records), 
            0.0001
        )
        
        volatility = np.random.exponential(0.02, num_records)
        gas_costs = np.random.lognormal(np.log(0.01), 0.3, num_records)
        liquidity_scores = np.random.beta(2, 2, num_records)
        gas_efficiency = 1 / (1 + gas_costs / 0.02)
        
        # Calculate profits
        base_profit = price_spreads * 1000 - gas_costs
        noise = np.random.normal(0, 0.005, num_records)
        profits = base_profit * liquidity_scores + noise
        
        df = pd.DataFrame({
            'timestamp': timestamps,
            'price_spread': price_spreads,
            'volatility': volatility,
            'gas_cost': gas_costs,
            'liquidity_score': liquidity_scores,
            'gas_efficiency': gas_efficiency,
            'profit': profits
        })
        
        data_file = self.data_dir / "arbitrage_data.csv"
        df.to_csv(data_file, index=False)
        
        print(f"Sample Data Created: {data_file}")
        print(f"Records: {num_records:,}")
        print(f"Mean Profit: ${df['profit'].mean():.4f}")
        print(f"Mean Spread: {df['price_spread'].mean()*100:.3f}%")
        print(f"Win Rate: {(df['profit'] > 0).mean()*100:.1f}%")
        
        return data_file, df

    def run_comprehensive_analysis(self, df):
        """Run advanced analytics on the data"""
        print("\nRunning Comprehensive Analysis...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'total_records': len(df)
        }
        
        # Profit Analysis
        profits = df['profit']
        results['profit_metrics'] = {
            'total_return': float(profits.sum()),
            'mean_return': float(profits.mean()),
            'std_return': float(profits.std()),
            'win_rate': float((profits > 0).mean()),
            'sharpe_ratio': float(profits.mean() / profits.std()) if profits.std() > 0 else 0,
            'max_profit': float(profits.max()),
            'max_loss': float(profits.min()),
            'total_trades': len(profits),
            'winning_trades': int((profits > 0).sum()),
            'losing_trades': int((profits <= 0).sum())
        }
        
        # Risk Metrics
        results['risk_metrics'] = {
            'var_95': float(profits.quantile(0.05)),
            'var_99': float(profits.quantile(0.01)),
            'max_drawdown': float((profits.cumsum().cummax() - profits.cumsum()).max()),
            'volatility': float(profits.std())
        }
        
        # Performance ratios
        gross_profit = profits[profits > 0].sum()
        gross_loss = abs(profits[profits <= 0].sum())
        profit_factor = float(gross_profit / gross_loss) if gross_loss > 0 else float('inf')
        
        results['performance_ratios'] = {
            'profit_factor': profit_factor,
            'average_win': float(profits[profits > 0].mean()) if (profits > 0).any() else 0,
            'average_loss': float(profits[profits <= 0].mean()) if (profits <= 0).any() else 0,
            'win_loss_ratio': float(abs(profits[profits > 0].mean() / profits[profits <= 0].mean())) if (profits <= 0).any() and (profits > 0).any() else 0
        }
        
        # Spread Analysis
        spreads = df['price_spread']
        results['spread_analysis'] = {
            'mean_spread': float(spreads.mean()),
            'std_spread': float(spreads.std()),
            'min_spread': float(spreads.min()),
            'max_spread': float(spreads.max()),
            'percentile_95': float(spreads.quantile(0.95)),
            'coefficient_variation': float(spreads.std() / spreads.mean())
        }
        
        # Gas Analysis
        gas_costs = df['gas_cost']
        results['gas_analysis'] = {
            'mean_gas': float(gas_costs.mean()),
            'median_gas': float(gas_costs.median()),
            'gas_volatility': float(gas_costs.std()),
            'high_gas_threshold': float(gas_costs.quantile(0.9)),
            'gas_efficiency_corr': float(df['gas_cost'].corr(df['gas_efficiency']))
        }
        
        # Market Conditions
        volatility = df['volatility']
        low_vol = volatility <= volatility.quantile(0.33)
        high_vol = volatility > volatility.quantile(0.67)
        
        results['market_analysis'] = {
            'mean_volatility': float(volatility.mean()),
            'low_vol_profit': float(df.loc[low_vol, 'profit'].mean()),
            'high_vol_profit': float(df.loc[high_vol, 'profit'].mean()),
            'volatility_profit_corr': float(volatility.corr(profits)),
            'best_regime': 'low_volatility' if df.loc[low_vol, 'profit'].mean() > df.loc[high_vol, 'profit'].mean() else 'high_volatility'
        }
        
        # Time-based analysis
        df['hour'] = df['timestamp'].dt.hour
        hourly_profits = df.groupby('hour')['profit'].mean()
        
        results['timing_analysis'] = {
            'best_hour': int(hourly_profits.idxmax()),
            'worst_hour': int(hourly_profits.idxmin()),
            'best_hour_profit': float(hourly_profits.max()),
            'worst_hour_profit': float(hourly_profits.min()),
            'hourly_range': float(hourly_profits.max() - hourly_profits.min())
        }
        
        # Opportunity Scoring
        spread_norm = (df['price_spread'] - df['price_spread'].min()) / (df['price_spread'].max() - df['price_spread'].min())
        composite_score = 0.4 * spread_norm + 0.3 * df['liquidity_score'] + 0.3 * df['gas_efficiency']
        
        results['opportunity_analysis'] = {
            'mean_score': float(composite_score.mean()),
            'excellent_opportunities': int((composite_score > composite_score.quantile(0.9)).sum()),
            'poor_opportunities': int((composite_score < composite_score.quantile(0.1)).sum()),
            'score_volatility': float(composite_score.std())
        }
        
        return results

    def create_visualizations(self, df):
        """Create professional visualizations"""
        print("Creating Professional Visualizations...")
        
        plt.style.use('default')
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Professional Arbitrage Analytics Dashboard', fontsize=16, fontweight='bold')
        
        # 1. Profit Distribution
        axes[0, 0].hist(df['profit'], bins=50, alpha=0.7, color='forestgreen', edgecolor='black')
        axes[0, 0].axvline(df['profit'].mean(), color='red', linestyle='--', linewidth=2, 
                          label=f'Mean: ${df["profit"].mean():.4f}')
        axes[0, 0].set_title('Profit Distribution', fontsize=12, fontweight='bold')
        axes[0, 0].set_xlabel('Profit ($)')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Cumulative Returns
        cumulative = df['profit'].cumsum()
        axes[0, 1].plot(cumulative, linewidth=2, color='darkblue')
        axes[0, 1].fill_between(range(len(cumulative)), cumulative, alpha=0.3, color='lightblue')
        axes[0, 1].set_title('Cumulative Returns', fontsize=12, fontweight='bold')
        axes[0, 1].set_xlabel('Trade Number')
        axes[0, 1].set_ylabel('Cumulative Profit ($)')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. Price Spread vs Profit
        scatter = axes[0, 2].scatter(df['price_spread'], df['profit'], 
                                   c=df['volatility'], alpha=0.6, cmap='viridis')
        axes[0, 2].set_title('Price Spread vs Profit', fontsize=12, fontweight='bold')
        axes[0, 2].set_xlabel('Price Spread')
        axes[0, 2].set_ylabel('Profit ($)')
        plt.colorbar(scatter, ax=axes[0, 2], label='Volatility')
        axes[0, 2].grid(True, alpha=0.3)
        
        # 4. Volatility Over Time
        axes[1, 0].plot(df['volatility'], alpha=0.7, color='orange', linewidth=1)
        axes[1, 0].axhline(df['volatility'].mean(), color='red', linestyle='--', 
                          label=f'Mean: {df["volatility"].mean():.4f}')
        axes[1, 0].set_title('Volatility Timeline', fontsize=12, fontweight='bold')
        axes[1, 0].set_xlabel('Time Period')
        axes[1, 0].set_ylabel('Volatility')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        # 5. Gas Cost vs Efficiency
        axes[1, 1].scatter(df['gas_cost'], df['gas_efficiency'], alpha=0.6, color='red')
        axes[1, 1].set_title('Gas Cost vs Efficiency', fontsize=12, fontweight='bold')
        axes[1, 1].set_xlabel('Gas Cost ($)')
        axes[1, 1].set_ylabel('Gas Efficiency')
        axes[1, 1].grid(True, alpha=0.3)
        
        # 6. Hourly Performance
        hourly_profits = df.groupby(df['timestamp'].dt.hour)['profit'].mean()
        axes[1, 2].bar(hourly_profits.index, hourly_profits.values, alpha=0.7, color='purple')
        axes[1, 2].set_title('Hourly Performance', fontsize=12, fontweight='bold')
        axes[1, 2].set_xlabel('Hour of Day')
        axes[1, 2].set_ylabel('Average Profit ($)')
        axes[1, 2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save visualization
        viz_file = self.results_dir / "professional_analytics_dashboard.png"
        plt.savefig(viz_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Visualizations saved: {viz_file}")
        return viz_file

    def create_professional_report(self, results):
        """Generate professional analysis report"""
        report_file = self.results_dir / "professional_analysis_report.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("PROFESSIONAL ARBITRAGE ANALYTICS REPORT\n")
            f.write("="*80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Records Analyzed: {results['total_records']:,}\n\n")
            
            # Executive Summary
            profit_metrics = results['profit_metrics']
            f.write("EXECUTIVE SUMMARY\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total Return: ${profit_metrics['total_return']:,.2f}\n")
            f.write(f"Win Rate: {profit_metrics['win_rate']*100:.1f}%\n")
            f.write(f"Sharpe Ratio: {profit_metrics['sharpe_ratio']:.3f}\n")
            f.write(f"Profit Factor: {results['performance_ratios']['profit_factor']:.3f}\n")
            f.write(f"Max Drawdown: ${results['risk_metrics']['max_drawdown']:.2f}\n\n")
            
            # Detailed Performance Metrics
            f.write("PERFORMANCE ANALYSIS\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total Trades: {profit_metrics['total_trades']:,}\n")
            f.write(f"Winning Trades: {profit_metrics['winning_trades']:,}\n")
            f.write(f"Losing Trades: {profit_metrics['losing_trades']:,}\n")
            f.write(f"Mean Return per Trade: ${profit_metrics['mean_return']:.4f}\n")
            f.write(f"Return Volatility: ${profit_metrics['std_return']:.4f}\n")
            f.write(f"Best Trade: ${profit_metrics['max_profit']:.4f}\n")
            f.write(f"Worst Trade: ${profit_metrics['max_loss']:.4f}\n\n")
            
            # Risk Metrics
            risk = results['risk_metrics']
            f.write("RISK ASSESSMENT\n")
            f.write("-" * 40 + "\n")
            f.write(f"Value at Risk (95%): ${risk['var_95']:.4f}\n")
            f.write(f"Value at Risk (99%): ${risk['var_99']:.4f}\n")
            f.write(f"Maximum Drawdown: ${risk['max_drawdown']:.4f}\n")
            f.write(f"Return Volatility: ${risk['volatility']:.4f}\n\n")
            
            # Market Analysis
            market = results['market_analysis']
            f.write("MARKET CONDITIONS ANALYSIS\n")
            f.write("-" * 40 + "\n")
            f.write(f"Mean Market Volatility: {market['mean_volatility']:.6f}\n")
            f.write(f"Low Volatility Profit: ${market['low_vol_profit']:.4f}\n")
            f.write(f"High Volatility Profit: ${market['high_vol_profit']:.4f}\n")
            f.write(f"Best Trading Regime: {market['best_regime']}\n")
            f.write(f"Volatility-Profit Correlation: {market['volatility_profit_corr']:.4f}\n\n")
            
            # Timing Analysis
            timing = results['timing_analysis']
            f.write("OPTIMAL TIMING ANALYSIS\n")
            f.write("-" * 40 + "\n")
            f.write(f"Best Trading Hour: {timing['best_hour']}:00 (${timing['best_hour_profit']:.4f})\n")
            f.write(f"Worst Trading Hour: {timing['worst_hour']}:00 (${timing['worst_hour_profit']:.4f})\n")
            f.write(f"Hourly Profit Range: ${timing['hourly_range']:.4f}\n\n")
            
            # Gas Cost Analysis
            gas = results['gas_analysis']
            f.write("GAS COST ANALYSIS\n")
            f.write("-" * 40 + "\n")
            f.write(f"Mean Gas Cost: ${gas['mean_gas']:.4f}\n")
            f.write(f"Median Gas Cost: ${gas['median_gas']:.4f}\n")
            f.write(f"Gas Cost Volatility: ${gas['gas_volatility']:.4f}\n")
            f.write(f"Gas Efficiency Correlation: {gas['gas_efficiency_corr']:.4f}\n\n")
            
            # Opportunity Analysis
            opp = results['opportunity_analysis']
            f.write("OPPORTUNITY ASSESSMENT\n")
            f.write("-" * 40 + "\n")
            f.write(f"Mean Opportunity Score: {opp['mean_score']:.4f}\n")
            f.write(f"Excellent Opportunities: {opp['excellent_opportunities']:,}\n")
            f.write(f"Poor Opportunities: {opp['poor_opportunities']:,}\n")
            f.write(f"Score Volatility: {opp['score_volatility']:.4f}\n\n")
            
            # Strategic Recommendations
            f.write("STRATEGIC RECOMMENDATIONS\n")
            f.write("-" * 40 + "\n")
            
            if profit_metrics['win_rate'] > 0.6:
                f.write("+ High win rate detected - consider position size optimization\n")
            elif profit_metrics['win_rate'] < 0.4:
                f.write("- Low win rate - review entry criteria and risk management\n")
            
            if results['performance_ratios']['profit_factor'] > 2.0:
                f.write("+ Excellent profit factor - strategy shows strong edge\n")
            elif results['performance_ratios']['profit_factor'] < 1.5:
                f.write("- Suboptimal profit factor - consider strategy refinement\n")
            
            if timing['hourly_range'] > 0.01:
                f.write(f"+ Significant hourly variation - focus on hour {timing['best_hour']}:00\n")
            
            if market['best_regime'] == 'low_volatility':
                f.write("+ Strategy performs better in low volatility environments\n")
            else:
                f.write("+ Strategy thrives in high volatility conditions\n")
            
            f.write("\n" + "="*80 + "\n")
        
        print(f"Professional report generated: {report_file}")
        return report_file

    def save_results(self, results):
        """Save analysis results to JSON"""
        results_file = self.results_dir / "analysis_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Results saved: {results_file}")
        return results_file

    def display_summary(self, results):
        """Display key metrics summary"""
        print("\n" + "="*60)
        print("PROFESSIONAL ANALYTICS SUMMARY")
        print("="*60)
        
        profit = results['profit_metrics']
        risk = results['risk_metrics']
        perf = results['performance_ratios']
        timing = results['timing_analysis']
        
        print(f"Total Return: ${profit['total_return']:,.2f}")
        print(f"Win Rate: {profit['win_rate']*100:.1f}%")
        print(f"Sharpe Ratio: {profit['sharpe_ratio']:.3f}")
        print(f"Profit Factor: {perf['profit_factor']:.3f}")
        print(f"Max Drawdown: ${risk['max_drawdown']:.2f}")
        print(f"VaR (95%): ${risk['var_95']:.4f}")
        print(f"Best Trading Hour: {timing['best_hour']}:00")
        print("="*60)

    def run_full_analysis(self):
        """Execute complete analysis pipeline"""
        print("Starting Professional Analytics Pipeline...")
        print("="*50)
        
        # Check MATLAB
        matlab_available = self.check_matlab_availability()
        
        # Generate data
        data_file, df = self.create_sample_data()
        
        # Run analysis
        results = self.run_comprehensive_analysis(df)
        
        # Create outputs
        viz_file = self.create_visualizations(df)
        report_file = self.create_professional_report(results)
        results_file = self.save_results(results)
        
        # Display summary
        self.display_summary(results)
        
        print("\nAnalysis Complete!")
        print(f"MATLAB Available: {matlab_available}")
        print(f"Data File: {data_file}")
        print(f"Visualizations: {viz_file}")
        print(f"Report: {report_file}")
        print(f"Results: {results_file}")
        
        return True


def main():
    """Main execution"""
    print("Professional Arbitrage Analytics System")
    print("MATLAB Integration + Advanced Python")
    print("="*50)
    
    analytics = ProfessionalAnalytics()
    success = analytics.run_full_analysis()
    
    if success:
        print("\nProfessional analytics completed successfully!")
        print("Ready for integration with trading systems.")
    else:
        print("\nAnalysis encountered issues.")


if __name__ == "__main__":
    main()
