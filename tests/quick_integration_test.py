# 🔬 Integrated Research Platform - Quick Setup Test

import pandas as pd
import numpy as np
from datetime import datetime
import os

class QuickIntegrationTest:
    def __init__(self):
        print("🚀 Quick Integration Test for Professional Research Suite")
        print("=" * 60)
        self.test_results = {}
        
    def test_python_scientific_stack(self):
        """Test core Python scientific libraries"""
        print("\n📊 Testing Python Scientific Stack...")
        try:
            # Test pandas
            df = pd.DataFrame({'price': [100, 101, 99], 'volume': [1000, 1200, 800]})
            assert len(df) == 3
            
            # Test numpy
            arr = np.array([1, 2, 3, 4, 5])
            mean_val = np.mean(arr)
            assert mean_val == 3.0
            
            # Test basic stats
            correlation = np.corrcoef([1, 2, 3], [2, 4, 6])[0, 1]
            assert abs(correlation - 1.0) < 0.001
            
            print("✅ Pandas, NumPy, Statistics: Working perfectly")
            self.test_results['python_scientific'] = True
            return True
            
        except Exception as e:
            print(f"❌ Python Scientific Stack failed: {e}")
            self.test_results['python_scientific'] = False
            return False
    
    def test_matlab_engine(self):
        """Test MATLAB Engine for Python"""
        print("\n🧮 Testing MATLAB Engine...")
        try:
            import matlab.engine
            
            # Start MATLAB engine
            eng = matlab.engine.start_matlab()
            
            # Test basic calculation
            result = eng.sqrt(16.0)
            assert result == 4.0
            
            # Test matrix operations
            test_matrix = matlab.double([[1, 2], [3, 4]])
            det_result = eng.det(test_matrix)
            expected_det = -2.0
            assert abs(det_result - expected_det) < 0.001
            
            # Close engine
            eng.quit()
            
            print("✅ MATLAB Engine: Connected and working perfectly")
            self.test_results['matlab_engine'] = True
            return True
            
        except ImportError:
            print("⚠️ MATLAB Engine not installed. Run setup from MATLAB installation:")
            print("   cd [MATLAB_ROOT]\\extern\\engines\\python")
            print("   python setup.py install")
            self.test_results['matlab_engine'] = False
            return False
        except Exception as e:
            print(f"❌ MATLAB Engine test failed: {e}")
            self.test_results['matlab_engine'] = False
            return False
    
    def test_aws_boto3(self):
        """Test AWS Boto3 connection"""
        print("\n☁️ Testing AWS Boto3...")
        try:
            import boto3
            
            # Test session creation (doesn't require credentials)
            session = boto3.Session()
            
            # Test if credentials are configured
            try:
                sts = boto3.client('sts')
                identity = sts.get_caller_identity()
                print(f"✅ AWS: Connected as {identity.get('Arn', 'Unknown')}")
                self.test_results['aws_boto3'] = True
                return True
            except:
                print("⚠️ AWS credentials not configured. Run: aws configure")
                self.test_results['aws_boto3'] = False
                return False
                
        except ImportError:
            print("⚠️ AWS Boto3 not installed. Run: pip install boto3")
            self.test_results['aws_boto3'] = False
            return False
        except Exception as e:
            print(f"❌ AWS Boto3 test failed: {e}")
            self.test_results['aws_boto3'] = False
            return False
    
    def test_data_processing_capabilities(self):
        """Test data processing for arbitrage analysis"""
        print("\n📈 Testing Data Processing Capabilities...")
        try:
            # Create sample trading data
            dates = pd.date_range('2025-01-01', periods=100, freq='H')
            prices = 100 + np.cumsum(np.random.randn(100) * 0.01)
            volumes = np.random.randint(1000, 5000, 100)
            
            df = pd.DataFrame({
                'timestamp': dates,
                'price': prices,
                'volume': volumes
            })
            
            # Test statistical operations
            price_mean = df['price'].mean()
            price_std = df['price'].std()
            correlation = df['price'].corr(df['volume'])
            
            # Test moving averages
            df['ma_10'] = df['price'].rolling(window=10).mean()
            
            # Test arbitrage opportunity detection
            df['price_change'] = df['price'].pct_change()
            opportunities = df[abs(df['price_change']) > 0.02]
            
            print(f"✅ Processed {len(df)} data points")
            print(f"✅ Found {len(opportunities)} potential arbitrage opportunities")
            print(f"✅ Price statistics: mean={price_mean:.2f}, std={price_std:.2f}")
            
            self.test_results['data_processing'] = True
            return True
            
        except Exception as e:
            print(f"❌ Data processing test failed: {e}")
            self.test_results['data_processing'] = False
            return False
    
    def run_all_tests(self):
        """Run all integration tests"""
        print(f"\n🔬 Starting Comprehensive Integration Test")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all tests
        tests = [
            self.test_python_scientific_stack,
            self.test_matlab_engine,
            self.test_aws_boto3,
            self.test_data_processing_capabilities
        ]
        
        for test in tests:
            test()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 INTEGRATION TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(self.test_results.values())
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title():.<30} {status}")
        
        print(f"\nOverall Success Rate: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED - READY FOR ADVANCED RESEARCH!")
            print("🚀 You can now proceed with Phase 2 implementation")
        elif passed_tests >= total_tests * 0.75:
            print("\n✅ MOSTLY READY - Minor setup needed for failed components")
        else:
            print("\n⚠️ SETUP NEEDED - Please address failed components before proceeding")
        
        return self.test_results

if __name__ == "__main__":
    tester = QuickIntegrationTest()
    results = tester.run_all_tests()
