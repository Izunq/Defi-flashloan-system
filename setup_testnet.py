#!/usr/bin/env python3
"""
🔧 TESTNET SETUP WIZARD
======================
Set up your testnet environment for 24-hour testing
"""

import os
import json
import subprocess
from eth_account import Account

def setup_testnet_environment():
    print("🌙 Bismillah - Setting up Testnet Environment")
    print("=" * 50)
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("📝 Creating .env file...")
        create_env_file()
    else:
        print("✅ .env file exists")
    
    # Check for private key
    if not os.getenv('PRIVATE_KEY'):
        print("\n🔑 No private key found. Options:")
        print("1. Generate new testnet wallet")
        print("2. Use existing wallet")
        choice = input("Choose (1 or 2): ").strip()
        
        if choice == "1":
            generate_testnet_wallet()
        else:
            setup_existing_wallet()
    else:
        print("✅ Private key configured")
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    install_dependencies()
    
    # Check network connectivity
    print("\n🔗 Testing network connectivity...")
    test_networks()
    
    # Provide faucet instructions
    print("\n🚰 GET TESTNET TOKENS:")
    print_faucet_instructions()
    
    print("\n✅ Testnet environment setup complete!")
    print("🚀 Ready to run: python testnet_trading_24h.py")

def create_env_file():
    env_content = """# Testnet Environment Variables
PRIVATE_KEY=
MUMBAI_RPC_URL=https://rpc-mumbai.maticvigil.com
ARBITRUM_GOERLI_RPC_URL=https://goerli-rollup.arbitrum.io/rpc
OPTIMISM_GOERLI_RPC_URL=https://goerli.optimism.io
TESTNET_STARTING_CAPITAL_USD=75
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env file")

def generate_testnet_wallet():
    print("\n🔐 Generating new testnet wallet...")
    account = Account.create()
    
    print(f"📮 Address: {account.address}")
    print(f"🔑 Private Key: {account.key.hex()}")
    
    # Update .env file
    update_env_private_key(account.key.hex())
    
    print("✅ Wallet generated and saved to .env")
    print("⚠️  IMPORTANT: This is for TESTNET ONLY!")

def setup_existing_wallet():
    private_key = input("Enter your private key (0x...): ").strip()
    if not private_key.startswith('0x'):
        private_key = '0x' + private_key
    
    try:
        account = Account.from_key(private_key)
        print(f"✅ Wallet address: {account.address}")
        update_env_private_key(private_key)
    except Exception as e:
        print(f"❌ Invalid private key: {e}")

def update_env_private_key(private_key):
    with open('.env', 'r') as f:
        content = f.read()
    
    # Update PRIVATE_KEY line
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('PRIVATE_KEY='):
            lines[i] = f'PRIVATE_KEY={private_key}'
            break
    
    with open('.env', 'w') as f:
        f.write('\n'.join(lines))

def install_dependencies():
    try:
        # Python dependencies
        subprocess.run(['pip', 'install', 'web3', 'eth-account', 'python-dotenv'], check=True)
        
        # Node.js dependencies  
        if os.path.exists('package.json'):
            subprocess.run(['npm', 'install'], check=True)
        else:
            subprocess.run(['npm', 'init', '-y'], check=True)
            subprocess.run(['npm', 'install', 'hardhat', '@nomicfoundation/hardhat-toolbox', 'dotenv'], check=True)
        
        print("✅ Dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")

def test_networks():
    networks = {
        'Mumbai': 'https://rpc-mumbai.maticvigil.com',
        'Arbitrum Goerli': 'https://goerli-rollup.arbitrum.io/rpc',
        'Optimism Goerli': 'https://goerli.optimism.io'
    }
    
    for name, url in networks.items():
        try:
            import requests
            response = requests.post(url, json={
                "jsonrpc": "2.0",
                "method": "eth_blockNumber",
                "params": [],
                "id": 1
            }, timeout=5)
            
            if response.status_code == 200:
                print(f"   ✅ {name}: Connected")
            else:
                print(f"   ❌ {name}: Failed ({response.status_code})")
        except Exception as e:
            print(f"   ❌ {name}: Error - {e}")

def print_faucet_instructions():
    print("🚰 Get testnet tokens from these faucets:")
    print("   • Polygon Mumbai: https://faucet.polygon.technology/")
    print("   • Arbitrum Goerli: https://bridge.arbitrum.io/")  
    print("   • Optimism Goerli: https://app.optimism.io/faucet")
    print("   • Sepolia ETH: https://sepoliafaucet.com/")
    print("\n💡 You need small amounts (~0.1 ETH) for gas fees")
    print("💰 Total needed: ~$1-5 worth for 24-hour testing")

if __name__ == "__main__":
    setup_testnet_environment()
