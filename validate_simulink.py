"""
🎯 Quick Simulink Integration Validation
Simple validation of the premium integration setup
"""

import os
import sys
from pathlib import Path

def validate_integration():
    """Quick validation of the integration setup"""
    print("🚀 Premium Simulink Integration - Quick Validation")
    print("=" * 60)
    
    # Check core structure
    checks = [
        ("Core directory", "simulink"),
        ("Models directory", "simulink/models"),
        ("Scripts directory", "simulink/scripts"),
        ("Premium models script", "simulink/scripts/create_premium_models.m"),
        ("Demo script", "simulink/scripts/demo_advanced_trading.m"),
        ("Python bridge", "simulink/simulink_bridge.py"),
        ("Documentation", "simulink/README.md"),
        ("Setup script", "setup_simulink_integration.py"),
        ("Integration status", "PREMIUM_SIMULINK_INTEGRATION_COMPLETE.md")
    ]
    
    passed = 0
    total = len(checks)
    
    for name, path in checks:
        exists = os.path.exists(path)
        status = "✅ PASS" if exists else "❌ FAIL"
        print(f"   {name:.<30} {status}")
        if exists:
            passed += 1
    
    print("\n📊 Validation Summary:")
    print(f"   Passed: {passed}/{total} ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("   🎉 Perfect! Integration is complete and ready.")
        print("   🚀 Ready for MATLAB model creation and testing.")
    elif passed >= total * 0.8:
        print("   👍 Good! Most components are in place.")
        print("   🔧 Review any missing components above.")
    else:
        print("   ⚠️  Integration needs attention.")
        print("   🛠️  Please run setup_simulink_integration.py")
    
    # Check for advanced features
    print("\n🔬 Advanced Features Check:")
    advanced_features = [
        ("Deep Learning models", "simulink/models/deep_learning"),
        ("RL models", "simulink/models/reinforcement_learning"),
        ("Econometric models", "simulink/models/econometrics"),
        ("Optimization models", "simulink/models/optimization"),
        ("HFT models", "simulink/models/parallel"),
        ("Stateflow models", "simulink/models/stateflow"),
        ("Signal processing", "simulink/models/signal_processing")
    ]
    
    advanced_passed = 0
    for name, path in advanced_features:
        exists = os.path.exists(path)
        status = "✅" if exists else "📁"
        print(f"   {name:.<30} {status}")
        if exists:
            advanced_passed += 1
    
    print(f"\n   Advanced Features: {advanced_passed}/{len(advanced_features)} ready")
    
    print("\n🎯 Next Steps:")
    print("   1. Open MATLAB and run: cd('simulink/scripts')")
    print("   2. Execute: create_premium_models()")
    print("   3. Test with: demo_advanced_trading()")
    print("   4. Deploy to production when ready")
    
    print("\n📚 Documentation:")
    print("   📖 Complete guide: simulink/README.md")
    print("   📊 Integration status: PREMIUM_SIMULINK_INTEGRATION_COMPLETE.md")
    print("   🎯 Architecture: docs/SIMULINK_INTEGRATION_ARCHITECTURE.md")

if __name__ == "__main__":
    validate_integration()
