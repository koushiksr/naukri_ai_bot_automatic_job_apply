"""
Advanced Statistics Tracker - Detailed metrics for Naukri Bot
Tracks: applications, skipped, answered questions, redirects, etc.
Stores: daily, weekly, monthly, yearly statistics
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any
from collections import defaultdict

class BotStatistics:
    """Track and store detailed bot statistics"""
    
    def __init__(self, stats_file: str = "data/bot_statistics.json"):
        self.stats_file = Path(stats_file)
        self.stats_file.parent.mkdir(exist_ok=True)
        self.stats = self._load_stats()
    
    def _load_stats(self) -> Dict[str, Any]:
        """Load existing statistics"""
        if self.stats_file.exists():
            with open(self.stats_file, 'r') as f:
                return json.load(f)
        
        return {
            'created_at': datetime.now().isoformat(),
            'daily': defaultdict(self._default_stats),
            'weekly': defaultdict(self._default_stats),
            'monthly': defaultdict(self._default_stats),
            'yearly': defaultdict(self._default_stats),
            'all_time': self._default_stats(),
        }
    
    def _default_stats(self) -> Dict:
        """Default statistics structure"""
        return {
            'total_runs': 0,
            'jobs_loaded': 0,
            'jobs_filtered': 0,
            'jobs_applied': 0,
            'jobs_skipped': 0,
            'questions_total': 0,
            'questions_answered': 0,
            'questions_unanswered': 0,
            'questions_by_type': {},
            'external_redirects': 0,
            'external_urls': [],
            'errors': 0,
            'error_list': [],
            'llm_calls': 0,
            'decision_tree_calls': 0,
            'cache_hits': 0,
            'success_rate': 0.0,
            'average_duration': 0.0,
            'total_duration': 0.0,
            'run_count': 0,
        }
    
    def record_run(self, run_data: Dict[str, Any]):
        """Record statistics for a single run"""
        now = datetime.now()
        day_key = now.strftime('%Y-%m-%d')
        week_key = now.strftime('%Y-W%W')
        month_key = now.strftime('%Y-%m')
        year_key = now.strftime('%Y')
        
        # Initialize keys if not exist
        if day_key not in self.stats['daily']:
            self.stats['daily'][day_key] = self._default_stats()
        if week_key not in self.stats['weekly']:
            self.stats['weekly'][week_key] = self._default_stats()
        if month_key not in self.stats['monthly']:
            self.stats['monthly'][month_key] = self._default_stats()
        if year_key not in self.stats['yearly']:
            self.stats['yearly'][year_key] = self._default_stats()
        
        # Update all time periods
        for period in [self.stats['daily'][day_key], 
                       self.stats['weekly'][week_key],
                       self.stats['monthly'][month_key],
                       self.stats['yearly'][year_key],
                       self.stats['all_time']]:
            
            period['total_runs'] += 1
            period['jobs_loaded'] += run_data.get('jobs_loaded', 0)
            period['jobs_filtered'] += run_data.get('jobs_filtered', 0)
            period['jobs_applied'] += run_data.get('jobs_applied', 0)
            period['jobs_skipped'] += run_data.get('jobs_skipped', 0)
            period['questions_total'] += run_data.get('questions_total', 0)
            period['questions_answered'] += run_data.get('questions_answered', 0)
            period['questions_unanswered'] += run_data.get('questions_unanswered', 0)
            period['external_redirects'] += run_data.get('external_redirects', 0)
            period['llm_calls'] += run_data.get('llm_calls', 0)
            period['decision_tree_calls'] += run_data.get('decision_tree_calls', 0)
            period['cache_hits'] += run_data.get('cache_hits', 0)
            period['errors'] += run_data.get('errors', 0)
            period['total_duration'] += run_data.get('duration', 0)
            period['run_count'] += 1
            
            # Merge question types
            for q_type, count in run_data.get('questions_by_type', {}).items():
                period['questions_by_type'][q_type] = \
                    period['questions_by_type'].get(q_type, 0) + count
            
            # Track external URLs
            for url in run_data.get('external_urls', []):
                if url not in period['external_urls']:
                    period['external_urls'].append(url)
            
            # Track errors
            for error in run_data.get('error_list', []):
                if error not in period['error_list']:
                    period['error_list'].append(error)
            
            # Calculate averages
            if period['run_count'] > 0:
                period['average_duration'] = period['total_duration'] / period['run_count']
                if period['total_runs'] > 0:
                    period['success_rate'] = (period['jobs_applied'] / max(period['jobs_loaded'], 1)) * 100
        
        self._save_stats()
    
    def _save_stats(self):
        """Save statistics to file"""
        with open(self.stats_file, 'w') as f:
            # Convert defaultdict to dict for JSON serialization
            stats_dict = {
                'created_at': self.stats['created_at'],
                'daily': dict(self.stats['daily']),
                'weekly': dict(self.stats['weekly']),
                'monthly': dict(self.stats['monthly']),
                'yearly': dict(self.stats['yearly']),
                'all_time': self.stats['all_time'],
            }
            json.dump(stats_dict, f, indent=2, default=str)
    
    def get_stats(self, period: str = 'all_time', period_key: str = None) -> Dict:
        """Get statistics for a period"""
        if period == 'all_time':
            return self.stats['all_time']
        
        period_dict = self.stats.get(period, {})
        if period_key:
            return period_dict.get(period_key, self._default_stats())
        
        return period_dict
    
    def generate_html_report(self, output_file: str = "data/bot_report.html"):
        """Generate HTML dashboard with statistics"""
        html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Naukri Bot Statistics Dashboard</title>
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
        }
        
        .header {
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            color: #333;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #666;
            font-size: 14px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            border-left: 5px solid #667eea;
        }
        
        .stat-card.applied {
            border-left-color: #10b981;
        }
        
        .stat-card.skipped {
            border-left-color: #f59e0b;
        }
        
        .stat-card.questions {
            border-left-color: #3b82f6;
        }
        
        .stat-card.redirects {
            border-left-color: #ef4444;
        }
        
        .stat-label {
            color: #666;
            font-size: 12px;
            text-transform: uppercase;
            margin-bottom: 5px;
        }
        
        .stat-value {
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }
        
        .stat-subtext {
            color: #999;
            font-size: 12px;
            margin-top: 5px;
        }
        
        .period-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            background: white;
            padding: 10px;
            border-radius: 10px;
        }
        
        .tab-button {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            background: #f0f0f0;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s;
        }
        
        .tab-button.active {
            background: #667eea;
            color: white;
        }
        
        .table-section {
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            background: #f9fafb;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #333;
            border-bottom: 2px solid #e5e7eb;
        }
        
        td {
            padding: 12px;
            border-bottom: 1px solid #e5e7eb;
        }
        
        tr:hover {
            background: #f9fafb;
        }
        
        .success-rate {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 5px;
            font-weight: 600;
            font-size: 12px;
        }
        
        .success-rate.high {
            background: #d1fae5;
            color: #065f46;
        }
        
        .success-rate.medium {
            background: #fef3c7;
            color: #92400e;
        }
        
        .success-rate.low {
            background: #fee2e2;
            color: #7f1d1d;
        }
        
        .chart-container {
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .urls-list {
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .url-item {
            padding: 10px;
            margin: 5px 0;
            background: #f9fafb;
            border-left: 3px solid #667eea;
            border-radius: 5px;
            font-size: 12px;
            word-break: break-all;
        }
        
        .footer {
            text-align: center;
            color: white;
            margin-top: 30px;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Naukri Bot Statistics Dashboard</h1>
            <p>Last updated: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
        </div>
        
        <!-- DAILY STATS -->
        <div class="stats-grid">
            <div class="stat-card applied">
                <div class="stat-label">Today - Jobs Applied</div>
                <div class="stat-value">""" + str(self.stats['daily'].get(datetime.now().strftime('%Y-%m-%d'), {}).get('jobs_applied', 0)) + """</div>
            </div>
            <div class="stat-card skipped">
                <div class="stat-label">Today - Jobs Skipped</div>
                <div class="stat-value">""" + str(self.stats['daily'].get(datetime.now().strftime('%Y-%m-%d'), {}).get('jobs_skipped', 0)) + """</div>
            </div>
            <div class="stat-card questions">
                <div class="stat-label">Today - Questions Answered</div>
                <div class="stat-value">""" + str(self.stats['daily'].get(datetime.now().strftime('%Y-%m-%d'), {}).get('questions_answered', 0)) + """</div>
            </div>
            <div class="stat-card redirects">
                <div class="stat-label">Today - External Redirects</div>
                <div class="stat-value">""" + str(self.stats['daily'].get(datetime.now().strftime('%Y-%m-%d'), {}).get('external_redirects', 0)) + """</div>
            </div>
        </div>
        
        <!-- MONTHLY STATS -->
        <div class="stats-grid">
            <div class="stat-card applied">
                <div class="stat-label">This Month - Jobs Applied</div>
                <div class="stat-value">""" + str(self.stats['monthly'].get(datetime.now().strftime('%Y-%m'), {}).get('jobs_applied', 0)) + """</div>
            </div>
            <div class="stat-card skipped">
                <div class="stat-label">This Month - Jobs Skipped</div>
                <div class="stat-value">""" + str(self.stats['monthly'].get(datetime.now().strftime('%Y-%m'), {}).get('jobs_skipped', 0)) + """</div>
            </div>
            <div class="stat-card questions">
                <div class="stat-label">This Month - Questions Total</div>
                <div class="stat-value">""" + str(self.stats['monthly'].get(datetime.now().strftime('%Y-%m'), {}).get('questions_total', 0)) + """</div>
            </div>
            <div class="stat-card redirects">
                <div class="stat-label">This Month - Avg Success Rate</div>
                <div class="stat-value">""" + str(round(self.stats['monthly'].get(datetime.now().strftime('%Y-%m'), {}).get('success_rate', 0), 1)) + """%</div>
            </div>
        </div>
        
        <!-- YEARLY STATS -->
        <div class="stats-grid">
            <div class="stat-card applied">
                <div class="stat-label">This Year - Jobs Applied</div>
                <div class="stat-value">""" + str(self.stats['yearly'].get(datetime.now().strftime('%Y'), {}).get('jobs_applied', 0)) + """</div>
            </div>
            <div class="stat-card skipped">
                <div class="stat-label">This Year - Jobs Skipped</div>
                <div class="stat-value">""" + str(self.stats['yearly'].get(datetime.now().strftime('%Y'), {}).get('jobs_skipped', 0)) + """</div>
            </div>
            <div class="stat-card questions">
                <div class="stat-label">This Year - Total Runs</div>
                <div class="stat-value">""" + str(self.stats['yearly'].get(datetime.now().strftime('%Y'), {}).get('total_runs', 0)) + """</div>
            </div>
            <div class="stat-card redirects">
                <div class="stat-label">This Year - External Redirects</div>
                <div class="stat-value">""" + str(self.stats['yearly'].get(datetime.now().strftime('%Y'), {}).get('external_redirects', 0)) + """</div>
            </div>
        </div>
        
        <!-- ALL TIME STATS -->
        <div class="stats-grid">
            <div class="stat-card applied">
                <div class="stat-label">All Time - Jobs Applied</div>
                <div class="stat-value">""" + str(self.stats['all_time'].get('jobs_applied', 0)) + """</div>
            </div>
            <div class="stat-card skipped">
                <div class="stat-label">All Time - Jobs Skipped</div>
                <div class="stat-value">""" + str(self.stats['all_time'].get('jobs_skipped', 0)) + """</div>
            </div>
            <div class="stat-card questions">
                <div class="stat-label">All Time - Questions Answered</div>
                <div class="stat-value">""" + str(self.stats['all_time'].get('questions_answered', 0)) + """</div>
            </div>
            <div class="stat-card redirects">
                <div class="stat-label">All Time - External Redirects</div>
                <div class="stat-value">""" + str(self.stats['all_time'].get('external_redirects', 0)) + """</div>
            </div>
        </div>
        
        <!-- DETAILED TABLE -->
        <div class="table-section">
            <h3>📊 Detailed Metrics (Today)</h3>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Total Runs</td>
                    <td>""" + str(self.stats['daily'].get(datetime.now().strftime('%Y-%m-%d'), {}).get('total_runs', 0)) + """</td>
                </tr>
                <tr>
                    <td>Jobs Loaded</td>
                    <td>""" + str(self.stats['daily'].get(datetime.now().strftime('%Y-%m-%d'), {}).get('jobs_loaded', 0)) + """</td>
                </tr>
                <tr>
                    <td>Jobs Filtered</td>
                    <td>""" + str(self.stats['daily'].get(datetime.now().strftime('%Y-%m-%d'), {}).get('jobs_filtered', 0)) + """</td>
                </tr>
                <tr>
                    <td>Jobs Applied</td>
                    <td>""" + str(self.stats['daily'].get(datetime.now().strftime('%Y-%m-%d'), {}).get('jobs_applied', 0)) + """</td>
                </tr>
                <tr>
                    <td>Jobs Skipped</td>
                    <td>""" + str(self.stats['daily'].get(datetime.now().strftime('%Y-%m-%d'), {}).get('jobs_skipped', 0)) + """</td>
                </tr>
                <tr>
                    <td>Questions Answered</td>
                    <td>""" + str(self.stats['daily'].get(datetime.now().strftime('%Y-%m-%d'), {}).get('questions_answered', 0)) + """</td>
                </tr>
                <tr>
                    <td>Questions Unanswered</td>
                    <td>""" + str(self.stats['daily'].get(datetime.now().strftime('%Y-%m-%d'), {}).get('questions_unanswered', 0)) + """</td>
                </tr>
                <tr>
                    <td>LLM Calls</td>
                    <td>""" + str(self.stats['daily'].get(datetime.now().strftime('%Y-%m-%d'), {}).get('llm_calls', 0)) + """</td>
                </tr>
                <tr>
                    <td>Decision Tree Calls</td>
                    <td>""" + str(self.stats['daily'].get(datetime.now().strftime('%Y-%m-%d'), {}).get('decision_tree_calls', 0)) + """</td>
                </tr>
                <tr>
                    <td>Cache Hits</td>
                    <td>""" + str(self.stats['daily'].get(datetime.now().strftime('%Y-%m-%d'), {}).get('cache_hits', 0)) + """</td>
                </tr>
                <tr>
                    <td>Success Rate</td>
                    <td><span class="success-rate high">""" + str(round(self.stats['daily'].get(datetime.now().strftime('%Y-%m-%d'), {}).get('success_rate', 0), 1)) + """%</span></td>
                </tr>
            </table>
        </div>
        
        <!-- EXTERNAL URLS -->
        <div class="urls-list">
            <h3>🔗 External Company Redirects (Today)</h3>
            <div>
                """ + "\n                ".join([f'<div class="url-item">{url}</div>' for url in self.stats['daily'].get(datetime.now().strftime('%Y-%m-%d'), {}).get('external_urls', [])]) + """
            </div>
        </div>
        
        <div class="footer">
            <p>📈 Naukri Bot Automation Dashboard | Updated every 15 minutes</p>
            <p>Data stored in: data/bot_statistics.json</p>
        </div>
    </div>
</body>
</html>
        """
        
        with open(output_file, 'w') as f:
            f.write(html)
        
        return output_file


if __name__ == "__main__":
    # Test
    stats = BotStatistics()
    
    # Record a sample run
    sample_run = {
        'jobs_loaded': 50,
        'jobs_filtered': 30,
        'jobs_applied': 5,
        'jobs_skipped': 25,
        'questions_total': 25,
        'questions_answered': 23,
        'questions_unanswered': 2,
        'questions_by_type': {'salary': 5, 'experience': 8, 'location': 10},
        'external_redirects': 3,
        'external_urls': ['https://company1.com/apply', 'https://company2.com/apply'],
        'llm_calls': 8,
        'decision_tree_calls': 17,
        'cache_hits': 10,
        'errors': 0,
        'error_list': [],
        'duration': 285.5,
    }
    
    stats.record_run(sample_run)
    report_file = stats.generate_html_report()
    print(f"✅ Report generated: {report_file}")
