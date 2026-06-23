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
            'run_history': [],
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
        
        # Append to individual run history (keep last 100 runs)
        run_record = run_data.copy()
        run_record['timestamp'] = now.strftime('%Y-%m-%d %H:%M:%S')
        if 'run_history' not in self.stats:
            self.stats['run_history'] = []
        self.stats['run_history'].insert(0, run_record)
        self.stats['run_history'] = self.stats['run_history'][:100]
        
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
                'run_history': self.stats.get('run_history', []),
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
    

