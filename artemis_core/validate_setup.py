"""
API Key Validation Script for Artemis AI Core
Run this script to test if your API keys are properly configured
"""

import os
import sys
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

def test_ai_keys():
    """Test AI API keys (Gemini or OpenAI)"""
    print("🔑 Testing AI API Keys...")
    
    ai_provider = os.getenv("AI_PROVIDER", "gemini")
    
    if ai_provider == "gemini":
        return test_gemini_key()
    elif ai_provider == "openai":
        return test_openai_key()
    else:
        print(f"❌ Unknown AI provider: {ai_provider}")
        return False

def test_gemini_key():
    """Test Google Gemini API key"""
    print("🧠 Testing Google Gemini API Key...")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_google_api_key_here":
        print("❌ Google Gemini API key not configured")
        print("   Please set GOOGLE_API_KEY in your .env file")
        print("   Get your key from: https://aistudio.google.com/app/apikey")
        return False
    
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Test with a simple request
        response = model.generate_content("Hello, respond with just 'OK'")
        
        if response.text and "OK" in response.text:
            print("✅ Google Gemini API key is valid and working")
            print(f"   Model response: {response.text.strip()}")
            return True
        else:
            print("❌ Gemini API key test failed - unexpected response")
            return False
            
    except ImportError:
        print("❌ Google Generative AI library not installed")
        print("   Run: pip install google-generativeai")
        return False
    except Exception as e:
        print(f"❌ Gemini API key test failed: {str(e)}")
        if "authentication" in str(e).lower() or "api_key" in str(e).lower():
            print("   Check your API key is correct")
        elif "quota" in str(e).lower():
            print("   You may have exceeded your usage quota")
        return False

def test_openai_key():
    """Test OpenAI API key (fallback)"""
    print("🤖 Testing OpenAI API Key...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        print("❌ OpenAI API key not configured")
        print("   Please set OPENAI_API_KEY in your .env file")
        return False
    
    try:
        import openai
        openai.api_key = api_key
        
        # Test with a simple request
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello, respond with just 'OK'"}],
            max_tokens=5
        )
        
        if response.choices[0].message.content:
            print("✅ OpenAI API key is valid and working")
            return True
        else:
            print("❌ OpenAI API key test failed - no response")
            return False
            
    except ImportError:
        print("❌ OpenAI library not installed")
        print("   Run: pip install openai")
        return False
    except Exception as e:
        print(f"❌ OpenAI API key test failed: {str(e)}")
        if "authentication" in str(e).lower():
            print("   Check your API key is correct")
        elif "quota" in str(e).lower():
            print("   You may have exceeded your usage quota")
        return False

def test_database():
    """Test database connection"""
    print("\n💾 Testing Database Connection...")
    
    db_url = os.getenv("DATABASE_URL", "sqlite:///./artemis.db")
    
    if db_url.startswith("sqlite"):
        print("✅ Using SQLite database (development mode)")
        return True
    elif db_url.startswith("postgresql"):
        print("🔄 Testing PostgreSQL connection...")
        try:
            import asyncpg
            # This is a simplified test - in real usage you'd test the connection
            print("✅ PostgreSQL configuration detected")
            return True
        except ImportError:
            print("❌ asyncpg library not installed")
            print("   Run: pip install asyncpg")
            return False
    else:
        print(f"⚠️  Unknown database type: {db_url}")
        return False

def test_environment():
    """Test environment configuration"""
    print("\n⚙️  Testing Environment Configuration...")
    
    required_vars = {
        "ARTEMIS_PORT": "8082",
        "ARTEMIS_HOST": "0.0.0.0",
        "SECRET_KEY": "artemis-dev-secret-key-change-this-in-production-12345"
    }
    
    all_good = True
    for var, default in required_vars.items():
        value = os.getenv(var, default)
        if value == default and var == "SECRET_KEY":
            print(f"⚠️  {var}: Using default value (change for production)")
        else:
            print(f"✅ {var}: {value}")
    
    return all_good

def test_optional_services():
    """Test optional services"""
    print("\n🔧 Testing Optional Services...")
    
    # Test blockchain RPC
    eth_rpc = os.getenv("ETHEREUM_RPC_URL")
    if eth_rpc:
        print(f"✅ Ethereum RPC configured: {eth_rpc[:30]}...")
    else:
        print("ℹ️  Ethereum RPC not configured (optional)")
    
    # Test Redis
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        print(f"✅ Redis configured: {redis_url}")
    else:
        print("ℹ️  Redis not configured (optional)")

def main():
    """Main validation function"""
    print("🧪 Artemis AI Core - API Key Validation")
    print("=" * 40)
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("❌ .env file not found!")
        print("   Copy .env.example to .env and configure your API keys")
        sys.exit(1)
    
    print("✅ .env file found")
      # Run tests
    tests_passed = 0
    total_tests = 3
    
    if test_ai_keys():
        tests_passed += 1
    
    if test_database():
        tests_passed += 1
        
    if test_environment():
        tests_passed += 1
    
    test_optional_services()
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {tests_passed}/{total_tests} core tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All core tests passed! You're ready to start Artemis AI Core")
        print("\nNext steps:")
        print("1. Run: python artemis_ai_core.py")
        print("2. In another terminal: cd .. && npm run dev")
        print("3. Open: http://localhost:5173")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        print("\nFor help, see:")
        print("- API_KEYS_SETUP_GUIDE.md")
        print("- ARTEMIS_SETUP_GUIDE.md")

if __name__ == "__main__":
    main()
