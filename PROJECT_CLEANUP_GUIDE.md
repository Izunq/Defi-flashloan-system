# 🧹 Project Cleanup & Optimization Guide

## 📊 Current Project Size Analysis:
- **Total Files**: 15,573 files
- **Total Size**: ~370 MB
- **Main Space Users**:
  - `node_modules/` (205 MB) - Frontend dependencies
  - `artemis_core/Lib/` (158 MB) - Python virtual environment
  - `src/` (5 MB) - React source code
  - `.git/` (2 MB) - Git history

## 🎯 Recommended Cleanup Actions:

### ✅ **Safe to Clean (Will reduce size by ~360 MB):**

#### 1. **Node Modules** (205 MB)
```powershell
# Can be regenerated with: npm install
Remove-Item node_modules -Recurse -Force
```

#### 2. **Python Virtual Environment** (158 MB)
```powershell
# Remove virtual environment files (keep requirements.txt)
cd artemis_core
Remove-Item Lib -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item Scripts -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item pyvenv.cfg -Force -ErrorAction SilentlyContinue
```

#### 3. **Python Cache Files** (1 MB)
```powershell
# Remove all __pycache__ directories
Get-ChildItem -Recurse -Directory -Name "__pycache__" | Remove-Item -Recurse -Force
```

### 🔧 **Reorganization Steps:**

#### 1. **Move to External Virtual Environment**
Instead of having the venv inside the project:
```powershell
# Create external virtual environment
cd C:\
python -m venv artemis_venv
cd "C:\Users\mahia\New_Flashloan\artemis_core"
# Activate external venv when needed:
# C:\artemis_venv\Scripts\activate
```

#### 2. **Update .gitignore**
Add these to `.gitignore`:
```
node_modules/
artemis_core/Lib/
artemis_core/Scripts/
artemis_core/pyvenv.cfg
__pycache__/
*.pyc
.env
```

### 📁 **Core Project Files (Keep These - Only ~10 MB):**

#### Essential Source Code:
- `src/` - React components and hooks
- `artemis_core/*.py` - Python AI backend (without venv)
- `abi/` - Smart contract ABIs
- `infrastructure/` - Terraform configs
- `*.md` - Documentation
- `package.json` & `requirements.txt` - Dependency lists

#### Configuration Files:
- `vite.config.ts`
- `tsconfig.json`
- `.env.example`
- `hardhat.config.js`

## 🚀 **Quick Cleanup Script:**

### Option 1: Complete Cleanup (Requires reinstall)
```powershell
# Remove large directories
Remove-Item node_modules -Recurse -Force
Remove-Item artemis_core/Lib -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item artemis_core/Scripts -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Directory -Name "__pycache__" | Remove-Item -Recurse -Force

# Project size will be ~10 MB after this
```

### Option 2: Keep Working Environment
```powershell
# Only remove cache and unnecessary files
Get-ChildItem -Recurse -Directory -Name "__pycache__" | Remove-Item -Recurse -Force
Remove-Item temp -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item logs -Recurse -Force -ErrorAction SilentlyContinue
```

## 📋 **To Restore After Cleanup:**

### Frontend:
```powershell
npm install
```

### Backend:
```powershell
cd artemis_core
pip install -r requirements.txt
```

## 💡 **Size Optimization Tips:**

1. **Use .gitignore** - Don't commit large dependencies
2. **External Virtual Envs** - Keep Python venv outside project
3. **Docker Alternative** - Consider containerizing for cleaner deployments
4. **Cloud Deployment** - Move to cloud to reduce local storage

## 🎯 **Recommended Action:**

For immediate relief and better project management:
1. Run **Option 1** cleanup to reduce size to ~10 MB
2. Document the reinstall process 
3. Update .gitignore to prevent future bloat
4. Your core project (source code + configs) is actually quite small!

**The 15,573 files are mostly dependency files that can be regenerated from package.json and requirements.txt!**
