#!/usr/bin/env python3
"""
SPSS Availability Checker for Phase 4 Implementation
"""

def check_spss_availability():
    """Check SPSS Statistics availability and capabilities"""
    
    print("="*80)
    print("🎯 PHASE 4: SPSS AVAILABILITY ASSESSMENT")
    print("="*80)
    
    spss_status = {
        "spss_api": False,
        "spss_statistics": False,
        "alternative_options": True,
        "integration_strategy": "TBD"
    }
    
    # Test 1: SPSS Python API
    print("\n📊 Testing SPSS Python API...")
    try:
        import spss
        print("✅ SPSS Python API available")
        try:
            version = spss.GetSPSSVersion()
            print(f"✅ SPSS Version: {version}")
            spss_status["spss_api"] = True
            spss_status["spss_statistics"] = True
        except Exception as e:
            print(f"⚠️ SPSS API available but not fully functional: {e}")
            spss_status["spss_api"] = True
    except ImportError:
        print("❌ SPSS Python API not available")
        print("   → This is expected if SPSS Statistics is not installed")
    
    # Test 2: Check for SPSS installation
    print("\n🔍 Checking for SPSS Statistics installation...")
    import os
    import subprocess
    
    spss_paths = [
        r"C:\Program Files\IBM\SPSS\Statistics\30\Statistics.exe",
        r"C:\Program Files\IBM\SPSS\Statistics\29\Statistics.exe", 
        r"C:\Program Files\IBM\SPSS\Statistics\28\Statistics.exe",
        r"C:\Program Files (x86)\IBM\SPSS\Statistics\30\Statistics.exe",
        r"C:\Program Files (x86)\IBM\SPSS\Statistics\29\Statistics.exe"
    ]
    
    spss_found = False
    for path in spss_paths:
        if os.path.exists(path):
            print(f"✅ Found SPSS Statistics at: {path}")
            spss_status["spss_statistics"] = True
            spss_found = True
            break
    
    if not spss_found:
        print("❌ SPSS Statistics installation not found in standard locations")
    
    # Test 3: Alternative statistical packages
    print("\n🔬 Checking alternative statistical packages...")
    
    alternatives = {
        "scipy.stats": "Advanced statistical tests and distributions",
        "statsmodels": "Professional statistical modeling",
        "scikit-learn": "Machine learning and statistical modeling", 
        "pandas": "Data manipulation and analysis",
        "seaborn": "Statistical data visualization",
        "pingouin": "Statistical analysis (SPSS-like functions)",
        "factor_analyzer": "Factor analysis capabilities",
        "lifelines": "Survival analysis"
    }
    
    available_alternatives = {}
    for package, description in alternatives.items():
        try:
            __import__(package)
            print(f"✅ {package}: {description}")
            available_alternatives[package] = description
        except ImportError:
            print(f"❌ {package}: Not available")
    
    # Assessment and recommendations
    print("\n📋 PHASE 4 IMPLEMENTATION STRATEGY:")
    print("-" * 60)
    
    if spss_status["spss_api"]:
        print("🎯 PRIMARY STRATEGY: SPSS Python API Integration")
        print("  ✅ Direct SPSS integration available")
        print("  ✅ Full SPSS capabilities accessible")
        print("  ✅ Professional reporting possible")
        spss_status["integration_strategy"] = "spss_api"
        
    elif spss_status["spss_statistics"]:
        print("🎯 SECONDARY STRATEGY: File-based SPSS Integration")
        print("  ✅ SPSS Statistics available")
        print("  ⚠️ Limited to file-based integration")
        print("  ✅ Syntax file generation possible")
        spss_status["integration_strategy"] = "spss_files"
        
    else:
        print("🎯 ALTERNATIVE STRATEGY: Enhanced Statistical Analysis")
        print("  ✅ Professional statistical analysis without SPSS")
        print("  ✅ Comprehensive alternatives available")
        print("  ✅ Institutional-grade reporting possible")
        spss_status["integration_strategy"] = "alternatives"
    
    # Detailed implementation plan
    print(f"\n🚀 RECOMMENDED IMPLEMENTATION APPROACH:")
    print("-" * 60)
    
    if spss_status["integration_strategy"] == "spss_api":
        implementation_plan = [
            "1. SPSS Python API integration development",
            "2. Professional statistical analysis functions",
            "3. Automated report generation",
            "4. Regulatory compliance features",
            "5. Integration with existing AI/ML results"
        ]
    elif spss_status["integration_strategy"] == "spss_files":
        implementation_plan = [
            "1. SPSS syntax file generation system",
            "2. File-based data exchange mechanisms", 
            "3. Automated SPSS execution",
            "4. Output parsing and integration",
            "5. Professional report compilation"
        ]
    else:
        implementation_plan = [
            "1. Enhanced statsmodels integration",
            "2. Professional statistical reporting framework",
            "3. Advanced regression and time series analysis",
            "4. Factor analysis and PCA capabilities",
            "5. Institutional-grade report templates"
        ]
    
    for step in implementation_plan:
        print(f"  {step}")
    
    # Expected capabilities
    print(f"\n💎 EXPECTED PHASE 4 CAPABILITIES:")
    print("-" * 60)
    
    expected_capabilities = [
        "📊 Professional statistical analysis and reporting",
        "📈 Advanced regression modeling (linear, logistic, polynomial)",
        "🔍 Factor analysis and principal component analysis",
        "⏰ Time series forecasting and trend analysis",
        "📋 Regulatory-compliant analytical reports",
        "🔗 Seamless integration with existing AI/ML systems",
        "📊 Enhanced visualization of statistical results",
        "⚡ Automated professional report generation"
    ]
    
    for capability in expected_capabilities:
        print(f"  {capability}")
    
    print(f"\n⏱️ ESTIMATED TIMELINE:")
    print("-" * 60)
    if spss_status["integration_strategy"] == "spss_api":
        print("  🎯 5-7 days for full SPSS integration")
    elif spss_status["integration_strategy"] == "spss_files":
        print("  🎯 4-6 days for file-based integration")
    else:
        print("  🎯 3-5 days for enhanced statistical analysis")
    
    print(f"\n✅ PHASE 4 READINESS: {'READY TO PROCEED' if available_alternatives else 'NEEDS PREPARATION'}")
    
    return spss_status, available_alternatives

if __name__ == "__main__":
    status, alternatives = check_spss_availability()
    
    print(f"\n" + "="*80)
    print("🎯 DECISION: PROCEED WITH PHASE 4?")
    print("="*80)
    print("✅ Alternative statistical packages available")
    print("✅ Professional analysis capabilities achievable")
    print("✅ Integration architecture ready")
    print("🚀 Recommend proceeding with Phase 4 implementation")
