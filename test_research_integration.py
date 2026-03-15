#!/usr/bin/env python3
"""
🧪 RESEARCH TOOLS INTEGRATION TEST
Quick test to check what's installed and working
"""

import os
import sys
from pathlib import Path

def test_matlab():
    """Test MATLAB integration"""
    print("🧮 Testing MATLAB...")
    try:
        # Check if MATLAB executable exists
        import shutil
        matlab_exe = shutil.which('matlab')
        if matlab_exe:
            print(f"✅ MATLAB executable found: {matlab_exe}")
        else:
            print("❌ MATLAB executable not in PATH")
        
        # Test MATLAB Engine for Python
        try:
            import matlab.engine
            print("✅ MATLAB Engine for Python: Available")
            return True
        except ImportError:
            print("❌ MATLAB Engine for Python: Not installed")
            print("💡 Install with: cd(fullfile(matlabroot,'extern','engines','python')); system('python setup.py install')")
            return False
    except Exception as e:
        print(f"❌ MATLAB test error: {e}")
        return False

def test_spss():
    """Test SPSS integration"""
    print("\n📊 Testing SPSS...")
    
    # Check installation paths
    spss_paths = [
        r"C:\Program Files\IBM\SPSS\Statistics\29",
        r"C:\Program Files\IBM\SPSS\Statistics\28",
        r"C:\Program Files (x86)\IBM\SPSS\Statistics\29"
    ]
    
    spss_found = False
    for path in spss_paths:
        if os.path.exists(path):
            print(f"✅ SPSS installation found: {path}")
            spss_found = True
            
            # Check for Amos
            amos_path = os.path.join(os.path.dirname(path), "Amos")
            if os.path.exists(amos_path):
                print(f"✅ SPSS Amos found: {amos_path}")
            break
    
    if not spss_found:
        print("❌ SPSS not found")
        print("💡 Get it free with campus license or 14-day trial")
    
    # Test Python integration
    try:
        import spss
        print("✅ SPSS Python integration: Available")
        return True
    except ImportError:
        print("❌ SPSS Python integration: Not available")
        print("💡 Install through SPSS Extensions menu")
        return spss_found

def test_nvivo():
    """Test NVivo integration"""
    print("\n📝 Testing NVivo...")
    
    nvivo_paths = [
        r"C:\Program Files\QSR\NVivo 14",
        r"C:\Program Files\QSR\NVivo 13", 
        r"C:\Program Files (x86)\QSR\NVivo 14"
    ]
    
    for path in nvivo_paths:
        if os.path.exists(path):
            print(f"✅ NVivo installation found: {path}")
            return True
    
    print("❌ NVivo not found")
    print("💡 Get it free with academic license or 14-day trial")
    return False

def show_current_structure():
    """Show current project structure"""
    print("\n📂 Current Project Structure:")
    
    key_paths = [
        "setup_matlab_integration.py",
        "setup_research_tools.py", 
        "matlab/",
        "research_analytics/",
        "docs/integrations/"
    ]
    
    for path in key_paths:
        full_path = Path(path)
        if full_path.exists():
            if full_path.is_file():
                print(f"✅ {path}")
            else:
                files = list(full_path.iterdir())[:3]  # Show first 3 items
                print(f"✅ {path} ({len(list(full_path.iterdir()))} items)")
                for f in files:
                    print(f"   └── {f.name}")
                if len(list(full_path.iterdir())) > 3:
                    print(f"   └── ... and {len(list(full_path.iterdir())) - 3} more")
        else:
            print(f"❌ {path} (not created yet)")

def main():
    """Main test function"""
    print("🧪 RESEARCH TOOLS INTEGRATION TEST")
    print("=" * 40)
    
    # Test each tool
    matlab_ok = test_matlab()
    spss_ok = test_spss() 
    nvivo_ok = test_nvivo()
    
    # Show structure
    show_current_structure()
    
    # Summary
    print("\n📋 SUMMARY:")
    print("=" * 40)
    print(f"🧮 MATLAB: {'✅ Ready' if matlab_ok else '⚠️ Needs setup'}")
    print(f"📊 SPSS: {'✅ Ready' if spss_ok else '⚠️ Needs installation'}")
    print(f"📝 NVivo: {'✅ Ready' if nvivo_ok else '⚠️ Needs installation'}")
    
    print("\n🚀 NEXT ACTIONS:")
    if not matlab_ok:
        print("1. Run: python setup_matlab_integration.py")
    if not spss_ok:
        print("2. Install SPSS Statistics + Amos (campus license)")
    if not nvivo_ok:
        print("3. Install NVivo (academic license)")
    
    print("4. Run: python setup_research_tools.py")
    print("5. Run: streamlit run research_analytics/research_dashboard.py")

if __name__ == "__main__":
    main()
