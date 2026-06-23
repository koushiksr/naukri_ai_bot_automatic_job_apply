# Scheduler Quick Start Guide

## Overview

Your bot now runs **automatically every 15 minutes** using APScheduler.

```
Start Once → Runs Every 15 Minutes Forever
```

## Installation

```bash
# 1. Install scheduler dependency
pip install apscheduler

# Or update from requirements.txt
pip install -r requirements.txt
```

## Running the Scheduler

### Terminal Setup (Recommended)

```bash
# Terminal 1: Start Ollama (local LLM)
ollama serve

# Terminal 2: Start Scheduler
cd /Users/koushik/Documents/naukri_ai_bot_automatic_job_apply
source venv/bin/activate
python3 main_scheduler.py

# Terminal 3: Monitor logs (optional)
tail -f logs/scheduler.log
```

### Expected Output

```
======================================================================
🚀 Starting Naukri Bot Scheduler
======================================================================
📋 Configuration:
   - Interval: Every 15 minutes
   - Max instances: 1
   - Start time: 2024-01-15 10:00:00

✅ Job added to scheduler
======================================================================
✅ Scheduler started successfully
📍 Press Ctrl+C to stop
======================================================================

[2024-01-15 10:00:05] INFO - ======================================================================
[2024-01-15 10:00:05] INFO - 🔎 [Run #1] Starting bot execution...
[2024-01-15 10:00:05] INFO - ⏰ Time: 2024-01-15 10:00:05
[2024-01-15 10:04:30] INFO - ✅ [Run #1] Completed in 265.23 seconds
[2024-01-15 10:04:30] INFO - 📊 Stats: 1 successful, 0 failed
[2024-01-15 10:04:30] INFO - ======================================================================

[2024-01-15 10:15:05] INFO - ======================================================================
[2024-01-15 10:15:05] INFO - 🔎 [Run #2] Starting bot execution...
[2024-01-15 10:15:05] INFO - ⏰ Time: 2024-01-15 10:15:05
[2024-01-15 10:19:45] INFO - ✅ [Run #2] Completed in 280.15 seconds
[2024-01-15 10:19:45] INFO - 📊 Stats: 2 successful, 0 failed
[2024-01-15 10:19:45] INFO - ======================================================================
```

## Command-Line Options

```bash
# Default (15 minutes)
python3 main_scheduler.py

# Custom interval (e.g., 5 minutes)
python3 main_scheduler.py --interval 5

# Custom max instances
python3 main_scheduler.py --interval 15 --max-instances 1
```

## Stopping the Scheduler

```bash
# Press Ctrl+C in Terminal 2

# Or from another terminal:
kill $(pgrep -f "python3 main_scheduler.py")
```

## Monitoring

### View Live Logs

```bash
# Terminal 3
tail -f logs/scheduler.log

# Last 100 lines:
tail -n 100 logs/scheduler.log

# Search for errors:
grep "❌" logs/scheduler.log

# Count runs:
grep -c "🔎 \[Run" logs/scheduler.log
```

### Statistics

Scheduler prints stats every run:
```
📊 Stats: 5 successful, 0 failed
```

On shutdown:
```
📊 Final Statistics:
   - Total runs: 5
   - Successful: 5
   - Failed: 0
   - Success rate: 100.0%
   - Average duration: 265.23s
   - Uptime: 1:02:15
```

## What Happens Each Run

1. **Login** - Authenticates with Naukri
2. **Load Jobs** - Fetches available jobs
3. **Filter** - Applies configured filters
4. **Apply** - Uses decision tree + LLM to answer questions
5. **Save** - Logs results, updates cache
6. **Sleep** - Waits 15 minutes for next run

Total time per run: ~4-5 minutes (leaves 10-11 min idle between runs)

## Keeping It Running 24/7

### Option 1: Screen (Simple, any OS)

```bash
# Start in background with screen
screen -S naukri-bot python3 main_scheduler.py

# Detach: Ctrl+A, then D
# Reattach: screen -r naukri-bot
# Kill: screen -X -S naukri-bot quit
```

### Option 2: Systemd (Linux/Mac)

```bash
# Create service file
sudo nano /etc/systemd/system/naukri-bot.service
```

```ini
[Unit]
Description=Naukri Bot Scheduler
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/Users/koushik/Documents/naukri_ai_bot_automatic_job_apply
ExecStart=/usr/bin/python3 /Users/koushik/Documents/naukri_ai_bot_automatic_job_apply/main_scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable naukri-bot
sudo systemctl start naukri-bot

# Check status
sudo systemctl status naukri-bot

# View logs
sudo journalctl -u naukri-bot -f
```

### Option 3: Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily (Daily repeating every 15 minutes)
4. Action: Start program
5. Program: `python3`
6. Arguments: `main_scheduler.py`
7. Start in: `/path/to/project`

### Option 4: Cron (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add this line (runs script every 15 minutes, which internally manages its own schedule):
*/15 * * * * /usr/bin/python3 /path/to/scheduler.py >> /path/to/logs/cron.log 2>&1
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'apscheduler'"

```bash
pip install apscheduler
```

### Scheduler won't start

```bash
# Check logs
cat logs/scheduler.log

# Verify Python version
python3 --version

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

### Jobs not running

1. Check if scheduler process is alive: `ps aux | grep python3`
2. Check logs: `tail -f logs/scheduler.log`
3. Verify job interval: `grep "Interval:" logs/scheduler.log`

### High CPU/Memory Usage

- Adjust Ollama model size (qwen2-vl:4b is already small)
- Reduce job frequency: `--interval 30` (30 minutes instead of 15)
- Check for memory leaks in logs

## Performance Notes

### Typical Run Time

- Job execution: ~4-5 minutes per run
- Idle time: ~10-11 minutes between runs
- Total cycle: 15 minutes

### Resource Usage

- Memory: ~500-800 MB (Python + Ollama offloads LLM)
- CPU: High during run (~100%), idle otherwise
- Network: During execution only
- Disk: Logs ~1-5 MB per run (archive old logs)

### Optimization

- Run during low-traffic hours (2 AM - 6 AM)
- Monitor success rate in logs
- Archive logs monthly: `tar -czf logs-$(date +%Y%m).tar.gz logs/*.log`

## Statistics & Monitoring

### View Current Status

```python
# Create status_check.py
from main_scheduler import NaukriBotScheduler

scheduler = NaukriBotScheduler()
print(scheduler.get_status())
```

### Log Rotation

```bash
# Archive logs weekly
tar -czf logs/archive/$(date +scheduler_%Y%m%d.tar.gz) logs/scheduler.log
rm logs/scheduler.log
```

## Summary

| Task | Command |
|------|---------|
| Start | `python3 main_scheduler.py` |
| Stop | `Ctrl+C` or `kill <pid>` |
| Monitor | `tail -f logs/scheduler.log` |
| Custom interval | `python3 main_scheduler.py --interval 30` |
| Background (screen) | `screen -S bot python3 main_scheduler.py` |
| Systemd (Linux) | `sudo systemctl start naukri-bot` |

---

## Next Steps

1. ✅ Install apscheduler: `pip install apscheduler`
2. ✅ Start Ollama: `ollama serve`
3. ✅ Run scheduler: `python3 main_scheduler.py`
4. ✅ Monitor: `tail -f logs/scheduler.log`
5. ✅ Set up 24/7 with screen/systemd/Task Scheduler

**Enjoy automated job applications every 15 minutes!** 🚀
