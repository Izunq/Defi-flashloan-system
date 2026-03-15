"""
Test Data Generator
----------------
This script generates test market data for the arbitrage system.
It creates a JSON file with sample market data that can be used for testing.
"""

import json
import random
import time
from datetime import datetime, timedelta

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

def generate_test_data(num_opportunities=100, time_span_hours=24):
    """
    Generate a set of test market data opportunities.
    
    Args:
        num_opportunities: Number of opportunities to generate
        time_span_hours: Time span in hours to distribute the opportunities
    
    Returns:
        List of opportunity dictionaries
    """
    opportunities = []
    
    # Calculate time step
    time_step = (time_span_hours * 3600) / num_opportunities
    
    # Generate opportunities
    base_time = time.time() - (time_span_hours * 3600)
    for i in range(num_opportunities):
        opportunity = generate_opportunity()
        opportunity["timestamp"] = base_time + (i * time_step)
        opportunities.append(opportunity)
    
    return opportunities

def save_test_data(opportunities, filename="test_market_data.json"):
    """
    Save test data to a JSON file.
    
    Args:
        opportunities: List of opportunity dictionaries
        filename: Output filename
    """
    with open(filename, 'w') as f:
        json.dump(opportunities, f, indent=2)
    
    print(f"✅ {len(opportunities)} test opportunities saved to {filename}")

if __name__ == "__main__":
    print("=== Generating Test Market Data ===")
    
    # Generate test data
    opportunities = generate_test_data(num_opportunities=100, time_span_hours=24)
    
    # Save to file
    save_test_data(opportunities)
    
    print("Done!")