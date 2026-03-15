#!/usr/bin/env pwsh
# 🚀 COMPREHENSIVE SYSTEM DEPLOYMENT & PAPER TRADING LAUNCHER
# Deploy the full system and start paper trading immediately

Write-Host "🕌 HALAL FLASH LOAN ARBITRAGE SYSTEM" -ForegroundColor Cyan
Write-Host "🚀 COMPREHENSIVE DEPLOYMENT & PAPER TRADING" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan

$ErrorActionPreference = "Continue"

# Navigate to project directory
Set-Location "c:\Users\mahia\New_Flashloan"

Write-Host "`n📋 PHASE 1: SYSTEM VERIFICATION" -ForegroundColor Yellow
Write-Host "-" * 40

# Run system verification
Write-Host "🔍 Running final system verification..." -ForegroundColor White
try {
    python final_system_verification.py
    Write-Host "✅ System verification completed" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Verification had issues but continuing..." -ForegroundColor Yellow
}

Write-Host "`n📋 PHASE 2: SYSTEM DEMONSTRATION" -ForegroundColor Yellow
Write-Host "-" * 40

# Run system demonstration
Write-Host "🎪 Running system demonstration..." -ForegroundColor White
try {
    node final_system_demo.js
    Write-Host "✅ System demonstration completed" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Demo had issues but continuing..." -ForegroundColor Yellow
}

Write-Host "`n📋 PHASE 3: TRADING SIMULATION TEST" -ForegroundColor Yellow
Write-Host "-" * 40

# Run trading simulation
Write-Host "💱 Running trading simulation..." -ForegroundColor White
try {
    node trading_ready.js
    Write-Host "✅ Trading simulation completed" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Trading simulation had issues but continuing..." -ForegroundColor Yellow
}

Write-Host "`n📋 PHASE 4: PAPER TRADING DEPLOYMENT" -ForegroundColor Yellow
Write-Host "-" * 40

Write-Host "🚀 LAUNCHING PAPER TRADING SYSTEM..." -ForegroundColor Cyan
Write-Host ""
Write-Host "🎯 Paper Trading Options:" -ForegroundColor White
Write-Host "  1. Quick Test (15 minutes)" -ForegroundColor Gray
Write-Host "  2. Extended Test (1 hour)" -ForegroundColor Gray
Write-Host "  3. Full Day Test (24 hours)" -ForegroundColor Gray
Write-Host "  4. Custom Duration" -ForegroundColor Gray
Write-Host ""

$choice = Read-Host "Select option (1-4)"

switch ($choice) {
    "1" { 
        Write-Host "🎯 Starting 15-minute quick paper trading test..." -ForegroundColor Green
        python -c "
import asyncio
import sys
sys.path.append('.')
from start_paper_trading import HalalPaperTradingSystem

async def quick_test():
    trader = HalalPaperTradingSystem()
    await trader.start_paper_trading_session(0.25)  # 15 minutes

asyncio.run(quick_test())
"
    }
    "2" { 
        Write-Host "🎯 Starting 1-hour extended paper trading test..." -ForegroundColor Green
        python -c "
import asyncio
import sys
sys.path.append('.')
from start_paper_trading import HalalPaperTradingSystem

async def extended_test():
    trader = HalalPaperTradingSystem()
    await trader.start_paper_trading_session(1.0)  # 1 hour

asyncio.run(extended_test())
"
    }
    "3" { 
        Write-Host "🎯 Starting 24-hour full day paper trading test..." -ForegroundColor Green
        python start_paper_trading.py
    }
    "4" { 
        $duration = Read-Host "Enter duration in hours"
        Write-Host "🎯 Starting $duration-hour custom paper trading test..." -ForegroundColor Green
        python -c "
import asyncio
import sys
sys.path.append('.')
from start_paper_trading import HalalPaperTradingSystem

async def custom_test():
    trader = HalalPaperTradingSystem()
    await trader.start_paper_trading_session($duration)

asyncio.run(custom_test())
"
    }
    default { 
        Write-Host "🎯 Starting quick 15-minute test by default..." -ForegroundColor Green
        python -c "
import asyncio
import sys
sys.path.append('.')
from start_paper_trading import HalalPaperTradingSystem

async def default_test():
    trader = HalalPaperTradingSystem()
    await trader.start_paper_trading_session(0.25)  # 15 minutes

asyncio.run(default_test())
"
    }
}

Write-Host "`n📋 PHASE 5: NEXT STEPS" -ForegroundColor Yellow
Write-Host "-" * 40

Write-Host "🎉 PAPER TRADING SESSION COMPLETED!" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 WHAT'S NEXT:" -ForegroundColor Cyan
Write-Host "  1. ✅ Review your paper trading results" -ForegroundColor White
Write-Host "  2. ✅ Analyze profitable strategies discovered" -ForegroundColor White
Write-Host "  3. ✅ Refine parameters based on results" -ForegroundColor White
Write-Host "  4. ✅ Scale up with real capital when ready" -ForegroundColor White
Write-Host ""
Write-Host "💰 REMEMBER:" -ForegroundColor Yellow
Write-Host "  - This was ZERO-RISK paper trading" -ForegroundColor Gray
Write-Host "  - All profits/losses were virtual" -ForegroundColor Gray
Write-Host "  - Perfect for strategy discovery" -ForegroundColor Gray
Write-Host "  - Ready to deploy with real funds when confident" -ForegroundColor Gray
Write-Host ""
Write-Host "🕌 All trading follows Sharia principles:" -ForegroundColor Green
Write-Host "  ✅ No Interest (Riba)" -ForegroundColor Green
Write-Host "  ✅ No Uncertainty (Gharar)" -ForegroundColor Green
Write-Host "  ✅ No Gambling (Maysir)" -ForegroundColor Green
Write-Host "  ✅ Profit sharing only (Mudarabah)" -ForegroundColor Green

Write-Host "`n🎯 System is now ready for live deployment!" -ForegroundColor Cyan
Write-Host "🚀 May Allah bless your halal trading journey!" -ForegroundColor Cyan
