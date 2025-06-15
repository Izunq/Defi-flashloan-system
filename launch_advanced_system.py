#!/usr/bin/env python3
"""
🧠 ADVANCED ARBITRAGE SYSTEM LAUNCHER
====================================

Integrates all existing systems with advanced backtesting and optimization
Uses the entire codebase for maximum profit with minimum risk
"""

import asyncio
import os
import sys
import json
import yaml
from pathlib import Path
from datetime import datetime, timedelta
import logging

def print_system_overview():
    """Print comprehensive system overview"""
    print("""
🧠 ADVANCED ARBITRAGE SYSTEM - COMPLETE INTEGRATION
==================================================

WHAT THIS SYSTEM DOES:
🔬 Analyzes ALL existing code and strategies
📊 Backtests strategies with historical data
🧠 Uses AI/ML to optimize performance
⚡ Finds maximum profit with minimum risk
🎯 Continuously adapts to market conditions
💰 Integrates all your existing systems

INTEGRATED SYSTEMS:
📈 INSTITUTIONAL_GRADE_V35.py - AI/ML features
🚀 python_agent_v34_ultimate.py - Advanced execution
🔥 MAXIMUM_PROFIT_ARBITRAGE_V2.py - Aggressive strategies
💰 MICRO_CAPITAL_ARBITRAGE_V1.py - Risk management
🏗️ All smart contracts and configurations

ADVANCED FEATURES:
🔬 Historical backtesting with real market simulation
📊 Multi-strategy performance analysis
🧠 AI-powered portfolio optimization
⚡ Live strategy adaptation
🎯 Risk-adjusted profit maximization
📈 Continuous learning and improvement

Ready to find the OPTIMAL strategy for your capital? 🚀
    """)

def analyze_existing_codebase():
    """Analyze existing codebase to understand available strategies"""
    print("🔍 ANALYZING EXISTING CODEBASE...")
    print("-" * 40)
    
    # Check for existing files
    files_found = {}
    
    key_files = {
        'INSTITUTIONAL_GRADE_V35.py': 'Institutional AI/ML System',
        'python_agent_v34_ultimate.py': 'Ultimate Arbitrage Agent',
        'MAXIMUM_PROFIT_ARBITRAGE_V2.py': 'Maximum Profit System',
        'MICRO_CAPITAL_ARBITRAGE_V1.py': 'Micro Capital System',
        'ADVANCED_BACKTESTING_OPTIMIZER_V1.py': 'Advanced Backtesting System'
    }
    
    for file, description in key_files.items():
        if Path(file).exists():
            files_found[file] = description
            print(f"✅ {description}")
        else:
            print(f"❌ {description} - Not found")
    
    # Check smart contracts
    contract_dir = Path('contracts')
    if contract_dir.exists():
        contracts = list(contract_dir.glob('*.sol'))
        print(f"✅ Smart Contracts: {len(contracts)} found")
        for contract in contracts[:5]:  # Show first 5
            print(f"   📄 {contract.name}")
    else:
        print("❌ Smart Contracts directory not found")
    
    # Check configurations
    config_files = ['institutional_config.yaml', 'max_profit_config.yaml', 'micro_config.yaml']
    configs_found = [f for f in config_files if Path(f).exists()]
    print(f"✅ Configuration Files: {len(configs_found)} found")
    
    print(f"\n📊 SYSTEM ANALYSIS COMPLETE:")
    print(f"   🎯 Available Systems: {len(files_found)}")
    print(f"   📄 Smart Contracts: {len(contracts) if 'contracts' in locals() else 0}")
    print(f"   ⚙️ Configuration Files: {len(configs_found)}")
    
    return files_found, configs_found

def get_user_preferences():
    """Get user preferences for optimization"""
    print("\n🎯 OPTIMIZATION PREFERENCES")
    print("-" * 30)
    
    # Get starting capital
    while True:
        try:
            capital_input = input("💰 Enter your starting capital ($10-$10000): $").strip()
            if not capital_input:
                capital = 50.0
                print("Using default: $50")
                break
            
            capital = float(capital_input)
            if capital < 10:
                print("⚠️ Warning: Capital below $10 may limit strategy options")
            elif capital > 10000:
                print("💡 High capital detected - institutional strategies available!")
            
            break
        except ValueError:
            print("❌ Please enter a valid number")
    
    # Get risk tolerance
    print("\n🎯 Risk Tolerance:")
    print("1. Conservative (Focus on capital preservation)")
    print("2. Moderate (Balanced risk/reward)")
    print("3. Aggressive (Maximum profit potential)")
    
    while True:
        risk_choice = input("Choose risk tolerance (1-3): ").strip()
        if risk_choice in ['1', '2', '3']:
            break
        print("❌ Please choose 1, 2, or 3")
    
    risk_profiles = {
        '1': {
            'name': 'Conservative',
            'max_drawdown': 0.10,
            'min_sharpe': 2.0,
            'target_return': 0.15,
            'strategies': ['simple_arbitrage', 'yield_arbitrage']
        },
        '2': {
            'name': 'Moderate',
            'max_drawdown': 0.20,
            'min_sharpe': 1.5,
            'target_return': 0.30,
            'strategies': ['simple_arbitrage', 'triangular_arbitrage', 'flash_arbitrage', 'yield_arbitrage']
        },
        '3': {
            'name': 'Aggressive',
            'max_drawdown': 0.35,
            'min_sharpe': 1.0,
            'target_return': 0.50,
            'strategies': ['simple_arbitrage', 'triangular_arbitrage', 'flash_arbitrage', 
                          'cross_chain_arbitrage', 'mev_sandwich', 'liquidation_arbitrage', 'yield_arbitrage']
        }
    }
    
    risk_profile = risk_profiles[risk_choice]
    
    # Get optimization objective
    print("\n📊 Optimization Objective:")
    print("1. Maximum Total Return")
    print("2. Best Risk-Adjusted Return (Sharpe Ratio)")
    print("3. Minimum Risk (Capital Preservation)")
    
    obj_choice = input("Choose objective (1-3): ").strip()
    
    objectives = {
        '1': 'total_return',
        '2': 'sharpe_ratio', 
        '3': 'minimum_risk'
    }
    
    optimization_objective = objectives.get(obj_choice, 'sharpe_ratio')
    
    # Get backtesting period
    print("\n📅 Backtesting Period:")
    print("1. Quick Test (1 week)")
    print("2. Standard Test (1 month)")
    print("3. Comprehensive Test (3 months)")
    print("4. Full Year Test (12 months)")
    
    period_choice = input("Choose backtesting period (1-4): ").strip()
    
    periods = {
        '1': {'days': 7, 'name': 'Quick'},
        '2': {'days': 30, 'name': 'Standard'},
        '3': {'days': 90, 'name': 'Comprehensive'},
        '4': {'days': 365, 'name': 'Full Year'}
    }
    
    backtest_period = periods.get(period_choice, periods['2'])
    
    return {
        'capital': capital,
        'risk_profile': risk_profile,
        'optimization_objective': optimization_objective,
        'backtest_period': backtest_period
    }

def show_optimization_plan(preferences):
    """Show the optimization plan"""
    print(f"\n🎯 OPTIMIZATION PLAN")
    print("-" * 25)
    print(f"💰 Starting Capital: ${preferences['capital']:.2f}")
    print(f"🎯 Risk Profile: {preferences['risk_profile']['name']}")
    print(f"📊 Objective: {preferences['optimization_objective'].replace('_', ' ').title()}")
    print(f"📅 Backtest Period: {preferences['backtest_period']['name']} ({preferences['backtest_period']['days']} days)")
    print(f"🔧 Strategies to Test: {len(preferences['risk_profile']['strategies'])}")
    
    for strategy in preferences['risk_profile']['strategies']:
        print(f"   • {strategy.replace('_', ' ').title()}")
    
    print(f"\n📈 Expected Outcomes:")
    print(f"   🎯 Target Return: {preferences['risk_profile']['target_return']:.0%}")
    print(f"   🛡️ Max Drawdown: {preferences['risk_profile']['max_drawdown']:.0%}")
    print(f"   📊 Min Sharpe Ratio: {preferences['risk_profile']['min_sharpe']:.1f}")
    
    # Calculate potential profits
    target_return = preferences['risk_profile']['target_return']
    capital = preferences['capital']
    
    daily_return = target_return / 365
    
    print(f"\n💰 PROFIT PROJECTIONS:")
    for days, label in [(7, "Week 1"), (30, "Month 1"), (90, "Month 3"), (365, "Year 1")]:
        if days <= preferences['backtest_period']['days']:
            projected_capital = capital * ((1 + daily_return) ** days)
            profit = projected_capital - capital
            print(f"   {label}: ${projected_capital:.2f} (+${profit:.2f})")

async def run_advanced_optimization(preferences):
    """Run the advanced optimization system"""
    print(f"\n🚀 STARTING ADVANCED OPTIMIZATION")
    print("-" * 40)
    
    try:
        # Import the advanced backtesting system
        from ADVANCED_BACKTESTING_OPTIMIZER_V1 import AdvancedBacktestingSystem, BacktestConfig
        
        # Create configuration
        end_date = datetime.now()
        start_date = end_date - timedelta(days=preferences['backtest_period']['days'])
        
        config = BacktestConfig(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            initial_capital=preferences['capital'],
            strategies_to_test=preferences['risk_profile']['strategies'],
            max_drawdown_threshold=preferences['risk_profile']['max_drawdown'],
            min_sharpe_ratio=preferences['risk_profile']['min_sharpe'],
            optimization_metric=preferences['optimization_objective']
        )
        
        print(f"📊 Configuration created:")
        print(f"   📅 Period: {config.start_date} to {config.end_date}")
        print(f"   🎯 Strategies: {len(config.strategies_to_test)}")
        print(f"   💰 Capital: ${config.initial_capital:.2f}")
        
        # Initialize system
        print(f"\n🔧 Initializing advanced backtesting system...")
        backtesting_system = AdvancedBacktestingSystem(config)
        
        # Run comprehensive backtest
        print(f"🔬 Running comprehensive backtest...")
        results = await backtesting_system.run_comprehensive_backtest()
        
        # Display results
        print("\n" + "="*60)
        print(results['report'])
        print("="*60)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"optimization_results_{timestamp}.json"
        
        # Prepare results for JSON serialization
        json_results = {
            'timestamp': timestamp,
            'config': {
                'capital': config.initial_capital,
                'strategies': config.strategies_to_test,
                'optimization_metric': config.optimization_metric
            },
            'optimal_allocation': results['optimal_allocation'],
            'portfolio_performance': results['portfolio_performance']
        }
        
        with open(results_file, 'w') as f:
            json.dump(json_results, f, indent=2)
        
        print(f"💾 Results saved to: {results_file}")
        
        # Ask about live trading
        if results['optimal_allocation']:
            print(f"\n🎯 OPTIMAL STRATEGY FOUND!")
            print(f"Best allocation: {results['optimal_allocation']}")
            
            start_live = input("\n🚀 Start live trading with optimal allocation? (y/n): ").lower()
            if start_live == 'y':
                await start_live_trading(results['optimal_allocation'], preferences)
        else:
            print(f"\n⚠️ No optimal allocation found with current parameters")
            print(f"💡 Consider:")
            print(f"   - Lowering risk requirements")
            print(f"   - Increasing capital")
            print(f"   - Adding more strategies")
            
    except ImportError as e:
        print(f"❌ Error importing backtesting system: {e}")
        print(f"💡 Make sure ADVANCED_BACKTESTING_OPTIMIZER_V1.py is available")
    except Exception as e:
        print(f"💥 Optimization error: {e}")

async def start_live_trading(optimal_allocation, preferences):
    """Start live trading with optimal allocation"""
    print(f"\n🚀 STARTING LIVE TRADING")
    print("-" * 25)
    
    capital = preferences['capital']
    
    print(f"💰 Capital: ${capital:.2f}")
    print(f"🎯 Strategy Allocation:")
    
    for strategy, weight in optimal_allocation.items():
        allocated_capital = capital * weight
        print(f"   {strategy}: {weight:.1%} (${allocated_capital:.2f})")
    
    print(f"\n⚠️ LIVE TRADING RISKS:")
    print(f"   💸 You can lose real money")
    print(f"   ⛽ Gas costs will reduce profits")
    print(f"   📉 Market conditions change constantly")
    print(f"   🤖 Bot performance may vary from backtest")
    
    final_confirm = input(f"\nType 'START LIVE TRADING' to begin: ").strip()
    if final_confirm != "START LIVE TRADING":
        print("👋 Live trading cancelled. Results saved for future reference.")
        return
    
    # Determine which system to use based on capital and allocation
    primary_strategy = max(optimal_allocation, key=optimal_allocation.get)
    
    try:
        if capital >= 1000 and 'flash_arbitrage' in optimal_allocation:
            print("🏛️ Starting Institutional Grade System...")
            from INSTITUTIONAL_GRADE_V35 import InstitutionalArbitrageSystem
            system = InstitutionalArbitrageSystem()
            await system.run_institutional_arbitrage()
            
        elif 'mev_sandwich' in optimal_allocation or capital >= 500:
            print("🔥 Starting Maximum Profit System...")
            from MAXIMUM_PROFIT_ARBITRAGE_V2 import MaximumProfitBot
            system = MaximumProfitBot(capital)
            await system.run_maximum_profit_extraction()
            
        else:
            print("💰 Starting Micro Capital System...")
            from MICRO_CAPITAL_ARBITRAGE_V1 import MicroArbitrageBot
            system = MicroArbitrageBot(capital)
            await system.run_micro_arbitrage()
            
    except ImportError as e:
        print(f"❌ Error importing trading system: {e}")
    except KeyboardInterrupt:
        print(f"\n⚠️ Live trading stopped by user")
    except Exception as e:
        print(f"💥 Live trading error: {e}")

def main():
    """Main function"""
    print_system_overview()
    
    # Analyze existing codebase
    files_found, configs_found = analyze_existing_codebase()
    
    if len(files_found) < 2:
        print(f"\n❌ Insufficient systems found!")
        print(f"💡 Make sure you have the required Python files in the directory")
        return
    
    # Get user preferences
    preferences = get_user_preferences()
    
    # Show optimization plan
    show_optimization_plan(preferences)
    
    # Confirm before starting
    print(f"\n🤔 Ready to start advanced optimization?")
    confirm = input("Type 'yes' to continue: ").lower()
    
    if confirm != 'yes':
        print("👋 Optimization cancelled. Run again when ready!")
        return
    
    # Run optimization
    asyncio.run(run_advanced_optimization(preferences))

if __name__ == "__main__":
    main()