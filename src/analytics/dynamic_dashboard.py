"""
Dynamic Statistics Dashboard - Real-time updating HTML with charts and live data
Auto-refreshes every 5 seconds, shows live graphs and metrics
"""

import json
import os
from datetime import datetime
from pathlib import Path

class DynamicDashboard:
    """Generate dynamic, auto-refreshing HTML dashboard with charts"""
    
    def __init__(self, stats_file: str = "data/bot_statistics.json", output_file: str = "data/dashboard.html"):
        self.stats_file = Path(stats_file)
        self.output_file = Path(output_file)
    
    def load_stats(self) -> dict:
        """Load current statistics"""
        if self.stats_file.exists():
            with open(self.stats_file, 'r') as f:
                return json.load(f)
        return {}
    
    def generate_dynamic_dashboard(self):
        """Generate dynamic HTML dashboard with real-time updates"""
        stats = self.load_stats()
        today = datetime.now().strftime('%Y-%m-%d')
        month = datetime.now().strftime('%Y-%m')
        year = datetime.now().strftime('%Y')
        
        daily_stats = stats.get('daily', {}).get(today, {})
        monthly_stats = stats.get('monthly', {}).get(month, {})
        yearly_stats = stats.get('yearly', {}).get(year, {})
        all_time = stats.get('all_time', {})
        
        # Prepare chart data
        daily_data = []
        for date_key in sorted(stats.get('daily', {}).keys())[-30:]:  # Last 30 days
            day_stats = stats['daily'][date_key]
            daily_data.append({
                'date': date_key,
                'applied': day_stats.get('jobs_applied', 0),
                'skipped': day_stats.get('jobs_skipped', 0),
            })
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Naukri Bot - Live Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 15px 40px rgba(0,0,0,0.15);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .header h1 {{
            color: #333;
            margin-bottom: 5px;
        }}
        
        .header p {{
            color: #666;
            font-size: 14px;
        }}
        
        .refresh-indicator {{
            text-align: right;
            font-size: 12px;
            color: #999;
        }}
        
        .refresh-dot {{
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #10b981;
            border-radius: 50%;
            margin-right: 5px;
            animation: pulse 1.5s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            border-left: 5px solid #667eea;
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        }}
        
        .stat-card.applied {{ border-left-color: #10b981; }}
        .stat-card.skipped {{ border-left-color: #f59e0b; }}
        .stat-card.questions {{ border-left-color: #3b82f6; }}
        .stat-card.redirects {{ border-left-color: #ef4444; }}
        .stat-card.success {{ border-left-color: #8b5cf6; }}
        
        .stat-label {{
            color: #666;
            font-size: 12px;
            text-transform: uppercase;
            margin-bottom: 8px;
            font-weight: 600;
        }}
        
        .stat-value {{
            font-size: 36px;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }}
        
        .stat-change {{
            font-size: 12px;
            color: #10b981;
        }}
        
        .chart-container {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        .chart-title {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 20px;
            color: #333;
        }}
        
        .tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            background: white;
            padding: 15px;
            border-radius: 15px;
            flex-wrap: wrap;
        }}
        
        .tab {{
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            background: #f0f0f0;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s;
        }}
        
        .tab.active {{
            background: #667eea;
            color: white;
        }}
        
        .tab-content {{
            display: none;
            animation: fadeIn 0.3s;
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        
        .details-table {{
            width: 100%;
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        .details-table th {{
            background: #f9fafb;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #333;
            border-bottom: 2px solid #e5e7eb;
        }}
        
        .details-table td {{
            padding: 15px;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        .details-table tr:hover {{
            background: #f9fafb;
        }}
        
        .urls-container {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        .url-item {{
            padding: 12px;
            margin: 8px 0;
            background: #f0f0f0;
            border-left: 4px solid #667eea;
            border-radius: 5px;
            word-break: break-all;
            font-size: 12px;
        }}
        
        .footer {{
            text-align: center;
            color: white;
            margin-top: 40px;
            font-size: 12px;
        }}
        
        .live-update {{
            animation: highlight 0.5s ease-in-out;
        }}
        
        @keyframes highlight {{
            0% {{ background-color: #fef3c7; }}
            100% {{ background-color: transparent; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>🤖 Naukri Bot - Live Dashboard</h1>
                <p>Real-time statistics and metrics</p>
            </div>
            <div class="refresh-indicator">
                <span class="refresh-dot"></span>
                <span>Live (refreshing every 5s)</span>
                <div style="margin-top: 8px; font-size: 11px;">
                    Last Bot Execution: <span id="lastSync">{datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}</span>
                </div>
            </div>
        </div>
        
        <!-- TODAY'S METRICS -->
        <h2 style="color: white; margin-bottom: 15px; font-size: 18px;">📊 Today's Performance</h2>
        <div class="stats-grid">
            <div class="stat-card applied">
                <div class="stat-label">Today - Jobs Applied</div>
                <div class="stat-value" id="todayApplied">{daily_stats.get('jobs_applied', 0)}</div>
                <div class="stat-change">+{daily_stats.get('jobs_applied', 0)} from start</div>
            </div>
            <div class="stat-card skipped">
                <div class="stat-label">Today - Jobs Skipped</div>
                <div class="stat-value" id="todaySkipped">{daily_stats.get('jobs_skipped', 0)}</div>
            </div>
            <div class="stat-card questions">
                <div class="stat-label">Today - Questions Answered</div>
                <div class="stat-value" id="todayAnswered">{daily_stats.get('questions_answered', 0)}</div>
            </div>
            <div class="stat-card redirects">
                <div class="stat-label">Today - External Redirects</div>
                <div class="stat-value" id="todayRedirects">{daily_stats.get('external_redirects', 0)}</div>
            </div>
            <div class="stat-card success">
                <div class="stat-label">Today - Success Rate</div>
                <div class="stat-value" id="todaySuccess">{round(daily_stats.get('success_rate', 0), 1)}%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Today - Total Runs</div>
                <div class="stat-value" id="todayRuns">{daily_stats.get('total_runs', 0)}</div>
                <div class="stat-change">Runs every 4 hours</div>
            </div>
        </div>
        
        <!-- PERIOD TABS -->
        <div class="tabs">
            <button class="tab active" onclick="switchTab('today')">Today</button>
            <button class="tab" onclick="switchTab('month')">This Month</button>
            <button class="tab" onclick="switchTab('year')">This Year</button>
            <button class="tab" onclick="switchTab('alltime')">All Time</button>
            <button class="tab" onclick="switchTab('history')">Run History</button>
        </div>
        
        <!-- TODAY TAB -->
        <div id="today-content" class="tab-content active">
            <div class="chart-container">
                <div class="chart-title">Today's Detailed Metrics</div>
                <table class="details-table">
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>Total Runs</td>
                        <td><strong>{daily_stats.get('total_runs', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>Jobs Loaded</td>
                        <td><strong>{daily_stats.get('jobs_loaded', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>Jobs Filtered</td>
                        <td><strong>{daily_stats.get('jobs_filtered', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>Jobs Applied</td>
                        <td><strong style="color: #10b981;">{daily_stats.get('jobs_applied', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>Jobs Skipped</td>
                        <td><strong style="color: #f59e0b;">{daily_stats.get('jobs_skipped', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>Questions Answered</td>
                        <td><strong style="color: #3b82f6;">{daily_stats.get('questions_answered', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>Questions Unanswered</td>
                        <td><strong style="color: #ef4444;">{daily_stats.get('questions_unanswered', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>Decision Tree Calls</td>
                        <td><strong>{daily_stats.get('decision_tree_calls', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>LLM Calls</td>
                        <td><strong>{daily_stats.get('llm_calls', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>Cache Hits</td>
                        <td><strong style="color: #8b5cf6;">{daily_stats.get('cache_hits', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>Success Rate</td>
                        <td><strong style="color: #10b981;">{round(daily_stats.get('success_rate', 0), 1)}%</strong></td>
                    </tr>
                    <tr>
                        <td>Average Duration</td>
                        <td><strong>{round(daily_stats.get('average_duration', 0), 1)}s</strong></td>
                    </tr>
                </table>
            </div>
        </div>
        
        <!-- MONTH TAB -->
        <div id="month-content" class="tab-content">
            <div class="chart-container">
                <div class="chart-title">This Month's Metrics</div>
                <table class="details-table">
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>Total Runs</td>
                        <td><strong>{monthly_stats.get('total_runs', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>Jobs Applied</td>
                        <td><strong style="color: #10b981;">{monthly_stats.get('jobs_applied', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>Jobs Skipped</td>
                        <td><strong style="color: #f59e0b;">{monthly_stats.get('jobs_skipped', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>Questions Total</td>
                        <td><strong>{monthly_stats.get('questions_total', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>Questions Answered</td>
                        <td><strong style="color: #3b82f6;">{monthly_stats.get('questions_answered', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>External Redirects</td>
                        <td><strong style="color: #ef4444;">{monthly_stats.get('external_redirects', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>Success Rate</td>
                        <td><strong style="color: #8b5cf6;">{round(monthly_stats.get('success_rate', 0), 1)}%</strong></td>
                    </tr>
                </table>
            </div>
        </div>
        
        <!-- YEAR TAB -->
        <div id="year-content" class="tab-content">
            <div class="chart-container">
                <div class="chart-title">This Year's Metrics</div>
                <table class="details-table">
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>Total Runs</td>
                        <td><strong>{yearly_stats.get('total_runs', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>Jobs Applied</td>
                        <td><strong style="color: #10b981;">{yearly_stats.get('jobs_applied', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>Jobs Skipped</td>
                        <td><strong style="color: #f59e0b;">{yearly_stats.get('jobs_skipped', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>Questions Total</td>
                        <td><strong>{yearly_stats.get('questions_total', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>External Redirects</td>
                        <td><strong style="color: #ef4444;">{yearly_stats.get('external_redirects', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>Success Rate</td>
                        <td><strong style="color: #8b5cf6;">{round(yearly_stats.get('success_rate', 0), 1)}%</strong></td>
                    </tr>
                </table>
            </div>
        </div>
        
        <!-- ALL TIME TAB -->
        <div id="alltime-content" class="tab-content">
            <div class="chart-container">
                <div class="chart-title">All-Time Metrics</div>
                <table class="details-table">
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>Total Runs</td>
                        <td><strong>{all_time.get('total_runs', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>Jobs Applied</td>
                        <td><strong style="color: #10b981;">{all_time.get('jobs_applied', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>Jobs Skipped</td>
                        <td><strong style="color: #f59e0b;">{all_time.get('jobs_skipped', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>Questions Answered</td>
                        <td><strong style="color: #3b82f6;">{all_time.get('questions_answered', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>External Redirects</td>
                        <td><strong style="color: #ef4444;">{all_time.get('external_redirects', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>LLM Calls</td>
                        <td><strong>{all_time.get('llm_calls', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>Decision Tree Calls</td>
                        <td><strong>{all_time.get('decision_tree_calls', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>Cache Hits</td>
                        <td><strong>{all_time.get('cache_hits', 0)}</strong></td>
                    </tr>
                    <tr>
                        <td>Success Rate</td>
                        <td><strong style="color: #8b5cf6;">{round(all_time.get('success_rate', 0), 1)}%</strong></td>
                    </tr>
                </table>
            </div>
        </div>

        <!-- RUN HISTORY TAB -->
        <div id="history-content" class="tab-content">
            <div class="chart-container">
                <div class="chart-title">Last 100 Runs</div>
                <table class="details-table" style="font-size: 13px;">
                    <tr>
                        <th>Time</th>
                        <th>Status</th>
                        <th>Applied</th>
                        <th>Skipped</th>
                        <th>Errors</th>
                        <th>Duration</th>
                    </tr>
                    """ + "".join([
                        f'''
                        <tr style="{'background-color: #fee2e2;' if 'Network Offline' in r.get('error_list', []) else ''}">
                            <td><strong>{r.get('timestamp', 'N/A')}</strong></td>
                            <td>
                                {'<span style="color: #ef4444; font-weight: bold;">Network Offline</span>' if 'Network Offline' in r.get('error_list', []) 
                                else '<span style="color: #ef4444; font-weight: bold;">Failed</span>' if r.get('errors', 0) > 0 
                                else '<span style="color: #10b981; font-weight: bold;">Success</span>'}
                            </td>
                            <td><span style="color: #10b981; font-weight: bold;">{r.get('jobs_applied', 0)}</span> / {r.get('jobs_loaded', 0)}</td>
                            <td>{r.get('jobs_skipped', 0)}</td>
                            <td>{r.get('errors', 0)}</td>
                            <td>{round(r.get('duration', 0), 1)}s</td>
                        </tr>
                        ''' for r in stats.get('run_history', [])
                    ]) + """
                </table>
            </div>
        </div>
        
        <!-- EXTERNAL URLS -->
        <div class="urls-container" style="margin-top: 30px;">
            <h3 style="margin-bottom: 15px;">🔗 External Company Redirects (Today)</h3>
            <div>
                {chr(10).join([f'<div class="url-item">{url}</div>' for url in daily_stats.get('external_urls', [])])}
            </div>
        </div>
        
        <div class="footer">
            <p>🤖 Naukri Bot - Automated Job Applications Dashboard</p>
            <p>Stats refresh every 5 seconds | Data stored in: data/bot_statistics.json</p>
        </div>
    </div>
    
    <script>
        function switchTab(tab) {{
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            
            // Show selected tab
            document.getElementById(tab + '-content').classList.add('active');
            event.target.classList.add('active');
        }}
        
        // Auto-refresh every 5 seconds
        setInterval(function() {{
            location.reload();
        }}, 5000);
        
        // Update last sync time
        setInterval(function() {{
            const now = new Date();
            document.getElementById('lastSync').textContent = now.toLocaleTimeString();
        }}, 1000);
    </script>
</body>
</html>
        """
        
        with open(self.output_file, 'w') as f:
            f.write(html)
        
        return str(self.output_file)

if __name__ == "__main__":
    dashboard = DynamicDashboard()
    output = dashboard.generate_dynamic_dashboard()
    print(f"✅ Dynamic dashboard generated: {output}")
