# Cron + Statistics Setup

## ONE-TIME SETUP (5 minutes)

### 1. Install APScheduler
```bash
pip install apscheduler
```

### 2. Setup Cron (Runs Every 15 Minutes Automatically)
```bash
chmod +x setup_cron.sh
./setup_cron.sh
```

**Output:**
```
✅ Cron job installed successfully
   Job: */15 * * * * /bin/bash /path/run_bot_cron.sh
   Log: /path/logs/cron_scheduler.log
```

### 3. Start Ollama (keep running)
```bash
ollama serve
```

**That's it!** Bot now runs automatically every 15 minutes. ✅

---

## USAGE

### View Statistics Dashboard
```bash
open data/bot_report.html   # macOS
# or
xdg-open data/bot_report.html  # Linux
```

### View Cron Logs
```bash
tail -f logs/cron_scheduler.log
```

### Check If Cron Is Running
```bash
crontab -l
```

### Stop Cron Job
```bash
crontab -e
# Remove the line with: /run_bot_cron.sh
# Save and exit
```

---

## WHAT GETS TRACKED

**Per Run:**
- ✅ Jobs applied
- ✅ Jobs skipped
- ✅ Questions answered
- ✅ Questions unanswered
- ✅ External redirects (company URLs)
- ✅ LLM calls vs Decision tree calls
- ✅ Cache hits
- ✅ Success rate
- ✅ Execution time

**Statistics Levels:**
- Daily (last 24 hours)
- Weekly (last 7 days)
- Monthly (last 30 days)
- Yearly (last 365 days)
- All-time (total)

---

## FILE LOCATIONS

| File | Purpose |
|------|---------|
| `data/bot_statistics.json` | Raw statistics data |
| `data/bot_report.html` | Beautiful dashboard |
| `logs/cron_scheduler.log` | Cron execution logs |

---

## HOW IT WORKS

```
Every 15 minutes:
├─ Cron triggers run_bot_cron.sh
├─ Bot runs (4-5 minutes)
├─ Statistics recorded
├─ HTML report updated
└─ Done, wait 15 minutes
```

The bot keeps running automatically in the background, even after you close the terminal.

---

## DASHBOARD SHOWS

**Today's Stats:**
- Jobs Applied: 5
- Jobs Skipped: 25
- Questions Answered: 23
- External Redirects: 3

**Monthly Stats:**
- Applied this month: 150
- Skipped: 750
- Questions: 2,300
- Success rate: 85%

**Yearly Stats:**
- Total applications: 2,000
- Avg success rate: 82%
- Total redirects: 45

**All-Time Stats:**
- Total jobs applied: 2,000
- Total external redirects: 45
- Average run time: 4m 30s

---

## KEEP SYSTEM CLEAN

Archive old logs monthly:
```bash
tar -czf logs/archive_$(date +%Y%m).tar.gz logs/cron_scheduler.log
rm logs/cron_scheduler.log
```

---

**Bot now runs 24/7 automatically!** 🚀
