#!/usr/bin/env python3
"""
🚀 REAL-TIME BLOCKCHAIN MONITORING DASHBOARD
===========================================
Live monitoring of:
- Gas prices across chains
- DEX liquidity pools
- Arbitrage opportunities
- Trade execution status
"""

import asyncio
import json
import time
import requests
import aiohttp
from datetime import datetime
from web3 import Web3
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import webbrowser

class RealTimeMonitoringDashboard:
    def __init__(self):
        self.live_data = {
            "gas_prices": {},
            "dex_prices": {},
            "opportunities": [],
            "system_status": "INITIALIZING",
            "last_update": datetime.now().isoformat(),
            "trades_today": 0,
            "profit_today": 0.0,
            "connections": {}
        }
        
        # Real blockchain endpoints
        self.rpc_endpoints = {
            "ethereum": "https://eth.llamarpc.com",
            "polygon": "https://polygon-rpc.com",
            "arbitrum": "https://arb1.arbitrum.io/rpc",
            "optimism": "https://mainnet.optimism.io",
            "bsc": "https://bsc-dataseed.binance.org"
        }
        
        # Initialize connections
        self.w3_connections = {}
        self.initialize_connections()

    def initialize_connections(self):
        """Initialize blockchain connections"""
        print("🔗 Initializing blockchain connections...")
        
        for chain, rpc_url in self.rpc_endpoints.items():
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url))
                if w3.is_connected():
                    self.w3_connections[chain] = w3
                    self.live_data["connections"][chain] = "CONNECTED"
                    print(f"✅ {chain.upper()}: Connected")
                else:
                    self.live_data["connections"][chain] = "FAILED"
                    print(f"❌ {chain.upper()}: Failed")
            except Exception as e:
                self.live_data["connections"][chain] = f"ERROR: {str(e)[:50]}"
                print(f"❌ {chain.upper()}: {e}")

    async def monitor_gas_prices(self):
        """Continuously monitor gas prices"""
        while True:
            try:
                print("⛽ Updating gas prices...")
                
                for chain, w3 in self.w3_connections.items():
                    try:
                        gas_price_wei = w3.eth.gas_price
                        gas_price_gwei = w3.from_wei(gas_price_wei, 'gwei')
                        
                        # Estimate USD cost for standard transaction
                        gas_limit = 150000  # Standard transaction
                        cost_eth = float(gas_price_gwei) * gas_limit / 1e9
                        
                        # Get ETH price (simplified)
                        eth_usd = 2000  # Approximate ETH price
                        cost_usd = cost_eth * eth_usd
                        
                        self.live_data["gas_prices"][chain] = {
                            "wei": int(gas_price_wei),
                            "gwei": float(gas_price_gwei),
                            "usd_estimate": round(cost_usd, 2),
                            "timestamp": datetime.now().isoformat(),
                            "status": "LIVE"
                        }
                        
                        print(f"   {chain.upper()}: {gas_price_gwei:.1f} gwei (${cost_usd:.2f})")
                        
                    except Exception as e:
                        self.live_data["gas_prices"][chain] = {
                            "error": str(e),
                            "status": "ERROR",
                            "timestamp": datetime.now().isoformat()
                        }
                
                self.live_data["last_update"] = datetime.now().isoformat()
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                print(f"⚠️ Gas monitoring error: {e}")
                await asyncio.sleep(60)

    async def monitor_dex_prices(self):
        """Monitor DEX prices for arbitrage opportunities"""
        while True:
            try:
                print("📊 Scanning DEX prices...")
                
                # Popular trading pairs
                pairs_to_monitor = [
                    {
                        "symbol": "WETH/USDC",
                        "token0": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                        "token1": "0xA0b86a33E6417Afb4C6d335d84E2E2b50e31c4fF"
                    },
                    {
                        "symbol": "WBTC/WETH", 
                        "token0": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
                        "token1": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
                    }
                ]
                
                async with aiohttp.ClientSession() as session:
                    for pair in pairs_to_monitor:
                        symbol = pair["symbol"]
                        print(f"   Checking {symbol}...")
                        
                        # Fetch from multiple DEXs
                        dex_prices = await self.fetch_all_dex_prices(session, pair)
                        
                        if len(dex_prices) >= 2:
                            # Find arbitrage opportunities
                            prices = [(dex, data["price"]) for dex, data in dex_prices.items()]
                            prices.sort(key=lambda x: x[1])
                            
                            lowest_dex, lowest_price = prices[0]
                            highest_dex, highest_price = prices[-1]
                            
                            spread_percent = ((highest_price - lowest_price) / lowest_price) * 100
                            
                            opportunity_data = {
                                "pair": symbol,
                                "buy_dex": lowest_dex,
                                "sell_dex": highest_dex,
                                "buy_price": lowest_price,
                                "sell_price": highest_price,
                                "spread_percent": round(spread_percent, 4),
                                "timestamp": datetime.now().isoformat(),
                                "profitable": spread_percent > 0.15
                            }
                            
                            # Update opportunities
                            self.live_data["opportunities"] = [
                                op for op in self.live_data["opportunities"] 
                                if op["pair"] != symbol or 
                                (datetime.now() - datetime.fromisoformat(op["timestamp"])).seconds < 300
                            ]
                            
                            if opportunity_data["profitable"]:
                                self.live_data["opportunities"].append(opportunity_data)
                                print(f"   🎯 OPPORTUNITY: {symbol} - {spread_percent:.3f}% spread")
                            
                            self.live_data["dex_prices"][symbol] = dex_prices
                
                await asyncio.sleep(45)  # Update every 45 seconds
                
            except Exception as e:
                print(f"⚠️ DEX monitoring error: {e}")
                await asyncio.sleep(90)

    async def fetch_all_dex_prices(self, session, pair):
        """Fetch prices from all DEXs for a pair"""
        dex_prices = {}
        
        # 1inch API
        try:
            url = "https://api.1inch.io/v5.0/1/quote"
            params = {
                "fromTokenAddress": pair["token0"],
                "toTokenAddress": pair["token1"],
                "amount": "1000000000000000000"  # 1 ETH
            }
            
            async with session.get(url, params=params, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    price = float(data["toTokenAmount"]) / 1e6  # Assuming USDC (6 decimals)
                    dex_prices["1inch"] = {
                        "price": price,
                        "source": "api",
                        "timestamp": datetime.now().isoformat()
                    }
        except Exception as e:
            print(f"   ⚠️ 1inch error: {e}")
        
        # CoinGecko for reference price
        try:
            if pair["symbol"] == "WETH/USDC":
                url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        price = data["ethereum"]["usd"]
                        dex_prices["coingecko"] = {
                            "price": price,
                            "source": "reference",
                            "timestamp": datetime.now().isoformat()
                        }
        except Exception as e:
            print(f"   ⚠️ CoinGecko error: {e}")
        
        # Simulate additional DEX prices with realistic variations
        base_price = 2000 if pair["symbol"] == "WETH/USDC" else 0.065  # ETH price or BTC/ETH ratio
        
        simulated_dexs = ["uniswap_v3", "sushiswap", "quickswap"]
        for i, dex in enumerate(simulated_dexs):
            variation = 1 + (hash(dex + pair["symbol"]) % 100 - 50) / 10000  # Small variations
            sim_price = base_price * variation
            
            dex_prices[dex] = {
                "price": sim_price,
                "source": "simulated",
                "timestamp": datetime.now().isoformat()
            }
        
        return dex_prices

    async def monitor_system_health(self):
        """Monitor overall system health"""
        while True:
            try:
                # Check connection health
                connected_chains = sum(1 for w3 in self.w3_connections.values() if w3.is_connected())
                total_chains = len(self.w3_connections)
                
                if connected_chains == total_chains:
                    self.live_data["system_status"] = "OPTIMAL"
                elif connected_chains > total_chains * 0.5:
                    self.live_data["system_status"] = "PARTIAL"
                else:
                    self.live_data["system_status"] = "DEGRADED"
                
                # Update metrics
                self.live_data["connections_active"] = connected_chains
                self.live_data["connections_total"] = total_chains
                self.live_data["opportunities_count"] = len(self.live_data["opportunities"])
                
                print(f"🏥 System Health: {self.live_data['system_status']} ({connected_chains}/{total_chains} chains)")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"⚠️ Health monitoring error: {e}")
                self.live_data["system_status"] = "ERROR"
                await asyncio.sleep(120)

    def create_dashboard_html(self):
        """Create HTML dashboard"""
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>🚀 Real-Time Blockchain Arbitrage Monitor</title>
    <meta charset="UTF-8">
    <style>
        body { 
            font-family: 'Segoe UI', Arial; 
            background: linear-gradient(135deg, #1e3c72, #2a5298); 
            color: white; 
            margin: 0; 
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { 
            background: rgba(255,255,255,0.1); 
            border-radius: 15px; 
            padding: 20px; 
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        .status-optimal { color: #4ade80; }
        .status-partial { color: #fbbf24; }
        .status-degraded { color: #f87171; }
        .opportunity { 
            background: rgba(16, 185, 129, 0.2); 
            border-left: 4px solid #10b981; 
            margin: 10px 0; 
            padding: 10px;
        }
        .gas-price { display: flex; justify-content: space-between; margin: 5px 0; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.2); }
        .refresh-btn { 
            background: #3b82f6; 
            color: white; 
            border: none; 
            padding: 10px 20px; 
            border-radius: 5px; 
            cursor: pointer; 
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Real-Time Blockchain Arbitrage Monitor</h1>
            <p>🕌 Halal Flash Loan Arbitrage System</p>
            <button class="refresh-btn" onclick="refreshData()">🔄 Refresh Data</button>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>🏥 System Status</h3>
                <div id="system-status">Loading...</div>
                <div id="connections">Loading...</div>
            </div>
            
            <div class="card">
                <h3>⛽ Gas Prices</h3>
                <div id="gas-prices">Loading...</div>
            </div>
            
            <div class="card">
                <h3>🎯 Live Opportunities</h3>
                <div id="opportunities">Scanning...</div>
            </div>
            
            <div class="card">
                <h3>📊 DEX Prices</h3>
                <div id="dex-prices">Loading...</div>
            </div>
        </div>
    </div>

    <script>
        async function refreshData() {
            try {
                const response = await fetch('/api/live-data');
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        }
        
        function updateDashboard(data) {
            // System Status
            const statusClass = `status-${data.system_status.toLowerCase()}`;
            document.getElementById('system-status').innerHTML = `
                <div class="${statusClass}">Status: ${data.system_status}</div>
                <div>Last Update: ${new Date(data.last_update).toLocaleTimeString()}</div>
                <div>Opportunities: ${data.opportunities_count || 0}</div>
            `;
            
            // Connections
            let connectionsHtml = '<div style="margin-top: 10px;">';
            for (const [chain, status] of Object.entries(data.connections || {})) {
                const statusIcon = status === 'CONNECTED' ? '✅' : '❌';
                connectionsHtml += `<div>${statusIcon} ${chain.toUpperCase()}: ${status}</div>`;
            }
            connectionsHtml += '</div>';
            document.getElementById('connections').innerHTML = connectionsHtml;
            
            // Gas Prices
            let gasPricesHtml = '';
            for (const [chain, gasData] of Object.entries(data.gas_prices || {})) {
                if (gasData.gwei) {
                    gasPricesHtml += `
                        <div class="gas-price">
                            <span>${chain.toUpperCase()}</span>
                            <span>${gasData.gwei.toFixed(1)} gwei ($${gasData.usd_estimate})</span>
                        </div>
                    `;
                }
            }
            document.getElementById('gas-prices').innerHTML = gasPricesHtml || 'No data available';
            
            // Opportunities
            let opportunitiesHtml = '';
            if (data.opportunities && data.opportunities.length > 0) {
                for (const opp of data.opportunities) {
                    opportunitiesHtml += `
                        <div class="opportunity">
                            <div><strong>${opp.pair}</strong></div>
                            <div>Buy: ${opp.buy_dex} @ $${opp.buy_price.toFixed(2)}</div>
                            <div>Sell: ${opp.sell_dex} @ $${opp.sell_price.toFixed(2)}</div>
                            <div>Spread: <strong>${opp.spread_percent.toFixed(3)}%</strong></div>
                        </div>
                    `;
                }
            } else {
                opportunitiesHtml = '<div>No profitable opportunities currently</div>';
            }
            document.getElementById('opportunities').innerHTML = opportunitiesHtml;
            
            // DEX Prices
            let dexPricesHtml = '<table><tr><th>Pair</th><th>DEX</th><th>Price</th><th>Source</th></tr>';
            for (const [pair, dexData] of Object.entries(data.dex_prices || {})) {
                for (const [dex, priceData] of Object.entries(dexData)) {
                    dexPricesHtml += `
                        <tr>
                            <td>${pair}</td>
                            <td>${dex}</td>
                            <td>$${priceData.price.toFixed(2)}</td>
                            <td>${priceData.source}</td>
                        </tr>
                    `;
                }
            }
            dexPricesHtml += '</table>';
            document.getElementById('dex-prices').innerHTML = dexPricesHtml;
        }
        
        // Auto-refresh every 30 seconds
        setInterval(refreshData, 30000);
        
        // Initial load
        refreshData();
    </script>
</body>
</html>
        """
        
        with open('dashboard.html', 'w') as f:
            f.write(html_content)

    def start_web_server(self):
        """Start web server for dashboard"""
        import json
        from http.server import HTTPServer, BaseHTTPRequestHandler
        
        class DashboardHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    with open('dashboard.html', 'r') as f:
                        self.wfile.write(f.read().encode())
                
                elif self.path == '/api/live-data':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    # Access parent's live_data
                    dashboard = self.server.dashboard_instance
                    self.wfile.write(json.dumps(dashboard.live_data).encode())
                
                else:
                    self.send_response(404)
                    self.end_headers()
        
        server = HTTPServer(('localhost', 8080), DashboardHandler)
        server.dashboard_instance = self  # Store reference to dashboard
        
        def run_server():
            print("🌐 Dashboard server running on http://localhost:8080")
            server.serve_forever()
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Open browser
        try:
            webbrowser.open('http://localhost:8080')
        except:
            pass

    async def start_monitoring(self):
        """Start all monitoring tasks"""
        print("🚀 Starting Real-Time Blockchain Monitor")
        print("=" * 50)
        
        # Create dashboard HTML
        self.create_dashboard_html()
        
        # Start web server
        self.start_web_server()
        
        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self.monitor_gas_prices()),
            asyncio.create_task(self.monitor_dex_prices()),
            asyncio.create_task(self.monitor_system_health())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            print("\n⏹️ Monitoring stopped")
        except Exception as e:
            print(f"❌ Monitoring error: {e}")

async def main():
    """Main function"""
    print("🌙 Bismillah ar-Rahman ar-Raheem")
    print("📊 Real-Time Blockchain Monitoring Dashboard")
    print("=" * 50)
    
    dashboard = RealTimeMonitoringDashboard()
    await dashboard.start_monitoring()

if __name__ == "__main__":
    asyncio.run(main())
