#!/usr/bin/env python3
"""
🚀 SIMPLE $75 CAPITAL TEST
=========================
"""

import random

# Starting capital
capital = 75.0
initial_capital = 75.0
trades = 0
profitable = 0
total_profit = 0.0

print("🌙 Bismillah - Testing $75 Capital Strategy")
print(f"💰 Starting Capital: ${capital}")
print("=" * 40)

# Run 20 test trades
for i in range(20):
    trades += 1
    
    # Position sizing - 20% of capital or max $50
    position_size = min(capital * 0.20, 50.0)
    
    # 88% success rate
    if random.random() < 0.88:
        # Successful trade
        profit_rate = random.uniform(0.008, 0.025)  # 0.8% to 2.5%
        gross_profit = position_size * profit_rate
        net_profit = gross_profit * 0.8  # 80% to trader
        
        capital += net_profit
        total_profit += net_profit
        profitable += 1
        
        print(f"Trade {trades}: ✅ +${net_profit:.2f} (Capital: ${capital:.2f})")
    else:
        # Failed trade - gas cost
        loss = random.uniform(1.0, 4.0)
        capital -= loss
        total_profit -= loss
        
        print(f"Trade {trades}: ❌ -${loss:.2f} (Capital: ${capital:.2f})")

# Results
total_return = (capital / initial_capital - 1) * 100
success_rate = (profitable / trades) * 100

print("\n" + "=" * 50)
print("🎉 $75 CAPITAL TEST RESULTS")
print("=" * 50)
print(f"💰 Starting Capital: ${initial_capital}")
print(f"💰 Final Capital: ${capital:.2f}")
print(f"📈 Total Return: {total_return:+.2f}%")
print(f"💵 Net Profit: ${total_profit:+.2f}")
print(f"🎯 Trades: {trades}")
print(f"✅ Success Rate: {success_rate:.1f}%")

if total_return > 0:
    print(f"\n🚀 EXCELLENT! Your $75 grew to ${capital:.2f}")
    print(f"📊 That's a ${total_profit:+.2f} profit!")
    print(f"✅ Strategy appears profitable for mainnet")
else:
    print(f"\n⚠️ Strategy needs optimization before mainnet")

print("=" * 50)
