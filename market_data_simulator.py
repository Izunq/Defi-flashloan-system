"""
Market Data Simulator
-------------------
This script simulates market data events for testing the arbitrage system.
It publishes simulated price data to the 'market-data-events' channel.
"""

import time
import random
import json
from datetime import datetime
from core.event_bus import event_bus

# Token addresses for common assets
TOKENS = {
    "WETH": "${CONTRACT_ADDRESS}",
    "USDC": "${CONTRACT_ADDRESS}",
    "WBTC": "${CONTRACT_ADDRESS}",
    "DAI": "${CONTRACT_ADDRESS}"
}

# Trading pairs to simulate
PAIRS = [
    "WETH/USDC",
    "WBTC/USDC",
    "WETH/DAI",
    "WBTC/WETH"
]

# DEXes to simulate
DEXES = ["Uniswap", "SushiSwap", "Curve", "Balancer"]

def generate_opportunity():
    """
    Generate a simulated arbitrage opportunity.
    
    Returns:
        Dictionary with opportunity data
    """
    # Select a random pair
    pair = random.choice(PAIRS)
    base_token, quote_token = pair.split('/')
    
    # Generate a base price
    if base_token == "WETH":
        base_price = random.uniform(1800, 2200)
    elif base_token == "WBTC":
        base_price = random.uniform(45000, 55000)
    else:
        base_price = random.uniform(0.9, 1.1)
    
    # Generate price difference (0-2%)
    price_diff_pct = random.uniform(0, 0.02)
    
    # Select two random DEXes
    dex_a, dex_b = random.sample(DEXES, 2)
    
    # Decide which DEX has the lower price
    if random.random() < 0.5:
        dex_a_price = base_price
        dex_b_price = base_price * (1 + price_diff_pct)
    else:
        dex_a_price = base_price * (1 + price_diff_pct)
        dex_b_price = base_price
    
    # Create the opportunity data
    opportunity = {
        "pair": pair,
        "timestamp": time.time(),
        "dex_a": dex_a,
        "dex_b": dex_b,
        "dex_a_price": dex_a_price,
        "dex_b_price": dex_b_price,
        "asset_address": TOKENS[base_token],
        "quote_address": TOKENS[quote_token]
    }
    
    return opportunity

def run_simulator(interval=5):
    """
    Run the market data simulator.
    
    Args:
        interval: Time between simulated events in seconds
    """
    print("Starting Market Data Simulator...")
    print(f"Publishing to 'market-data-events' every {interval} seconds")
    
    try:
        while True:
            opportunity = generate_opportunity()
            print(f"[SIMULATOR] Generated opportunity for {opportunity['pair']}: {opportunity['dex_a']} vs {opportunity['dex_b']}")
            
            # Publish to the event bus
            event_bus.publish('market-data-events', opportunity)
            
            # Wait for the next interval
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Simulator stopped.")

if __name__ == "__main__":
    run_simulator()