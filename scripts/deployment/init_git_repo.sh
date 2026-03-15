#!/bin/bash
# Git Repository Initialization Script
# Run this script after installing Git

echo "🚀 Initializing Advanced DeFi System Repository..."
echo "=================================================="

# Navigate to project directory
cd "$(dirname "$0")"

# Initialize git repository
echo "📁 Initializing Git repository..."
git init

# Set up Git configuration (optional - customize with your details)
echo "⚙️ Setting up Git configuration..."
# git config user.name "Your Name"
# git config user.email "your.email@example.com"

# Add all files to staging
echo "📋 Adding files to Git staging..."
git add .

# Create initial commit
echo "💾 Creating initial commit..."
git commit -m "🎉 Initial commit: Advanced DeFi Flashloan & Arbitrage System

Features:
✅ Sentinel Agent Architecture (Oracle, MEV, Strategy monitoring)
✅ AI-powered trading strategies with ML models
✅ Cross-chain security and bridge monitoring
✅ MEV protection and oracle manipulation defense
✅ Real-time WebSocket alerts and dashboard integration
✅ Emergency response system with contract pause capabilities
✅ Comprehensive testing framework
✅ Production-ready deployment scripts
✅ Multi-chain support (Ethereum, Polygon, Arbitrum, Optimism)
✅ ZK proof integration and formal verification
✅ Enterprise-grade security and observability"

# Create development branch
echo "🌿 Creating development branch..."
git branch development
git branch feature/sentinel-integration

# Display repository status
echo "📊 Repository Status:"
echo "===================="
git status

echo ""
echo "✅ Git repository initialized successfully!"
echo ""
echo "🔧 Next Steps:"
echo "1. Set up remote repository: git remote add origin <your-repo-url>"
echo "2. Push to remote: git push -u origin main"
echo "3. Configure branch protection rules"
echo "4. Set up CI/CD pipelines"
echo ""
echo "🎯 Available Branches:"
echo "- main: Production-ready code"
echo "- development: Development integration"
echo "- feature/sentinel-integration: Sentinel system features"
echo ""
echo "🛡️ Security Reminder:"
echo "- Never commit private keys or sensitive data"
echo "- Use .env files for configuration"
echo "- Review .gitignore before commits"
echo "- Enable signed commits for security"
