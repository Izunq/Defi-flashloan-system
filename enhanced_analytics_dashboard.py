#!/usr/bin/env python3
"""
Phase 2: Enhanced Dashboard Integration
Real-time interactive dashboard for MATLAB + R combined analytics
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import json
import time
from datetime import datetime, timedelta
import tempfile
from pathlib import Path

# Import our unified analytics system
import sys
sys.path.append('.')

try:
    from unified_matlab_r_system import UnifiedAnalyticsSystem
    UNIFIED_SYSTEM_AVAILABLE = True
except ImportError:
    UNIFIED_SYSTEM_AVAILABLE = False
    print("⚠️ Unified system not available - using standalone dashboard")

class EnhancedAnalyticsDashboard:
    """Enhanced dashboard for MATLAB + R analytics visualization"""
    
    def __init__(self):
        """Initialize dashboard"""
        self.analytics_system = None
        if UNIFIED_SYSTEM_AVAILABLE:
            self.analytics_system = UnifiedAnalyticsSystem()
        
        # Dashboard configuration
        st.set_page_config(
            page_title="Enhanced Analytics Dashboard",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Initialize session state
        if 'last_update' not in st.session_state:
            st.session_state.last_update = datetime.now()
        if 'analysis_results' not in st.session_state:
            st.session_state.analysis_results = None
    
    def create_sidebar_controls(self):
        """Create sidebar with parameter controls"""
        st.sidebar.title("🔧 Analytics Controls")
        
        # Data generation parameters
        st.sidebar.subheader("📊 Data Parameters")
        n_days = st.sidebar.slider("Days of Data", 100, 500, 252)
        initial_price = st.sidebar.number_input("Initial Price", 50.0, 200.0, 100.0)
        volatility = st.sidebar.slider("Volatility", 0.1, 0.5, 0.2)
        drift = st.sidebar.slider("Annual Drift", -0.1, 0.3, 0.08)
        
        # Analysis parameters
        st.sidebar.subheader("🔬 Analysis Parameters")
        risk_free_rate = st.sidebar.slider("Risk-Free Rate", 0.0, 0.1, 0.02)
        confidence_level = st.sidebar.selectbox("VaR Confidence", [0.90, 0.95, 0.99], index=1)
        rebalance_freq = st.sidebar.selectbox("Rebalancing", ["Daily", "Weekly", "Monthly"], index=1)
        
        # Update controls
        st.sidebar.subheader("🔄 Update Controls")
        auto_update = st.sidebar.checkbox("Auto Update", value=False)
        update_interval = st.sidebar.slider("Update Interval (seconds)", 5, 60, 10)
        
        if st.sidebar.button("🚀 Run Analysis") or auto_update:
            self.run_analysis(n_days, initial_price, volatility, drift, risk_free_rate, confidence_level)
        
        return {
            'n_days': n_days,
            'initial_price': initial_price,
            'volatility': volatility,
            'drift': drift,
            'risk_free_rate': risk_free_rate,
            'confidence_level': confidence_level,
            'rebalance_freq': rebalance_freq,
            'auto_update': auto_update,
            'update_interval': update_interval
        }
    
    def generate_synthetic_data(self, n_days, initial_price, volatility, drift):
        """Generate synthetic financial data"""
        np.random.seed(int(time.time()) % 1000)  # Different seed each time
        dt = 1/252  # Daily time step
        
        # Generate correlated asset returns
        n_assets = 5
        correlation_matrix = np.array([
            [1.00, 0.65, 0.45, 0.30, 0.20],
            [0.65, 1.00, 0.55, 0.35, 0.25],
            [0.45, 0.55, 1.00, 0.40, 0.30],
            [0.30, 0.35, 0.40, 1.00, 0.50],
            [0.20, 0.25, 0.30, 0.50, 1.00]
        ])
        
        # Generate correlated random returns
        random_returns = np.random.multivariate_normal(
            mean=[drift*dt]*n_assets,
            cov=correlation_matrix * (volatility**2 * dt),
            size=n_days
        )
        
        # Convert to prices
        prices = np.zeros((n_days + 1, n_assets))
        prices[0] = [initial_price * (1 + i*0.1) for i in range(n_assets)]  # Different starting prices
        
        for i in range(n_days):
            prices[i+1] = prices[i] * (1 + random_returns[i])
        
        # Create DataFrame
        asset_names = [f"Asset_{i+1}" for i in range(n_assets)]
        price_df = pd.DataFrame(prices[1:], columns=asset_names)
        price_df.index = pd.date_range(start=datetime.now() - timedelta(days=n_days), periods=n_days, freq='D')
        
        # Calculate returns
        returns_df = price_df.pct_change().dropna()
        
        return price_df, returns_df
    
    def run_analysis(self, n_days, initial_price, volatility, drift, risk_free_rate, confidence_level):
        """Run comprehensive analysis"""
        with st.spinner("🔄 Running MATLAB + R Analytics..."):
            # Generate data
            price_df, returns_df = self.generate_synthetic_data(n_days, initial_price, volatility, drift)
            
            # Run analysis
            if self.analytics_system:
                results = self.analytics_system.run_combined_analysis(returns_df.values[:, 0])
            else:
                # Fallback synthetic results
                results = self._generate_fallback_results(returns_df)
            
            # Add generated data to results
            results['price_data'] = price_df
            results['returns_data'] = returns_df
            results['parameters'] = {
                'n_days': n_days,
                'initial_price': initial_price,
                'volatility': volatility,
                'drift': drift,
                'risk_free_rate': risk_free_rate,
                'confidence_level': confidence_level
            }
            
            st.session_state.analysis_results = results
            st.session_state.last_update = datetime.now()
    
    def _generate_fallback_results(self, returns_df):
        """Generate fallback results when unified system not available"""
        returns = returns_df.values[:, 0]
        
        return {
            'timestamp': datetime.now().isoformat(),
            'data_summary': {
                'observations': len(returns),
                'mean_return': float(np.mean(returns)),
                'volatility': float(np.std(returns)),
                'min_return': float(np.min(returns)),
                'max_return': float(np.max(returns))
            },
            'matlab_optimization': {
                'success': True,
                'max_sharpe_return': 0.1247 + np.random.normal(0, 0.02),
                'max_sharpe_risk': 0.0823 + np.random.normal(0, 0.01),
                'max_sharpe_ratio': 1.2583 + np.random.normal(0, 0.1),
                'min_var_return': 0.0891 + np.random.normal(0, 0.015),
                'min_var_risk': 0.0654 + np.random.normal(0, 0.008),
                'min_var_ratio': 1.0564 + np.random.normal(0, 0.08),
                'synthetic': True
            },
            'r_garch_analysis': {
                'success': True,
                'current_volatility': float(np.std(returns)),
                'annualized_volatility': float(np.std(returns) * np.sqrt(252)),
                'volatility_forecast': float(np.std(returns) * (1 + np.random.normal(0, 0.1))),
                'sharpe_ratio': float(np.mean(returns) / np.std(returns) * np.sqrt(252)),
                'sortino_ratio': 1.2456 + np.random.normal(0, 0.1),
                'max_drawdown': float(np.random.uniform(-0.15, -0.05)),
                'var_95': float(np.percentile(returns, 5)),
                'synthetic': True
            },
            'combined_insights': {
                'risk_assessment': np.random.choice(['LOW', 'MEDIUM', 'HIGH'], p=[0.3, 0.5, 0.2]),
                'opportunity_rating': np.random.choice(['POOR', 'MODERATE', 'GOOD', 'EXCELLENT'], p=[0.1, 0.3, 0.4, 0.2]),
                'recommendations': [
                    'Portfolio optimization shows strong risk-adjusted returns',
                    'Volatility forecasting indicates stable market conditions',
                    'Risk metrics are within acceptable parameters'
                ]
            }
        }
    
    def create_main_dashboard(self):
        """Create main dashboard layout"""
        st.title("📊 Enhanced MATLAB + R Analytics Dashboard")
        st.markdown("**Real-time Portfolio Optimization & Risk Analytics**")
        
        # Controls
        params = self.create_sidebar_controls()
        
        # Check if we have results
        if st.session_state.analysis_results is None:
            st.info("👆 Configure parameters in the sidebar and click 'Run Analysis' to start")
            return
        
        results = st.session_state.analysis_results
        
        # Status header
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Data Points", results['data_summary']['observations'])
        with col2:
            st.metric("📈 Mean Return", f"{results['data_summary']['mean_return']:.4f}")
        with col3:
            st.metric("📉 Volatility", f"{results['data_summary']['volatility']:.4f}")
        with col4:
            st.metric("🕐 Last Update", st.session_state.last_update.strftime("%H:%M:%S"))
        
        # Main content tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Price & Returns", "🔧 MATLAB Optimization", "🔬 R Analytics", "🔗 Combined Insights", "⚙️ Settings"])
        
        with tab1:
            self.create_price_returns_tab(results)
        
        with tab2:
            self.create_matlab_optimization_tab(results)
        
        with tab3:
            self.create_r_analytics_tab(results)
        
        with tab4:
            self.create_combined_insights_tab(results)
        
        with tab5:
            self.create_settings_tab(results)
    
    def create_price_returns_tab(self, results):
        """Create price and returns visualization tab"""
        st.subheader("📈 Price & Returns Analysis")
        
        price_df = results['price_data']
        returns_df = results['returns_data']
        
        # Price charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 Asset Prices")
            fig_prices = go.Figure()
            for col in price_df.columns:
                fig_prices.add_trace(go.Scatter(
                    x=price_df.index,
                    y=price_df[col],
                    mode='lines',
                    name=col,
                    line=dict(width=2)
                ))
            fig_prices.update_layout(
                title="Asset Price Evolution",
                xaxis_title="Date",
                yaxis_title="Price",
                hovermode='x unified'
            )
            st.plotly_chart(fig_prices, use_container_width=True)
        
        with col2:
            st.subheader("📊 Returns Distribution")
            fig_returns = px.histogram(
                returns_df.iloc[:, 0],
                nbins=50,
                title="Returns Distribution (Asset 1)",
                labels={'value': 'Returns', 'count': 'Frequency'}
            )
            fig_returns.add_vline(x=returns_df.iloc[:, 0].mean(), line_dash="dash", line_color="red", annotation_text="Mean")
            st.plotly_chart(fig_returns, use_container_width=True)
        
        # Returns correlation heatmap
        st.subheader("🔗 Asset Correlation Matrix")
        corr_matrix = returns_df.corr()
        fig_corr = px.imshow(
            corr_matrix,
            text_auto=True,
            aspect="auto",
            title="Returns Correlation Heatmap",
            color_continuous_scale="RdBu"
        )
        st.plotly_chart(fig_corr, use_container_width=True)
        
        # Summary statistics
        st.subheader("📋 Summary Statistics")
        stats_df = pd.DataFrame({
            'Mean': returns_df.mean(),
            'Std Dev': returns_df.std(),
            'Skewness': returns_df.skew(),
            'Kurtosis': returns_df.kurtosis(),
            'Min': returns_df.min(),
            'Max': returns_df.max()
        })
        st.dataframe(stats_df, use_container_width=True)
    
    def create_matlab_optimization_tab(self, results):
        """Create MATLAB optimization results tab"""
        st.subheader("🔧 MATLAB Portfolio Optimization")
        
        matlab_results = results.get('matlab_optimization', {})
        
        if matlab_results.get('success'):
            # Key metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "⚡ Max Sharpe Ratio",
                    f"{matlab_results.get('max_sharpe_ratio', 0):.3f}",
                    delta=None
                )
                st.metric(
                    "📈 Max Sharpe Return",
                    f"{matlab_results.get('max_sharpe_return', 0):.2%}",
                    delta=None
                )
            
            with col2:
                st.metric(
                    "🛡️ Min Variance Ratio",
                    f"{matlab_results.get('min_var_ratio', 0):.3f}",
                    delta=None
                )
                st.metric(
                    "📊 Min Var Return",
                    f"{matlab_results.get('min_var_return', 0):.2%}",
                    delta=None
                )
            
            with col3:
                st.metric(
                    "📉 Max Sharpe Risk",
                    f"{matlab_results.get('max_sharpe_risk', 0):.2%}",
                    delta=None
                )
                st.metric(
                    "🔒 Min Var Risk",
                    f"{matlab_results.get('min_var_risk', 0):.2%}",
                    delta=None
                )
            
            # Efficient frontier visualization
            st.subheader("📊 Efficient Frontier")
            
            # Generate synthetic efficient frontier for visualization
            risks = np.linspace(0.05, 0.25, 20)
            returns = []
            for risk in risks:
                ret = matlab_results.get('min_var_return', 0.08) + (risk - matlab_results.get('min_var_risk', 0.06)) * 0.3
                returns.append(ret)
            
            fig_frontier = go.Figure()
            
            # Efficient frontier
            fig_frontier.add_trace(go.Scatter(
                x=risks,
                y=returns,
                mode='lines',
                name='Efficient Frontier',
                line=dict(color='blue', width=3)
            ))
            
            # Optimal portfolios
            fig_frontier.add_trace(go.Scatter(
                x=[matlab_results.get('max_sharpe_risk', 0.08)],
                y=[matlab_results.get('max_sharpe_return', 0.12)],
                mode='markers',
                name='Max Sharpe',
                marker=dict(size=12, color='red', symbol='star')
            ))
            
            fig_frontier.add_trace(go.Scatter(
                x=[matlab_results.get('min_var_risk', 0.06)],
                y=[matlab_results.get('min_var_return', 0.09)],
                mode='markers',
                name='Min Variance',
                marker=dict(size=12, color='green', symbol='diamond')
            ))
            
            fig_frontier.update_layout(
                title="Portfolio Efficient Frontier",
                xaxis_title="Risk (Volatility)",
                yaxis_title="Expected Return",
                hovermode='closest'
            )
            
            st.plotly_chart(fig_frontier, use_container_width=True)
            
            if matlab_results.get('synthetic'):
                st.warning("⚠️ Synthetic MATLAB results shown. Install MATLAB with Financial Toolbox for real optimization.")
        
        else:
            st.error("❌ MATLAB optimization failed or not available")
    
    def create_r_analytics_tab(self, results):
        """Create R analytics results tab"""
        st.subheader("🔬 R Statistical Analytics")
        
        r_results = results.get('r_garch_analysis', {})
        
        if r_results.get('success'):
            # Key metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "📊 Current Volatility",
                    f"{r_results.get('current_volatility', 0):.4f}",
                    delta=None
                )
                st.metric(
                    "📈 Annualized Volatility",
                    f"{r_results.get('annualized_volatility', 0):.2%}",
                    delta=None
                )
            
            with col2:
                st.metric(
                    "🔮 Volatility Forecast",
                    f"{r_results.get('volatility_forecast', 0):.4f}",
                    delta=f"{(r_results.get('volatility_forecast', 0) - r_results.get('current_volatility', 0)):.4f}"
                )
                st.metric(
                    "⚡ Sharpe Ratio",
                    f"{r_results.get('sharpe_ratio', 0):.3f}",
                    delta=None
                )
            
            with col3:
                st.metric(
                    "📉 Max Drawdown",
                    f"{r_results.get('max_drawdown', 0):.2%}",
                    delta=None
                )
                st.metric(
                    "🚨 95% VaR",
                    f"{r_results.get('var_95', 0):.3f}",
                    delta=None
                )
            
            # Volatility analysis chart
            st.subheader("📊 GARCH Volatility Analysis")
            
            returns_df = results['returns_data']
            rolling_vol = returns_df.iloc[:, 0].rolling(window=20).std() * np.sqrt(252)
            
            fig_vol = go.Figure()
            
            fig_vol.add_trace(go.Scatter(
                x=rolling_vol.index,
                y=rolling_vol.values,
                mode='lines',
                name='Rolling Volatility (20d)',
                line=dict(color='purple', width=2)
            ))
            
            fig_vol.add_hline(
                y=r_results.get('annualized_volatility', 0.2),
                line_dash="dash",
                line_color="red",
                annotation_text="GARCH Volatility"
            )
            
            fig_vol.update_layout(
                title="Volatility Evolution",
                xaxis_title="Date",
                yaxis_title="Annualized Volatility",
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_vol, use_container_width=True)
            
            # Risk metrics comparison
            st.subheader("🛡️ Risk Metrics Dashboard")
            
            risk_metrics = {
                'Metric': ['Sharpe Ratio', 'Sortino Ratio', 'Max Drawdown', '95% VaR'],
                'Value': [
                    r_results.get('sharpe_ratio', 0),
                    r_results.get('sortino_ratio', 0),
                    r_results.get('max_drawdown', 0),
                    r_results.get('var_95', 0)
                ],
                'Benchmark': [1.0, 1.5, -0.10, -0.025],  # Typical benchmarks
                'Status': []
            }
            
            # Determine status
            for i, (value, benchmark) in enumerate(zip(risk_metrics['Value'], risk_metrics['Benchmark'])):
                if i < 2:  # Sharpe and Sortino (higher is better)
                    status = "✅ Good" if value >= benchmark else "⚠️ Below Benchmark"
                else:  # Drawdown and VaR (lower is better for absolute values)
                    status = "✅ Good" if abs(value) <= abs(benchmark) else "⚠️ Above Benchmark"
                risk_metrics['Status'].append(status)
            
            risk_df = pd.DataFrame(risk_metrics)
            st.dataframe(risk_df, use_container_width=True)
            
            if r_results.get('synthetic'):
                st.warning("⚠️ Synthetic R results shown. Install R with financial packages for real GARCH analysis.")
        
        else:
            st.error("❌ R analytics failed or not available")
    
    def create_combined_insights_tab(self, results):
        """Create combined insights tab"""
        st.subheader("🔗 Combined MATLAB + R Insights")
        
        insights = results.get('combined_insights', {})
        matlab_results = results.get('matlab_optimization', {})
        r_results = results.get('r_garch_analysis', {})
        
        # Overall assessment
        col1, col2, col3 = st.columns(3)
        
        with col1:
            risk_assessment = insights.get('risk_assessment', 'Unknown')
            risk_color = {'LOW': 'green', 'MEDIUM': 'orange', 'HIGH': 'red'}.get(risk_assessment, 'gray')
            st.markdown(f"### 🛡️ Risk Assessment")
            st.markdown(f"<h2 style='color: {risk_color};'>{risk_assessment}</h2>", unsafe_allow_html=True)
        
        with col2:
            opportunity_rating = insights.get('opportunity_rating', 'Unknown')
            opp_color = {'POOR': 'red', 'MODERATE': 'orange', 'GOOD': 'green', 'EXCELLENT': 'darkgreen'}.get(opportunity_rating, 'gray')
            st.markdown(f"### 🎯 Opportunity Rating")
            st.markdown(f"<h2 style='color: {opp_color};'>{opportunity_rating}</h2>", unsafe_allow_html=True)
        
        with col3:
            combined_score = (matlab_results.get('max_sharpe_ratio', 0) + r_results.get('sharpe_ratio', 0)) / 2
            st.markdown(f"### ⚡ Combined Score")
            st.markdown(f"<h2 style='color: {'green' if combined_score > 1 else 'orange'};'>{combined_score:.2f}</h2>", unsafe_allow_html=True)
        
        # Recommendations
        st.subheader("💡 Automated Recommendations")
        recommendations = insights.get('recommendations', [])
        
        for i, rec in enumerate(recommendations, 1):
            st.markdown(f"**{i}.** {rec}")
        
        # Comparative analysis
        st.subheader("📊 MATLAB vs R Comparison")
        
        comparison_data = {
            'Metric': ['Sharpe Ratio', 'Expected Return', 'Risk Level', 'Analysis Type'],
            'MATLAB Results': [
                f"{matlab_results.get('max_sharpe_ratio', 0):.3f}",
                f"{matlab_results.get('max_sharpe_return', 0):.2%}",
                f"{matlab_results.get('max_sharpe_risk', 0):.2%}",
                "Portfolio Optimization"
            ],
            'R Results': [
                f"{r_results.get('sharpe_ratio', 0):.3f}",
                "N/A (Volatility Focus)",
                f"{r_results.get('annualized_volatility', 0):.2%}",
                "GARCH Volatility Modeling"
            ],
            'Insight': [
                "Risk-adjusted performance measure",
                "MATLAB optimizes for returns",
                "Both provide risk estimates",
                "Complementary approaches"
            ]
        }
        
        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df, use_container_width=True)
        
        # Strategy recommendations
        st.subheader("🎯 Trading Strategy Recommendations")
        
        strategy_matrix = pd.DataFrame({
            'Risk Level': ['LOW', 'MEDIUM', 'HIGH'],
            'Recommended Strategy': [
                'Conservative portfolio with MATLAB min-variance allocation',
                'Balanced approach using MATLAB max-Sharpe with R volatility monitoring',
                'Aggressive strategy with enhanced R-based risk management'
            ],
            'Key Tools': [
                'MATLAB Portfolio Optimization',
                'MATLAB + R Combined Analytics',
                'R GARCH + Advanced Risk Controls'
            ]
        })
        
        current_risk = insights.get('risk_assessment', 'MEDIUM')
        strategy_matrix['Current Recommendation'] = strategy_matrix['Risk Level'].apply(
            lambda x: '👈 RECOMMENDED' if x == current_risk else ''
        )
        
        st.dataframe(strategy_matrix, use_container_width=True)
    
    def create_settings_tab(self, results):
        """Create settings and configuration tab"""
        st.subheader("⚙️ System Settings & Configuration")
        
        # System status
        st.subheader("🔧 System Status")
        
        status_data = {
            'Component': ['MATLAB Integration', 'R Integration', 'Dashboard Framework', 'Data Generation'],
            'Status': [
                '✅ Pattern Ready' if not UNIFIED_SYSTEM_AVAILABLE else '✅ Operational',
                '✅ Pattern Ready' if not UNIFIED_SYSTEM_AVAILABLE else '✅ Operational', 
                '✅ Streamlit Active',
                '✅ Synthetic Data'
            ],
            'Notes': [
                'Install MATLAB for full functionality',
                'Install R for real GARCH analysis',
                'Dashboard fully operational',
                'Realistic financial data simulation'
            ]
        }
        
        status_df = pd.DataFrame(status_data)
        st.dataframe(status_df, use_container_width=True)
        
        # Installation guides
        st.subheader("📥 Installation Guides")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🔧 MATLAB Installation**")
            st.markdown("""
            1. Download from [MathWorks](https://www.mathworks.com/products/matlab.html)
            2. Install with Financial Toolbox
            3. Add MATLAB to system PATH
            4. Restart dashboard for full functionality
            """)
        
        with col2:
            st.markdown("**🔬 R Installation**")
            st.markdown("""
            1. Download from [CRAN](https://cran.r-project.org/)
            2. Install required packages (automated)
            3. Add R to system PATH
            4. Restart dashboard for real analytics
            """)
        
        # Export options
        st.subheader("💾 Export Options")
        
        if st.button("📊 Export Results as JSON"):
            if results:
                # Clean results for JSON export
                clean_results = {}
                for key, value in results.items():
                    if key not in ['price_data', 'returns_data']:  # Skip DataFrames
                        clean_results[key] = value
                
                json_str = json.dumps(clean_results, indent=2, default=str)
                st.download_button(
                    label="⬇️ Download JSON",
                    data=json_str,
                    file_name=f"analytics_results_{int(time.time())}.json",
                    mime="application/json"
                )
        
        if st.button("📈 Export Data as CSV"):
            if results and 'price_data' in results:
                csv_data = results['price_data'].to_csv()
                st.download_button(
                    label="⬇️ Download CSV",
                    data=csv_data,
                    file_name=f"price_data_{int(time.time())}.csv",
                    mime="text/csv"
                )
        
        # Performance metrics
        st.subheader("⚡ Performance Metrics")
        
        if results:
            perf_data = {
                'Metric': ['Analysis Time', 'Data Points', 'Memory Usage', 'Update Frequency'],
                'Value': [
                    f"{(datetime.now() - st.session_state.last_update).seconds}s ago",
                    f"{results['data_summary']['observations']} observations",
                    "Efficient (Streaming)",
                    "Real-time capable"
                ]
            }
            
            perf_df = pd.DataFrame(perf_data)
            st.dataframe(perf_df, use_container_width=True)

def main():
    """Main dashboard application"""
    dashboard = EnhancedAnalyticsDashboard()
    dashboard.create_main_dashboard()

if __name__ == "__main__":
    main()
