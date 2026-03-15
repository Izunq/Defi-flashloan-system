#!/bin/bash
# Smart Project Optimization for AI Analysis

echo "🤖 Optimizing project for AI analysis..."
echo "Keeping all essential files while removing bulk dependencies"

# Create optimized project structure
mkdir -p optimized_artemis/{src,artemis_core,abi,infrastructure,docs}

# Copy essential source files
echo "📁 Copying core source files..."
cp -r src/ optimized_artemis/
cp -r abi/ optimized_artemis/
cp -r infrastructure/ optimized_artemis/

# Copy essential backend files (without venv)
echo "🐍 Copying Python core files..."
cp artemis_core/*.py optimized_artemis/artemis_core/
cp artemis_core/*.txt optimized_artemis/artemis_core/
cp artemis_core/.env.example optimized_artemis/artemis_core/

# Copy configuration files
echo "⚙️ Copying configuration..."
cp package.json optimized_artemis/
cp vite.config.ts optimized_artemis/
cp tsconfig.json optimized_artemis/ 2>/dev/null || true
cp hardhat.config.js optimized_artemis/ 2>/dev/null || true

# Copy all documentation
echo "📚 Copying documentation..."
cp *.md optimized_artemis/docs/

# Create restore script
cat > optimized_artemis/restore_dependencies.sh << 'EOF'
#!/bin/bash
echo "🔄 Restoring dependencies..."

# Install Node.js dependencies
echo "📦 Installing frontend dependencies..."
npm install

# Create Python virtual environment
echo "🐍 Setting up Python environment..."
cd artemis_core
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

echo "✅ Dependencies restored!"
echo "To start:"
echo "1. Frontend: npm run dev"
echo "2. Backend: cd artemis_core && source venv/bin/activate && python artemis_ai_core.py"
EOF

chmod +x optimized_artemis/restore_dependencies.sh

# Create Windows restore script
cat > optimized_artemis/restore_dependencies.bat << 'EOF'
@echo off
echo 🔄 Restoring dependencies...

echo 📦 Installing frontend dependencies...
npm install

echo 🐍 Setting up Python environment...
cd artemis_core
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt

echo ✅ Dependencies restored!
echo To start:
echo 1. Frontend: npm run dev
echo 2. Backend: cd artemis_core && venv\Scripts\activate && python artemis_ai_core.py
pause
EOF

# Calculate sizes
original_size=$(du -sh . | cut -f1)
optimized_size=$(du -sh optimized_artemis | cut -f1)

echo "📊 Optimization complete!"
echo "Original project: $original_size"
echo "Optimized for AI: $optimized_size"
echo "📁 Optimized project available in: optimized_artemis/"
echo ""
echo "🤖 This optimized version contains:"
echo "   ✅ All source code and configuration"
echo "   ✅ Complete documentation"
echo "   ✅ Infrastructure definitions"
echo "   ✅ Smart contract ABIs"
echo "   ✅ Dependency restoration scripts"
echo "   ❌ node_modules/ and Python venv (can be restored)"
echo ""
echo "Perfect for AI analysis with minimal size!"
