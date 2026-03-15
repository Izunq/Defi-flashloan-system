#!/usr/bin/env python3
"""
🔥 MAXIMUM PROFIT LAUNCHER - AGGRESSIVE EDITION
==============================================

Launch the most aggressive profit extraction system
Turn $50 into $500+ with maximum aggression!
"""

import asyncio
import os
import sys
from pathlib import Path

def print_aggressive_welcome():
    """Print aggressive welcome message"""
    print("""
🔥 MAXIMUM PROFIT ARBITRAGE SYSTEM - AGGRESSIVE EDITION
======================================================

TURN $50 INTO $500+ WITH MAXIMUM AGGRESSION!

WHAT THIS SYSTEM DOES:
🚀 Executes 7 different arbitrage strategies simultaneously
⚡ Uses 2.5x leverage simulation for maximum capital efficiency
💰 Hunts MEV opportunities and sandwich attacks
🌐 Operates across 6 blockchain networks
🔍 Scans every 5 seconds for new opportunities
💎 Compounds profits aggressively for exponential growth

AGGRESSIVE TARGETS:
💵 Starting Capital: $50
🎯 Daily Target: $15-25 (30%-50% returns)
📊 Weekly Goal: 200-500% growth
🚀 Monthly Target: 1000%+ returns
💎 Ultimate Goal: $50 → $5000+ in 2-3 months

⚠️ EXTREME RISK WARNING ⚠️
This system uses HIGH-RISK, HIGH-REWARD strategies:
- MEV sandwich attacks
- Flash loan arbitrage (up to $100k)
- Cross-chain arbitrage
- 2.5x leverage simulation
- 95% capital utilization per trade
- Multiple concurrent trades

YOU CAN LOSE ALL YOUR MONEY!
Only use money you can afford to lose completely!

Ready to get aggressive? 🔥💰🚀
    """)

def get_aggressive_settings():
    """Get user settings for maximum aggression"""
    print("\n🔥 AGGRESSIVE CONFIGURATION")
    print("-" * 40)
    
    # Get starting capital
    while True:
        try:
            capital_input = input("💰 Enter your starting capital ($25-$1000): $").strip()
            if not capital_input:
                capital = 50.0
                print("Using default: $50")
                break
            
            capital = float(capital_input)
            if capital < 25:
                print("⚠️ Warning: Capital below $25 may not be viable for aggressive strategies")
                confirm = input("Continue anyway? (y/n): ").lower()
                if confirm != 'y':
                    continue
            elif capital > 1000:
                print("💡 Tip: For capital above $1000, consider the institutional version!")
            
            break
        except ValueError:
            print("❌ Please enter a valid number")
    
    # Get aggression level
    print("\n🔥 Aggression Level:")
    print("1. Aggressive (25% daily target, 2x leverage)")
    print("2. Very Aggressive (35% daily target, 2.5x leverage)")
    print("3. MAXIMUM AGGRESSION (50% daily target, 3x leverage)")
    
    while True:
        aggression_choice = input("Choose aggression level (1-3): ").strip()
        if aggression_choice in ['1', '2', '3']:
            break
        print("❌ Please choose 1, 2, or 3")
    
    aggression_levels = {
        '1': {
            'name': 'Aggressive',
            'daily_target': 25.0,
            'leverage': 2.0,
            'position_size': 90.0,
            'concurrent_trades': 3
        },
        '2': {
            'name': 'Very Aggressive',
            'daily_target': 35.0,
            'leverage': 2.5,
            'position_size': 95.0,
            'concurrent_trades': 5
        },
        '3': {
            'name': 'MAXIMUM AGGRESSION',
            'daily_target': 50.0,
            'leverage': 3.0,
            'position_size': 98.0,
            'concurrent_trades': 7
        }
    }
    
    aggression_profile = aggression_levels[aggression_choice]
    
    # Get strategy preferences
    print("\n🚀 Strategy Selection:")
    print("1. Safe Strategies (arbitrage + yield)")
    print("2. Balanced Strategies (arbitrage + MEV + flash loans)")
    print("3. ALL STRATEGIES (including sandwich attacks)")
    
    strategy_choice = input("Choose strategy set (1-3): ").strip()
    
    strategy_options = {
        '1': ['simple_arbitrage', 'triangular_arbitrage', 'yield_arbitrage'],
        '2': ['simple_arbitrage', 'triangular_arbitrage', 'flash_arbitrage', 'cross_chain_arbitrage', 'liquidation_arbitrage'],
        '3': ['simple_arbitrage', 'triangular_arbitrage', 'flash_arbitrage', 'cross_chain_arbitrage', 'mev_sandwich', 'liquidation_arbitrage', 'yield_arbitrage']
    }
    
    enabled_strategies = strategy_options.get(strategy_choice, strategy_options['2'])
    
    return {
        'capital': capital,
        'aggression_profile': aggression_profile,
        'enabled_strategies': enabled_strategies
    }

def show_aggressive_projections(settings):
    """Show aggressive growth projections"""
    capital = settings['capital']
    daily_target = settings['aggression_profile']['daily_target']
    
    print(f"\n🔥 AGGRESSIVE GROWTH PROJECTIONS")
    print("-" * 50)
    print(f"Starting Capital: ${capital:.2f}")
    print(f"Daily Target: {daily_target:.1f}% (${capital * daily_target / 100:.2f})")
    
    # Calculate aggressive compound growth projections
    current = capital
    print(f"\nAGGRESSIVE GROWTH TIMELINE:")
    
    milestones = [
        (1, "Day 1"),
        (3, "Day 3"),
        (7, "Week 1"),
        (14, "Week 2"),
        (30, "Month 1"),
        (60, "Month 2"),
        (90, "Month 3")
    ]
    
    for days, label in milestones:
        # Aggressive compound growth
        projected = capital * ((1 + daily_target/100) ** days)
        growth_multiple = projected / capital
        
        print(f"{label:8}: ${projected:8.0f} ({growth_multiple:5.1f}x growth)")
        
        if projected >= 100 and capital < 100:
            print(f"         🎯 First $100 milestone!")
        if projected >= 500 and capital < 500:
            print(f"         🚀 $500 milestone - 10x growth!")
        if projected >= 1000 and capital < 1000:
            print(f"         💎 $1000 milestone - 20x growth!")
        if projected >= 5000 and capital < 5000:
            print(f"         👑 $5000 milestone - 100x growth!")
        if projected >= 10000:
            print(f"         🏆 $10K+ - You've mastered the system!")
    
    print(f"\n⚠️ DISCLAIMER: These are AGGRESSIVE projections assuming {daily_target:.1f}% daily returns.")
    print("   Actual results will vary. You can lose all your money!")
    print("   Past performance does not guarantee future results!")

def show_risk_warnings():
    """Show comprehensive risk warnings"""
    print(f"\n⚠️ COMPREHENSIVE RISK WARNING")
    print("=" * 50)
    print("BEFORE YOU START, UNDERSTAND THESE RISKS:")
    print()
    print("💸 FINANCIAL RISKS:")
    print("   - You can lose ALL your money")
    print("   - Crypto markets are extremely volatile")
    print("   - Gas costs can eat into profits")
    print("   - Smart contract risks")
    print("   - Bridge risks for cross-chain trades")
    print()
    print("🔥 STRATEGY RISKS:")
    print("   - MEV sandwich attacks can fail")
    print("   - Flash loans can be liquidated")
    print("   - High leverage amplifies losses")
    print("   - Multiple concurrent trades = multiple risks")
    print("   - Front-running by other bots")
    print()
    print("⚡ TECHNICAL RISKS:")
    print("   - Network congestion")
    print("   - Failed transactions")
    print("   - Slippage on trades")
    print("   - Smart contract bugs")
    print("   - API failures")
    print()
    print("🎯 REALISTIC EXPECTATIONS:")
    print("   - Most days you might make little or no profit")
    print("   - Some days you will lose money")
    print("   - Consistent 30%+ daily returns are NOT guaranteed")
    print("   - Market conditions change constantly")
    print("   - Competition from other bots is fierce")
    print()
    print("💡 RESPONSIBLE TRADING:")
    print("   - Only risk money you can afford to lose completely")
    print("   - Start with small amounts to learn")
    print("   - Don't invest borrowed money")
    print("   - Have realistic expectations")
    print("   - Stop if you're losing consistently")

async def start_aggressive_bot(settings):
    """Start the aggressive arbitrage bot"""
    print(f"\n🔥 STARTING MAXIMUM PROFIT EXTRACTION")
    print("-" * 50)
    print(f"Capital: ${settings['capital']:.2f}")
    print(f"Aggression: {settings['aggression_profile']['name']}")
    print(f"Daily Target: {settings['aggression_profile']['daily_target']:.1f}%")
    print(f"Leverage: {settings['aggression_profile']['leverage']:.1f}x")
    print(f"Strategies: {len(settings['enabled_strategies'])}")
    print(f"Concurrent Trades: {settings['aggression_profile']['concurrent_trades']}")
    
    print(f"\n🚨 FINAL WARNING:")
    print(f"You are about to start AGGRESSIVE trading with ${settings['capital']:.2f}")
    print(f"This system will attempt to make {settings['aggression_profile']['daily_target']:.1f}% daily returns")
    print(f"using HIGH-RISK strategies including MEV attacks and flash loans.")
    print(f"\nYou could lose ALL your money!")
    
    final_confirm = input(f"\nType 'START AGGRESSIVE TRADING' to begin: ").strip()
    if final_confirm != "START AGGRESSIVE TRADING":
        print("👋 Smart choice! Consider starting with the safer micro version.")
        return
    
    print(f"\n🚀 LAUNCHING MAXIMUM PROFIT EXTRACTION...")
    print(f"Press Ctrl+C to stop the bot at any time")
    print(f"Bot will show progress and profits in real-time")
    
    input("\nPress Enter to start aggressive trading... ")
    
    try:
        # Import and run the maximum profit bot
        from MAXIMUM_PROFIT_ARBITRAGE_V2 import MaximumProfitBot
        
        bot = MaximumProfitBot(settings['capital'])
        
        # Update bot config with user settings
        bot.config.daily_target_percent = settings['aggression_profile']['daily_target']
        bot.config.max_position_percent = settings['aggression_profile']['position_size']
        bot.config.leverage_simulation = settings['aggression_profile']['leverage']
        bot.config.max_concurrent_trades = settings['aggression_profile']['concurrent_trades']
        
        await bot.run_maximum_profit_extraction()
        
    except KeyboardInterrupt:
        print("\n⚠️ Bot stopped by user")
    except ImportError as e:
        print(f"❌ Error importing bot: {e}")
        print("Make sure MAXIMUM_PROFIT_ARBITRAGE_V2.py is in the same directory")
    except Exception as e:
        print(f"💥 Bot error: {e}")

def main():
    """Main function"""
    print_aggressive_welcome()
    
    # Show risk warnings first
    show_risk_warnings()
    
    # Get user confirmation for risks
    risk_confirm = input(f"\nDo you understand and accept these risks? (yes/no): ").lower()
    if risk_confirm != 'yes':
        print("👋 Wise choice! Consider learning more about arbitrage trading first.")
        return
    
    settings = get_aggressive_settings()
    show_aggressive_projections(settings)
    
    # Final confirmation before starting
    print(f"\n🤔 Ready to start AGGRESSIVE trading with these settings?")
    print(f"Remember: You can lose ALL your ${settings['capital']:.2f}!")
    
    confirm = input("Type 'yes' to continue: ").lower()
    
    if confirm != 'yes':
        print("👋 Setup cancelled. Run again when ready!")
        return
    
    # Start the aggressive bot
    asyncio.run(start_aggressive_bot(settings))

if __name__ == "__main__":
    main()