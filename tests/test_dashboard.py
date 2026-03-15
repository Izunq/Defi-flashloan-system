#!/usr/bin/env python3
"""
Test Status Dashboard

A simple web dashboard to view test results and system status.
"""

import json
import time
import os
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver
import threading

class TestDashboardHandler(SimpleHTTPRequestHandler):
    """Custom handler for test dashboard."""
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/':
            self.serve_dashboard()
        elif self.path == '/api/status':
            self.serve_status_api()
        elif self.path == '/api/results':
            self.serve_results_api()
        else:
            super().do_GET()
    
    def serve_dashboard(self):
        """Serve the main dashboard HTML."""
        html_content = self.generate_dashboard_html()
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def serve_status_api(self):
        """Serve system status API."""
        status = self.get_system_status()
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(status).encode())
    
    def serve_results_api(self):
        """Serve test results API."""
        results = self.get_test_results()
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(results).encode())
    
    def get_system_status(self):
        """Get current system status."""
        return {
            'timestamp': datetime.now().isoformat(),
            'system_health': 'healthy',
            'last_test_run': self.get_last_test_time(),
            'test_environment': 'ready',
            'dependencies': 'installed'
        }
    
    def get_test_results(self):
        """Get latest test results."""
        results_file = Path('test_report.json')
        if results_file.exists():
            with open(results_file) as f:
                return json.load(f)
        
        return {
            'test_run_info': {
                'timestamp': 'N/A',
                'total_duration': 0,
                'test_suites_run': 0
            },
            'summary': {
                'total_suites': 0,
                'passed_suites': 0,
                'failed_suites': 0,
                'success_rate': 0
            },
            'test_results': []
        }
    
    def get_last_test_time(self):
        """Get the last test execution time."""
        log_files = list(Path('.').glob('test*.log'))
        if log_files:
            latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
            return datetime.fromtimestamp(latest_log.stat().st_mtime).isoformat()
        return 'Never'
    
    def generate_dashboard_html(self):
        """Generate the dashboard HTML."""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>Flash Loan System - Test Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        
        .header {
            background: #2c3e50;
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            opacity: 0.8;
            font-size: 1.1em;
        }
        
        .dashboard {
            padding: 30px;
        }
        
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .status-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            border-left: 4px solid #28a745;
        }
        
        .status-card.warning {
            border-left-color: #ffc107;
        }
        
        .status-card.error {
            border-left-color: #dc3545;
        }
        
        .status-card h3 {
            color: #2c3e50;
            margin-bottom: 10px;
        }
        
        .status-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #28a745;
        }
        
        .status-value.warning {
            color: #ffc107;
        }
        
        .status-value.error {
            color: #dc3545;
        }
        
        .test-results {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
        }
        
        .test-suite {
            background: white;
            border-radius: 5px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #28a745;
        }
        
        .test-suite.failed {
            border-left-color: #dc3545;
        }
        
        .test-suite.error {
            border-left-color: #ffc107;
        }
        
        .actions {
            display: flex;
            gap: 10px;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        
        .btn {
            background: #007bff;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            transition: background 0.3s;
        }
        
        .btn:hover {
            background: #0056b3;
        }
        
        .btn.success {
            background: #28a745;
        }
        
        .btn.success:hover {
            background: #1e7e34;
        }
        
        .btn.warning {
            background: #ffc107;
            color: #212529;
        }
        
        .btn.warning:hover {
            background: #e0a800;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            color: #6c757d;
        }
        
        .auto-refresh {
            text-align: center;
            margin-top: 20px;
            color: #6c757d;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Flash Loan System</h1>
            <p>Test Dashboard & System Monitor</p>
        </div>
        
        <div class="dashboard">
            <div class="status-grid" id="statusGrid">
                <div class="loading">Loading system status...</div>
            </div>
            
            <div class="actions">
                <button class="btn success" onclick="runTests('smoke')">🚀 Run Smoke Tests</button>
                <button class="btn" onclick="runTests('unit')">🔧 Run Unit Tests</button>
                <button class="btn warning" onclick="runTests('security')">🔒 Run Security Tests</button>
                <button class="btn" onclick="runTests('all')">🎯 Run All Tests</button>
                <button class="btn" onclick="refreshData()">🔄 Refresh</button>
            </div>
            
            <div class="test-results" id="testResults">
                <div class="loading">Loading test results...</div>
            </div>
            
            <div class="auto-refresh">
                <small>Auto-refresh every 30 seconds | Last updated: <span id="lastUpdate">Never</span></small>
            </div>
        </div>
    </div>

    <script>
        let refreshInterval;
        
        function updateLastRefresh() {
            document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
        }
        
        async function fetchData(endpoint) {
            try {
                const response = await fetch(endpoint);
                return await response.json();
            } catch (error) {
                console.error('Failed to fetch data:', error);
                return null;
            }
        }
        
        async function refreshData() {
            const status = await fetchData('/api/status');
            const results = await fetchData('/api/results');
            
            if (status) updateStatusGrid(status);
            if (results) updateTestResults(results);
            
            updateLastRefresh();
        }
        
        function updateStatusGrid(status) {
            const grid = document.getElementById('statusGrid');
            
            grid.innerHTML = `
                <div class="status-card">
                    <h3>System Health</h3>
                    <div class="status-value">${status.system_health}</div>
                </div>
                <div class="status-card">
                    <h3>Test Environment</h3>
                    <div class="status-value">${status.test_environment}</div>
                </div>
                <div class="status-card">
                    <h3>Dependencies</h3>
                    <div class="status-value">${status.dependencies}</div>
                </div>
                <div class="status-card">
                    <h3>Last Test Run</h3>
                    <div class="status-value">${formatDateTime(status.last_test_run)}</div>
                </div>
            `;
        }
        
        function updateTestResults(results) {
            const container = document.getElementById('testResults');
            
            if (!results.test_results || results.test_results.length === 0) {
                container.innerHTML = '<div class="loading">No test results available</div>';
                return;
            }
            
            const summary = results.summary;
            let html = `
                <h3>Test Summary</h3>
                <div class="status-grid">
                    <div class="status-card">
                        <h3>Total Suites</h3>
                        <div class="status-value">${summary.total_suites}</div>
                    </div>
                    <div class="status-card">
                        <h3>Passed</h3>
                        <div class="status-value">${summary.passed_suites}</div>
                    </div>
                    <div class="status-card ${summary.failed_suites > 0 ? 'error' : ''}">
                        <h3>Failed</h3>
                        <div class="status-value ${summary.failed_suites > 0 ? 'error' : ''}">${summary.failed_suites}</div>
                    </div>
                    <div class="status-card">
                        <h3>Success Rate</h3>
                        <div class="status-value">${summary.success_rate.toFixed(1)}%</div>
                    </div>
                </div>
                
                <h3>Test Suite Details</h3>
            `;
            
            results.test_results.forEach(result => {
                const statusClass = result.status === 'PASS' ? '' : 
                                  result.status === 'FAIL' ? 'failed' : 'error';
                
                html += `
                    <div class="test-suite ${statusClass}">
                        <h4>${result.test_name} - ${result.status}</h4>
                        <p><strong>Duration:</strong> ${result.duration.toFixed(2)}s</p>
                        <p><strong>Tests:</strong> 
                           ${result.details.tests_passed || 0} passed, 
                           ${result.details.tests_failed || 0} failed, 
                           ${result.details.tests_skipped || 0} skipped</p>
                        ${result.details.coverage_percentage ? 
                          `<p><strong>Coverage:</strong> ${result.details.coverage_percentage.toFixed(1)}%</p>` : ''}
                        ${result.error_message ? 
                          `<p style="color: #dc3545;"><strong>Error:</strong> ${result.error_message}</p>` : ''}
                    </div>
                `;
            });
            
            container.innerHTML = html;
        }
        
        function formatDateTime(dateString) {
            if (!dateString || dateString === 'Never') return 'Never';
            return new Date(dateString).toLocaleString();
        }
        
        function runTests(testType) {
            // This would trigger test execution in a real implementation
            alert(`Running ${testType} tests...\\n\\nIn a full implementation, this would execute:\\npython test_runner.py --suites ${testType}`);
        }
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            refreshData();
            refreshInterval = setInterval(refreshData, 30000); // Refresh every 30 seconds
        });
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', function() {
            if (refreshInterval) {
                clearInterval(refreshInterval);
            }
        });
    </script>
</body>
</html>
        """

def start_dashboard(port=8080):
    """Start the test dashboard server."""
    try:
        with socketserver.TCPServer(("", port), TestDashboardHandler) as httpd:
            print(f"🌐 Test Dashboard running at http://localhost:{port}")
            print("📊 View test results and system status")
            print("🔄 Auto-refreshes every 30 seconds")
            print("Press Ctrl+C to stop")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped")
    except Exception as e:
        print(f"❌ Failed to start dashboard: {e}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Status Dashboard')
    parser.add_argument('--port', type=int, default=8080, help='Port to run dashboard on')
    
    args = parser.parse_args()
    start_dashboard(args.port)
