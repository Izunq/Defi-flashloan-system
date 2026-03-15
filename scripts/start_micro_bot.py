#!/usr/bin/env python3
"""
💰 MICRO ARBITRAGE BOT STARTER - $50 EDITION
===========================================

Simple starter script for micro-capital arbitrage
Perfect for beginners with $50-$500 capital
"""

import asyncio
import os
import sys
from pathlib import Path

def print_welcome():
    """Print welcome message"""
    print("""
💰 MICRO-CAPITAL ARBITRAGE BOT - $50 STARTER EDITION
===================================================

Welcome to realistic arbitrage trading!

WHAT THIS BOT DOES:
🎯 Finds small arbitrage opportunities on cheap chains
⚡ Executes trades with minimal gas costs
📈 Compounds profits to grow your capital
🛡️ Protects your capital with smart risk management

REALISTIC EXPECTATIONS:
💵 Starting Capital: $50
🎯 Daily Target: $2-10 (4%-20% returns)
📊 Monthly Goal: 50-200% growth
🚀 Long-term: Grow to $500+ in 3-6 months

IMPORTANT NOTES:
⚠️ This is REAL trading with REAL money
⚠️ You can lose money - start small and learn
⚠️ Results depend on market conditions
⚠️ Gas costs will eat into small profits

Ready to start? Let's grow that $50! 🚀
    """)

def check_requirements():
    """Check if requirements are met"""
    print("🔍 Checking requirements...")
    
    required_files = [
        'MICRO_CAPITAL_ARBITRAGE_V1.py',
        'micro_config.yaml'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files found")
    return True

def get_user_settings():
    """Get user settings"""
    print("\n📋 SETUP CONFIGURATION")
    print("-" * 30)
    
    # Get starting capital
    while True:
        try:
            capital_input = input("💰 Enter your starting capital ($10-$1000): $").strip()
            if not capital_input:
                capital = 50.0
                print("Using default: $50")
                break
            
            capital = float(capital_input)
            if capital < 10:
                print("⚠️ Warning: Capital below $10 may not be viable due to gas costs")
                confirm = input("Continue anyway? (y/n): ").lower()
                if confirm != 'y':
                    continue
            elif capital > 1000:
                print("💡 Tip: For capital above $1000, consider the institutional version!")
            
            break
        except ValueError:
            print("❌ Please enter a valid number")
    
    # Get risk tolerance
    print("\n🎯 Risk Tolerance:")
    print("1. Conservative (5-10% daily target, lower risk)")
    print("2. Moderate (10-15% daily target, balanced)")
    print("3. Aggressive (15-25% daily target, higher risk)")
    
    while True:
        risk_choice = input("Choose risk level (1-3): ").strip()
        if risk_choice in ['1', '2', '3']:
            break
        print("❌ Please choose 1, 2, or 3")
    
    risk_levels = {
        '1': {'name': 'Conservative', 'daily_target': 7.5, 'max_position': 70},
        '2': {'name': 'Moderate', 'daily_target': 12.5, 'max_position': 80},
        '3': {'name': 'Aggressive', 'daily_target': 20.0, 'max_position': 90}
    }
    
    risk_profile = risk_levels[risk_choice]
    
    # Get preferred chains
    print("\n🌐 Preferred Chains (cheaper gas):")
    print("1. Polygon (cheapest, ~$0.01 gas)")
    print("2. BSC (cheap, ~$0.20 gas)")
    print("3. Arbitrum (moderate, ~$0.50 gas)")
    print("4. All chains")
    
    chain_choice = input("Choose preferred chains (1-4): ").strip()
    
    chain_options = {
        '1': ['polygon'],
        '2': ['bsc'],
        '3': ['arbitrum'],
        '4': ['polygon', 'bsc', 'arbitrum']
    }
    
    preferred_chains = chain_options.get(chain_choice, ['polygon', 'bsc'])
    
    return {
        'capital': capital,
        'risk_profile': risk_profile,
        'preferred_chains': preferred_chains
    }

def show_projections(settings):
    """Show realistic projections"""
    capital = settings['capital']
    daily_target = settings['risk_profile']['daily_target']
    
    print(f"\n📊 REALISTIC PROJECTIONS")
    print("-" * 40)
    print(f"Starting Capital: ${capital:.2f}")
    print(f"Daily Target: {daily_target:.1f}% (${capital * daily_target / 100:.2f})")
    
    # Calculate compound growth projections
    current = capital
    print(f"\nGROWTH TIMELINE:")
    
    for days in [7, 14, 30, 60, 90]:
        # Conservative compound growth
        projected = capital * ((1 + daily_target/100) ** days)
        growth_percent = ((projected - capital) / capital) * 100
        
        print(f"Day {days:2d}: ${projected:7.2f} ({growth_percent:6.1f}% growth)")
        
        if projected >= 100 and capital < 100:
            print(f"        🎯 First $100 milestone!")
        if projected >= 500 and capital < 500:
            print(f"        🚀 $500 milestone - consider scaling up!")
        if projected >= 1000 and capital < 1000:
            print(f"        💎 $1000 milestone - time for advanced strategies!")
    
    print(f"\n⚠️ Note: These are projections assuming {daily_target:.1f}% daily returns.")
    print("   Actual results will vary based on market conditions!")

async def start_bot(settings):
    """Start the arbitrage bot"""
    print(f"\n🚀 STARTING MICRO ARBITRAGE BOT")
    print("-" * 40)
    print(f"Capital: ${settings['capital']:.2f}")
    print(f"Risk Level: {settings['risk_profile']['name']}")
    print(f"Daily Target: {settings['risk_profile']['daily_target']:.1f}%")
    print(f"Chains: {', '.join(settings['preferred_chains'])}")
    
    print(f"\nPress Ctrl+C to stop the bot at any time")
    print(f"Bot will show progress every few minutes")
    
    input("\nPress Enter to start trading... ")
    
    try:
        # Import and run the micro arbitrage bot
        from MICRO_CAPITAL_ARBITRAGE_V1 import MicroArbitrageBot
        
        bot = MicroArbitrageBot(settings['capital'])
        
        # Update bot config with user settings
        bot.config.daily_target_percent = settings['risk_profile']['daily_target']
        bot.config.max_position_percent = settings['risk_profile']['max_position']
        bot.config.preferred_chains = settings['preferred_chains']
        
        await bot.run_micro_arbitrage()
        
    except KeyboardInterrupt:
        print("\n⚠️ Bot stopped by user")
    except ImportError as e:
        print(f"❌ Error importing bot: {e}")
        print("Make sure MICRO_CAPITAL_ARBITRAGE_V1.py is in the same directory")
    except Exception as e:
        print(f"💥 Bot error: {e}")

def main():
    """Main function"""
    print_welcome()
    
    if not check_requirements():
        print("\n❌ Setup incomplete. Please ensure all files are present.")
        return
    
    settings = get_user_settings()
    show_projections(settings)
    
    # Confirm before starting
    print(f"\n🤔 Ready to start trading with these settings?")
    confirm = input("Type 'yes' to continue: ").lower()
    
    if confirm != 'yes':
        print("👋 Setup cancelled. Run again when ready!")
        return
    
    # Start the bot
    asyncio.run(start_bot(settings))

if __name__ == "__main__":
    main()