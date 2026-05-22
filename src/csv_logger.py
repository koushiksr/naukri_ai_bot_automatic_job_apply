import os
import csv
from datetime import datetime

class CSVLogger:
    """Logs job application outcomes to separate CSV files for analytics"""
    
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        self.applied_file = os.path.join(data_dir, "applied_jobs.csv")
        self.skipped_file = os.path.join(data_dir, "skipped_jobs.csv")
        self.external_file = os.path.join(data_dir, "external_redirect_jobs.csv")
        
        self._init_files()
        
    def _init_files(self):
        """Initialize CSV files with headers if they don't exist"""
        if not os.path.exists(self.applied_file):
            with open(self.applied_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Date', 'Company', 'Role', 'Experience', 'Location', 'Questions Answered'])
                
        if not os.path.exists(self.skipped_file):
            with open(self.skipped_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Date', 'Company', 'Role', 'Experience', 'Location', 'Skip Reason'])
                
        if not os.path.exists(self.external_file):
            with open(self.external_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Date', 'Company', 'Role', 'Experience', 'Location', 'External URL'])

    def log_applied(self, company: str, role: str, experience: str, location: str, questions_answered: int):
        with open(self.applied_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), company, role, experience, location, questions_answered])

    def log_skipped(self, company: str, role: str, experience: str, location: str, reason: str):
        with open(self.skipped_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), company, role, experience, location, reason])

    def log_external(self, company: str, role: str, experience: str, location: str, url: str):
        with open(self.external_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), company, role, experience, location, url])
