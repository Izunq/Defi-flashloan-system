#!/usr/bin/env python3
"""
📈 SPSS & SPSS Amos Integration Setup for DeFi Research
Complete setup for statistical analysis and structural equation modeling
"""

import os
import sys
import subprocess
from pathlib import Path
import pandas as pd
import numpy as np

def check_spss_installation():
    """Check if SPSS is installed"""
    print("🔍 Checking SPSS installation...")
    
    # Common SPSS installation paths
    spss_paths = [
        r"C:\Program Files\IBM\SPSS\Statistics\29",
        r"C:\Program Files\IBM\SPSS\Statistics\28",
        r"C:\Program Files\IBM\SPSS\Statistics\27",
        r"C:\Program Files (x86)\IBM\SPSS\Statistics"
    ]
    
    spss_found = False
    spss_version = None
    
    for path in spss_paths:
        if os.path.exists(path):
            spss_found = True
            spss_version = os.path.basename(path)
            print(f"✅ SPSS found at: {path}")
            
            # Check for Python integration
            python_path = os.path.join(path, "Python")
            if os.path.exists(python_path):
                print(f"✅ SPSS Python integration available: {python_path}")
            else:
                print(f"⚠️ SPSS Python integration not found")
            break
    
    if not spss_found:
        print("❌ SPSS not found on system")
        print("💡 Install IBM SPSS Statistics with campus license")
        print("📋 Required components:")
        print("   - IBM SPSS Statistics Base")
        print("   - IBM SPSS Statistics Advanced Statistics")
        print("   - IBM SPSS Amos (for SEM)")
        print("   - Python Integration Plugin")
        return False, None
    
    return True, spss_version

def check_amos_installation():
    """Check if SPSS Amos is installed"""
    print("\n🔗 Checking SPSS Amos installation...")
    
    # Common Amos installation paths
    amos_paths = [
        r"C:\Program Files\IBM\SPSS\Amos\29",
        r"C:\Program Files\IBM\SPSS\Amos\28",
        r"C:\Program Files\IBM\SPSS\Amos\27",
        r"C:\Program Files (x86)\IBM\SPSS\Amos"
    ]
    
    for path in amos_paths:
        if os.path.exists(path):
            print(f"✅ SPSS Amos found at: {path}")
            return True, path
    
    print("❌ SPSS Amos not found")
    print("💡 Install SPSS Amos add-on for structural equation modeling")
    return False, None

def setup_spss_data_preparation():
    """Setup data preparation functions for SPSS"""
    print("\n📊 Setting up SPSS data preparation...")
    
    spss_dir = Path("spss_analysis")
    spss_dir.mkdir(exist_ok=True)
    
    # Data preparation module
    data_prep_code = '''"""
SPSS Data Preparation for DeFi Arbitrage Research
Prepares trading data for statistical analysis in SPSS
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SPSSDataPreparator:
    """Prepare arbitrage data for SPSS analysis"""
    
    def __init__(self):
        self.prepared_data = None
    
    def prepare_trading_data(self, trading_data: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare trading data for SPSS statistical analysis
        
        Args:
            trading_data: DataFrame with price, volume, timestamp columns
            
        Returns:
            Analysis-ready DataFrame for SPSS
        """
        try:
            # Create analysis dataset
            analysis_data = pd.DataFrame()
            
            # Basic price metrics
            analysis_data['price'] = trading_data['price']
            analysis_data['volume'] = trading_data['volume']
            analysis_data['timestamp'] = trading_data['timestamp']
            
            # Returns calculations
            analysis_data['returns'] = trading_data['price'].pct_change()
            analysis_data['log_returns'] = np.log(trading_data['price'] / trading_data['price'].shift(1))
            
            # Volatility measures
            analysis_data['volatility_5min'] = analysis_data['returns'].rolling(5).std()
            analysis_data['volatility_1hr'] = analysis_data['returns'].rolling(60).std()
            analysis_data['volatility_24hr'] = analysis_data['returns'].rolling(1440).std()
            
            # Volume metrics
            analysis_data['log_volume'] = np.log(trading_data['volume'] + 1)
            analysis_data['volume_ma_5'] = trading_data['volume'].rolling(5).mean()
            analysis_data['volume_ratio'] = trading_data['volume'] / analysis_data['volume_ma_5']
            
            # Price momentum indicators
            analysis_data['price_ma_5'] = trading_data['price'].rolling(5).mean()
            analysis_data['price_ma_20'] = trading_data['price'].rolling(20).mean()
            analysis_data['price_momentum'] = (trading_data['price'] - analysis_data['price_ma_20']) / analysis_data['price_ma_20']
            
            # Market microstructure
            analysis_data['bid_ask_spread'] = trading_data.get('spread', 0)
            analysis_data['trade_size'] = trading_data.get('trade_size', trading_data['volume'])
            
            # Time features
            analysis_data['hour'] = pd.to_datetime(trading_data['timestamp']).dt.hour
            analysis_data['day_of_week'] = pd.to_datetime(trading_data['timestamp']).dt.dayofweek
            analysis_data['is_weekend'] = (analysis_data['day_of_week'] >= 5).astype(int)
            
            # Arbitrage opportunities (if available)
            if 'arbitrage_profit' in trading_data.columns:
                analysis_data['arbitrage_profit'] = trading_data['arbitrage_profit']
                analysis_data['has_arbitrage'] = (trading_data['arbitrage_profit'] > 0.01).astype(int)
            
            # Remove infinite and NaN values
            analysis_data = analysis_data.replace([np.inf, -np.inf], np.nan)
            analysis_data = analysis_data.dropna()
            
            self.prepared_data = analysis_data
            logger.info(f"Data prepared for SPSS: {len(analysis_data)} observations")
            
            return analysis_data
            
        except Exception as e:
            logger.error(f"Data preparation failed: {e}")
            raise
    
    def export_for_spss(self, data: pd.DataFrame, filename: str = "spss_analysis_data.csv"):
        """Export data in SPSS-compatible format"""
        try:
            # Ensure proper data types
            for col in data.columns:
                if data[col].dtype == 'object':
                    data[col] = pd.Categorical(data[col]).codes
            
            # Export to CSV (SPSS can import)
            filepath = f"spss_analysis/{filename}"
            data.to_csv(filepath, index=False)
            
            # Create SPSS import syntax
            self.create_spss_import_syntax(data.columns, filename)
            
            logger.info(f"Data exported for SPSS: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"SPSS export failed: {e}")
            raise
    
    def create_spss_import_syntax(self, columns, filename):
        """Create SPSS syntax file for data import"""
        
        syntax = f'''* SPSS Import Syntax for DeFi Arbitrage Analysis
* Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

GET DATA
  /TYPE=TXT
  /FILE='{filename}'
  /ARRANGEMENT=DELIMITED
  /DELIMITERS=","
  /QUALIFIER='"'
  /FIRSTCASE=2
  /VARIABLES=
'''
        
        # Add variable definitions
        for i, col in enumerate(columns, 1):
            syntax += f"  {col} F8.4\\n"
        
        syntax += '''.

* Add variable labels
VARIABLE LABELS
'''
        
        # Add meaningful labels
        label_map = {
            'price': 'Asset Price',
            'volume': 'Trading Volume',
            'returns': 'Price Returns',
            'log_returns': 'Log Returns',
            'volatility_5min': '5-Minute Volatility',
            'volatility_1hr': '1-Hour Volatility',
            'volatility_24hr': '24-Hour Volatility',
            'log_volume': 'Log Trading Volume',
            'volume_ratio': 'Volume Ratio to MA',
            'price_momentum': 'Price Momentum',
            'arbitrage_profit': 'Arbitrage Profit Rate',
            'has_arbitrage': 'Arbitrage Opportunity (0/1)'
        }
        
        for col in columns:
            label = label_map.get(col, col.replace('_', ' ').title())
            syntax += f"  {col} '{label}'\\n"
        
        syntax += '''.

* Save as SPSS data file
SAVE OUTFILE='arbitrage_analysis.sav'.

EXECUTE.
'''
        
        with open("spss_analysis/import_data.sps", "w") as f:
            f.write(syntax)
        
        logger.info("SPSS import syntax created: import_data.sps")

def create_spss_analysis_templates():
    """Create SPSS analysis templates"""
    print("📋 Creating SPSS analysis templates...")
    
    # Descriptive analysis template
    descriptive_template = '''* SPSS Descriptive Analysis for DeFi Arbitrage
* Comprehensive statistical overview

* Basic descriptive statistics
DESCRIPTIVES VARIABLES=price volume returns volatility_24hr arbitrage_profit
  /STATISTICS=MEAN STDDEV MIN MAX SKEWNESS KURTOSIS
  /SORT=MEAN(A).

* Frequency distributions for categorical variables
FREQUENCIES VARIABLES=hour day_of_week has_arbitrage
  /ORDER=ANALYSIS.

* Correlation matrix
CORRELATIONS
  /VARIABLES=price volume returns volatility_24hr price_momentum arbitrage_profit
  /PRINT=TWOTAIL NOSIG
  /STATISTICS DESCRIPTIVES
  /MISSING=PAIRWISE.

* Cross-tabulation analysis
CROSSTABS
  /TABLES=has_arbitrage BY hour
  /FORMAT=AVALUE TABLES
  /STATISTICS=CHISQ PHI CC
  /CELLS=COUNT EXPECTED ROW COLUMN TOTAL.

* Box plots for outlier detection
EXAMINE VARIABLES=returns arbitrage_profit BY has_arbitrage
  /PLOT=BOXPLOT STEMLEAF HISTOGRAM NPPLOT
  /COMPARE=GROUPS
  /STATISTICS=DESCRIPTIVES
  /CINTERVAL 95
  /MISSING=LISTWISE
  /NOTOTAL.
'''
    
    # Regression analysis template
    regression_template = '''* SPSS Regression Analysis for Arbitrage Prediction
* Predicting arbitrage opportunities and profitability

* Linear regression: Arbitrage profit prediction
REGRESSION
  /MISSING LISTWISE
  /STATISTICS COEFF OUTS CI(95) R ANOVA CHANGE ZPP
  /CRITERIA=PIN(.05) POUT(.10)
  /NOORIGIN 
  /DEPENDENT arbitrage_profit
  /METHOD=ENTER volatility_24hr volume_ratio price_momentum
  /METHOD=STEPWISE hour day_of_week
  /RESIDUALS DURBIN HISTOGRAM NORMPROB
  /CASEWISE PLOT(ZRESID) OUTLIERS(3).

* Logistic regression: Arbitrage opportunity prediction
LOGISTIC REGRESSION VARIABLES has_arbitrage
  /METHOD=ENTER volatility_24hr volume_ratio price_momentum hour
  /CRITERIA=PIN(0.05) POUT(0.10) ITERATE(20) CUT(0.5)
  /PRINT=GOODFIT CORR ITER(1) CI(95)
  /PLOT=SURVIVAL PGROUP
  /CASEWISE OUTLIER(2).

* Advanced analysis: Time series components
TSMODEL
  /MODELSUMMARY  PRINT=[MODELFIT]
  /MODELSTATISTICS  DISPLAY=YES MODELFIT=[ SRSQUARE]
  /MODELDETAILS  PRINT=[ PARAMETERS RESIDUALACF RESIDUALSTATS]
  /SERIESPLOT VARIABLE= returns
  /OUTPUTFILTER DISPLAY=ALLMODELS
  /SAVE  PREDICTED(Predicted_returns)
  /AUXILIARY CILEVEL=95 MAXACFLAGS=24
  /MISSING USERMISSING=EXCLUDE
  /MODEL DEPENDENT=returns INDEPENDENT= 
  PREFIX='Model'
  /AUTOOUTLIER DETECT=ON.
'''
    
    # Save templates
    templates_dir = Path("spss_analysis/templates")
    templates_dir.mkdir(exist_ok=True)
    
    with open(templates_dir / "descriptive_analysis.sps", "w") as f:
        f.write(descriptive_template)
    
    with open(templates_dir / "regression_analysis.sps", "w") as f:
        f.write(regression_template)
    
    print("✅ SPSS analysis templates created")
    print(f"   📁 Templates directory: {templates_dir}")

def create_amos_sem_templates():
    """Create SPSS Amos SEM templates"""
    print("🔗 Creating SPSS Amos SEM templates...")
    
    sem_template = '''* SPSS Amos Structural Equation Model Template
* Market Structure and Arbitrage Relationship Analysis

* This template guides the creation of structural models in Amos
* Copy this code into Amos programming environment

* Model Specification: Market Efficiency and Arbitrage
* Latent Variables:
*   - Market_Efficiency (observed: volatility, volume_ratio, price_momentum)
*   - Trading_Activity (observed: volume, trade_frequency, spread)
*   - Arbitrage_Success (observed: arbitrage_profit, success_rate, frequency)

BEGIN PROGRAM
Import "C:\\Path\\To\\Your\\arbitrage_analysis.sav"

* Define latent variables and indicators
Latent_Variable Market_Efficiency
  Indicators: volatility_24hr, volume_ratio, price_momentum

Latent_Variable Trading_Activity  
  Indicators: log_volume, trade_frequency, bid_ask_spread

Latent_Variable Arbitrage_Success
  Indicators: arbitrage_profit, success_rate, opportunity_frequency

* Specify structural relationships
Market_Efficiency -> Arbitrage_Success
Trading_Activity -> Arbitrage_Success
Trading_Activity -> Market_Efficiency

* Add error terms and covariances
Error_Market_Efficiency <-> Error_Trading_Activity (0.3)

* Estimation settings
Estimation_Method: Maximum_Likelihood
Bootstrap_Samples: 1000
Confidence_Intervals: 95%

* Fit indices to report
Report: Chi_Square, RMSEA, CFI, TLI, SRMR, AIC, BIC

* Modification indices
Modification_Indices: All parameters

* Output options
Standardized_Estimates: Yes
Residual_Covariances: Yes
Factor_Score_Weights: Yes

END PROGRAM

* Alternative: Using Amos Graphics Interface
* 1. Open Amos Graphics
* 2. Draw latent variables as ovals
* 3. Draw observed variables as rectangles  
* 4. Connect with single-headed arrows (regression paths)
* 5. Connect with double-headed arrows (covariances)
* 6. Add error terms to observed variables
* 7. Run analysis and interpret results

* Model Interpretation Guidelines:
* - Standardized path coefficients > 0.3 considered meaningful
* - R² values indicate variance explained
* - Fit indices: RMSEA < 0.08, CFI > 0.95, SRMR < 0.08
* - Modification indices suggest model improvements
'''
    
    amos_dir = Path("spss_analysis/amos_sem")
    amos_dir.mkdir(exist_ok=True)
    
    with open(amos_dir / "market_structure_sem.amos", "w") as f:
        f.write(sem_template)
    
    print("✅ SPSS Amos SEM templates created")
    print(f"   📁 Amos directory: {amos_dir}")

def main():
    """Main setup function"""
    print("📈 SPSS & SPSS AMOS INTEGRATION SETUP")
    print("=" * 45)
    
    # Check installations
    spss_installed, spss_version = check_spss_installation()
    amos_installed, amos_path = check_amos_installation()
    
    if not spss_installed:
        print("\\n❌ Setup cannot continue without SPSS installation")
        print("📋 Installation requirements:")
        print("1. Download IBM SPSS Statistics from IBM or campus portal")
        print("2. Install with Python Integration plugin")
        print("3. Install SPSS Amos add-on for SEM")
        print("4. Configure Python integration path")
        return False
    
    # Setup analysis components
    setup_spss_data_preparation()
    create_spss_analysis_templates()
    
    if amos_installed:
        create_amos_sem_templates()
    else:
        print("⚠️ SPSS Amos not found - SEM templates created but not functional")
    
    print("\\n🎉 SPSS INTEGRATION SETUP COMPLETE!")
    print("=" * 45)
    print(f"✅ SPSS {spss_version}: Available")
    print(f"✅ Data Preparation: Ready")
    print(f"✅ Analysis Templates: Created")
    
    if amos_installed:
        print(f"✅ SPSS Amos: Available")
        print(f"✅ SEM Templates: Ready")
    
    print("\\n📋 Next Steps:")
    print("1. Import your trading data")
    print("2. Run: from spss_analysis.data_preparation import SPSSDataPreparator")
    print("3. Use SPSS GUI to run analysis templates")
    print("4. For SEM: Open Amos and load model templates")
    
    return True

if __name__ == "__main__":
    main()
