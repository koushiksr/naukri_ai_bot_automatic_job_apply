"""
Naukri Bot Scheduler - Runs bot every 15 minutes
Uses APScheduler for reliable, production-ready scheduling
"""

import time
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

# Setup logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)-8s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_dir / 'scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class NaukriBotScheduler:
    """Scheduler for running Naukri bot at regular intervals"""
    
    def __init__(self, interval_minutes: int = 15, max_instances: int = 1):
        """
        Initialize scheduler
        
        Args:
            interval_minutes: Interval between runs (default: 15)
            max_instances: Max concurrent instances of job (default: 1)
        """
        self.interval_minutes = interval_minutes
        self.max_instances = max_instances
        self.scheduler = BackgroundScheduler(daemon=False)
        
        # Statistics
        self.stats = {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'total_duration': 0,
            'last_run_time': None,
            'next_run_time': None,
            'start_time': None,
        }
        
        # Setup event listeners
        self.scheduler.add_listener(self._job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._job_error, EVENT_JOB_ERROR)
    
    def _job_executed(self, event):
        """Called when job executes successfully"""
        self.stats['successful_runs'] += 1
        logger.info(f"✅ Job completed successfully (Run #{self.stats['total_runs']})")
    
    def _job_error(self, event):
        """Called when job fails"""
        self.stats['failed_runs'] += 1
        logger.error(f"❌ Job failed (Run #{self.stats['total_runs']}): {event.exception}")
    
    def bot_job(self):
        """
        Main job function - runs the Naukri bot
        This is called every 15 minutes
        """
        self.stats['total_runs'] += 1
        run_number = self.stats['total_runs']
        
        try:
            logger.info("=" * 70)
            logger.info(f"🔎 [Run #{run_number}] Starting bot execution...")
            logger.info(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            start_time = time.time()
            
            # Import and run bot
            from src.bot import main
            main()
            
            duration = time.time() - start_time
            self.stats['total_duration'] += duration
            self.stats['last_run_time'] = datetime.now()
            
            logger.info(f"✅ [Run #{run_number}] Completed in {duration:.2f} seconds")
            logger.info(f"📊 Stats: {self.stats['successful_runs']} successful, {self.stats['failed_runs']} failed")
            logger.info("=" * 70)
            
        except Exception as e:
            duration = time.time() - start_time
            self.stats['total_duration'] += duration
            logger.error(f"❌ [Run #{run_number}] Failed after {duration:.2f}s: {str(e)}", exc_info=True)
            logger.info("=" * 70)
            raise
    
    def start(self):
        """Start the scheduler"""
        try:
            logger.info("=" * 70)
            logger.info("🚀 Starting Naukri Bot Scheduler")
            logger.info("=" * 70)
            logger.info(f"📋 Configuration:")
            logger.info(f"   - Interval: Every {self.interval_minutes} minutes")
            logger.info(f"   - Max instances: {self.max_instances}")
            logger.info(f"   - Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            self.stats['start_time'] = datetime.now()
            
            # Add the job
            self.scheduler.add_job(
                self.bot_job,
                'interval',
                minutes=self.interval_minutes,
                id='naukri_bot_job',
                name='Naukri Bot Auto-Applicant',
                max_instances=self.max_instances,
                misfire_grace_time=60,  # Allow 60 seconds grace time for missed runs
                replace_existing=True,
            )
            
            logger.info("✅ Job added to scheduler")
            logger.info("=" * 70)
            
            # Start scheduler
            self.scheduler.start()
            logger.info("✅ Scheduler started successfully")
            logger.info("📍 Press Ctrl+C to stop")
            logger.info("=" * 70)
            
            # Keep running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("🛑 Interrupt signal received (Ctrl+C)")
                self.stop()
        
        except Exception as e:
            logger.error(f"❌ Failed to start scheduler: {e}", exc_info=True)
            sys.exit(1)
    
    def stop(self):
        """Stop the scheduler gracefully"""
        logger.info("=" * 70)
        logger.info("🛑 Stopping scheduler...")
        
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
        
        logger.info(f"📊 Final Statistics:")
        logger.info(f"   - Total runs: {self.stats['total_runs']}")
        logger.info(f"   - Successful: {self.stats['successful_runs']}")
        logger.info(f"   - Failed: {self.stats['failed_runs']}")
        
        if self.stats['total_runs'] > 0:
            success_rate = (self.stats['successful_runs'] / self.stats['total_runs']) * 100
            logger.info(f"   - Success rate: {success_rate:.1f}%")
            
            if self.stats['total_duration'] > 0:
                avg_duration = self.stats['total_duration'] / self.stats['total_runs']
                logger.info(f"   - Average duration: {avg_duration:.2f}s")
        
        uptime = datetime.now() - self.stats['start_time']
        logger.info(f"   - Uptime: {uptime}")
        
        logger.info("✅ Scheduler stopped")
        logger.info("=" * 70)
    
    def get_status(self) -> dict:
        """Get current scheduler status"""
        next_job = self.scheduler.get_job('naukri_bot_job')
        
        return {
            'status': 'running' if self.scheduler.running else 'stopped',
            'total_runs': self.stats['total_runs'],
            'successful_runs': self.stats['successful_runs'],
            'failed_runs': self.stats['failed_runs'],
            'success_rate': f"{(self.stats['successful_runs'] / max(self.stats['total_runs'], 1)) * 100:.1f}%",
            'average_duration': f"{self.stats['total_duration'] / max(self.stats['total_runs'], 1):.2f}s",
            'last_run': self.stats['last_run_time'].isoformat() if self.stats['last_run_time'] else None,
            'next_run': next_job.next_run_time.isoformat() if next_job and next_job.next_run_time else None,
            'uptime': str(datetime.now() - self.stats['start_time']) if self.stats['start_time'] else None,
        }


def main():
    """Entry point for scheduler"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Naukri Bot Scheduler')
    parser.add_argument(
        '--interval',
        type=int,
        default=15,
        help='Interval between runs in minutes (default: 15)'
    )
    parser.add_argument(
        '--max-instances',
        type=int,
        default=1,
        help='Maximum concurrent instances (default: 1)'
    )
    
    args = parser.parse_args()
    
    # Create and start scheduler
    scheduler = NaukriBotScheduler(
        interval_minutes=args.interval,
        max_instances=args.max_instances
    )
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        scheduler.stop()
    except Exception as e:
        logger.error(f"Scheduler error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
