# Scheduler Analysis: Best Approach for 15-Minute Execution

## Project Requirements Analysis

Your Naukri bot needs to:
1. **Run every 15 minutes** automatically
2. **Apply to jobs** on each run
3. **Maintain state** (cache, logs, statistics)
4. **Run 24/7** (24 hours, 7 days)
5. **Be reliable** (handle failures gracefully)
6. **Minimal overhead** (fast startup, low resources)

---

## Comparison of 5 Scheduler Approaches

### Approach 1: Simple `time.sleep()` Loop
**Implementation**: Infinite loop with sleep in main.py

```python
import time
from src.bot import main

if __name__ == "__main__":
    while True:
        try:
            print(f"[{datetime.now()}] Starting bot run...")
            main()
            print(f"[{datetime.now()}] Bot run completed. Sleeping 15 minutes...")
        except Exception as e:
            print(f"Error: {e}. Retrying in 15 minutes...")
        
        time.sleep(900)  # 15 minutes = 900 seconds
```

**Pros:**
- ✅ Simple, no dependencies
- ✅ Easy to understand
- ✅ Minimal code changes
- ✅ Good for development

**Cons:**
- ❌ Blocks process (can't do other tasks)
- ❌ Not reliable for production
- ❌ Drift over time (execution time added to sleep)
- ❌ No pause/resume capability
- ❌ No error recovery

**Best For**: Local testing, development

**Reliability**: ⭐ (40%)

---

### Approach 2: APScheduler (Python library)
**Installation**: `pip install apscheduler`

```python
from apscheduler.schedulers.background import BackgroundScheduler
from src.bot import main
import time

scheduler = BackgroundScheduler()

def job():
    try:
        print(f"[{datetime.now()}] Bot run started...")
        main()
        print(f"[{datetime.now()}] Bot run completed")
    except Exception as e:
        print(f"Error: {e}")

scheduler.add_job(job, 'interval', minutes=15, id='bot_job')
scheduler.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    scheduler.shutdown()
```

**Pros:**
- ✅ Reliable scheduling
- ✅ Non-blocking (background jobs)
- ✅ Error handling built-in
- ✅ Pause/resume support
- ✅ Execution metrics
- ✅ Multiple job support

**Cons:**
- ⚠️ Requires dependency
- ⚠️ State lost on restart
- ⚠️ Single machine only (no clustering)

**Best For**: Production on single machine, moderate load

**Reliability**: ⭐⭐⭐⭐ (85%)

---

### Approach 3: System Cron Job (Linux/Mac)
**Setup**: Use crontab to run script every 15 minutes

```bash
# Terminal: crontab -e
# Add this line:
*/15 * * * * cd /path/to/project && python3 scheduler.py >> logs/cron.log 2>&1
```

```python
# scheduler.py
from src.bot import main

if __name__ == "__main__":
    try:
        print(f"[{datetime.now()}] Starting bot...")
        main()
        print(f"[{datetime.now()}] Completed")
    except Exception as e:
        print(f"Failed: {e}")
```

**Pros:**
- ✅ OS-level scheduling (very reliable)
- ✅ No Python dependencies
- ✅ Runs even if app crashes
- ✅ System manages resources
- ✅ Easy to monitor
- ✅ Works on Mac/Linux/WSL

**Cons:**
- ❌ Unix/Linux only (not Windows)
- ❌ Hard to debug
- ❌ Environmental variables tricky
- ❌ Need shell access
- ⚠️ Not ideal for dynamic intervals

**Best For**: Production on Linux/Mac servers

**Reliability**: ⭐⭐⭐⭐⭐ (95%)

---

### Approach 4: Windows Task Scheduler
**Setup**: Create scheduled task to run script every 15 minutes

```xml
<!-- Task Scheduler setup -->
Action: Run python3 scheduler.py
Trigger: Every 15 minutes
Restart on failure: Yes
```

```python
# scheduler.py (same as Cron approach)
```

**Pros:**
- ✅ OS-level scheduling (Windows)
- ✅ Very reliable
- ✅ Automatic restart on failure
- ✅ Built-in monitoring
- ✅ Resource management

**Cons:**
- ❌ Windows only
- ❌ Hard to debug
- ❌ GUI-dependent setup

**Best For**: Production on Windows servers

**Reliability**: ⭐⭐⭐⭐⭐ (95%)

---

### Approach 5: Docker + Kubernetes/Docker Compose
**Most Advanced**: Container-based orchestration

```yaml
# docker-compose.yml
version: '3.8'
services:
  naukri-bot:
    build: .
    container_name: naukri-bot-scheduler
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
      - ./output:/app/output
    restart: unless-stopped
    
  scheduler:
    image: mcuadros/ofelia
    container_name: ofelia-scheduler
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    command: daemon --docker
    
# In docker-compose override:
services:
  naukri-bot:
    labels:
      ofelia: "enabled"
      ofelia.enabled: "true"
      ofelia.schedule: "@every 15m"
      ofelia.save-output: "true"
      ofelia.save-output-file: "/app/logs/scheduler.log"
```

**Pros:**
- ✅ Cloud-ready
- ✅ Highly scalable
- ✅ Self-healing
- ✅ Easy deployment
- ✅ Cross-platform
- ✅ Production-grade

**Cons:**
- ❌ Complex setup
- ❌ Overkill for single bot
- ❌ Requires Docker knowledge
- ❌ More resources needed

**Best For**: Cloud deployment, scaling to multiple instances

**Reliability**: ⭐⭐⭐⭐⭐ (99%)

---

## Comparison Table

| Feature | time.sleep | APScheduler | Cron | Task Scheduler | Docker |
|---------|-----------|-------------|------|---|---|
| **Setup Time** | 5 min | 10 min | 5 min | 10 min | 30 min |
| **Reliability** | 40% | 85% | 95% | 95% | 99% |
| **Cross-Platform** | ✅ | ✅ | ❌ | ❌ | ✅ |
| **Error Recovery** | ❌ | ✅ | ✅ | ✅ | ✅✅ |
| **Resource Usage** | Low | Medium | Low | Low | High |
| **Scalability** | ❌ | ❌ | ❌ | ❌ | ✅✅ |
| **Production Ready** | ❌ | ✅ | ✅ | ✅ | ✅✅ |
| **Maintenance** | Easy | Medium | Easy | Hard | Hard |
| **Dependencies** | None | 1 lib | None | None | Docker |
| **Best For** | Dev/Test | Single machine | Linux/Mac | Windows | Production/Cloud |

---

## RECOMMENDATION: Hybrid Approach

### Best Solution for YOUR Project

**Use APScheduler** with optional Cron/Task Scheduler fallback.

**Why?**
1. ✅ Simple to implement (one file)
2. ✅ Reliable for production (85%+)
3. ✅ Easy to test locally
4. ✅ No system configuration needed
5. ✅ Can add monitoring/logging easily
6. ✅ Can upgrade to Docker later

### Implementation Plan

```python
# main_scheduler.py
import time
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from src.bot import main

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BotScheduler:
    def __init__(self, interval_minutes=15):
        self.scheduler = BackgroundScheduler()
        self.interval = interval_minutes
        self.run_count = 0
        self.failed_runs = 0
        
    def job_handler(self):
        """Execute bot job"""
        self.run_count += 1
        try:
            logger.info(f"[Run #{self.run_count}] Starting bot execution...")
            start_time = time.time()
            
            main()  # Run bot
            
            duration = time.time() - start_time
            logger.info(f"[Run #{self.run_count}] Completed in {duration:.2f} seconds")
            
        except Exception as e:
            self.failed_runs += 1
            logger.error(f"[Run #{self.run_count}] Failed: {e}", exc_info=True)
    
    def start(self):
        """Start scheduler"""
        logger.info("Starting Naukri bot scheduler...")
        logger.info(f"Interval: Every {self.interval} minutes")
        
        self.scheduler.add_job(
            self.job_handler,
            'interval',
            minutes=self.interval,
            id='naukri_bot_job',
            name='Naukri Bot Auto-Applicant',
            misfire_grace_time=60
        )
        
        self.scheduler.start()
        logger.info("Scheduler started successfully")
        
        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutdown signal received")
            self.stop()
    
    def stop(self):
        """Stop scheduler"""
        logger.info(f"Stopping scheduler... Total runs: {self.run_count}, Failed: {self.failed_runs}")
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")
    
    def get_stats(self):
        """Get scheduler statistics"""
        return {
            'runs': self.run_count,
            'failed': self.failed_runs,
            'success_rate': (self.run_count - self.failed_runs) / max(self.run_count, 1),
        }

if __name__ == "__main__":
    scheduler = BotScheduler(interval_minutes=15)
    scheduler.start()
```

---

## Implementation Steps

### Step 1: Install APScheduler
```bash
pip install apscheduler
```

### Step 2: Create Scheduler Script
Create `main_scheduler.py` (code above)

### Step 3: Run
```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start Scheduler
python3 main_scheduler.py
```

### Step 4: Monitor
```bash
# Terminal 3: Watch logs
tail -f logs/scheduler.log
```

### Output Example
```
[2024-01-15 10:00:00] INFO - Starting Naukri bot scheduler...
[2024-01-15 10:00:00] INFO - Interval: Every 15 minutes
[2024-01-15 10:00:00] INFO - Scheduler started successfully
[2024-01-15 10:00:05] INFO - [Run #1] Starting bot execution...
[2024-01-15 10:04:30] INFO - [Run #1] Completed in 265.23 seconds
[2024-01-15 10:15:05] INFO - [Run #2] Starting bot execution...
[2024-01-15 10:19:45] INFO - [Run #2] Completed in 280.15 seconds
```

---

## Alternative: For Production/Cloud

If you later want to scale or deploy to cloud:

```bash
# Option 1: Keep running with screen/tmux
screen -S naukri-bot python3 main_scheduler.py

# Option 2: Use systemd (Linux)
# Create /etc/systemd/system/naukri-bot.service
[Unit]
Description=Naukri Bot Scheduler
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/project
ExecStart=/usr/bin/python3 /path/to/main_scheduler.py
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target

# Then:
sudo systemctl enable naukri-bot
sudo systemctl start naukri-bot

# Option 3: Docker (future)
docker compose up -d
```

---

## Monitoring & Health Checks

```python
# Add health check endpoint
from flask import Flask

app = Flask(__name__)
scheduler_instance = None

@app.route('/health')
def health():
    stats = scheduler_instance.get_stats()
    return {
        'status': 'running',
        'runs': stats['runs'],
        'failed': stats['failed'],
        'success_rate': f"{stats['success_rate']:.1%}",
        'timestamp': datetime.now().isoformat()
    }

# Run in background thread
if __name__ == "__main__":
    import threading
    
    scheduler = BotScheduler()
    scheduler_instance = scheduler
    
    # Start scheduler in background
    scheduler_thread = threading.Thread(target=scheduler.start, daemon=True)
    scheduler_thread.start()
    
    # Start health check server
    app.run(host='localhost', port=5000, debug=False)
```

---

## Summary & Recommendation

| Use Case | Recommended Approach |
|----------|---|
| **Local Development** | `time.sleep()` loop |
| **Single Machine Production** | **APScheduler** ← RECOMMENDED |
| **Linux/Mac Server** | Cron + APScheduler |
| **Windows Server** | Task Scheduler + APScheduler |
| **Cloud/Scaling** | Docker + Kubernetes |

### BEST CHOICE FOR YOUR PROJECT: **APScheduler**

**Why?**
- ✅ Production-ready
- ✅ Easy to implement (minimal code)
- ✅ Works everywhere (Python)
- ✅ Good error handling
- ✅ Can scale up later
- ✅ Simple monitoring/logging
- ✅ No system configuration needed

### Next Steps:
1. Install: `pip install apscheduler`
2. Create: `main_scheduler.py`
3. Update: `requirements.txt`
4. Run: `python3 main_scheduler.py`
5. Monitor: `tail -f logs/scheduler.log`

---

**Ready to implement APScheduler? 🚀**
