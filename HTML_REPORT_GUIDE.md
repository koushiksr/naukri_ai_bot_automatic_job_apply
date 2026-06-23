# HTML STATISTICS REPORT - QUICK GUIDE

## ✅ REPORT IS READY

**Location:** `data/bot_report.html`

### View Dashboard (2 Ways)

**Option 1: Auto-open script**
```bash
./view_stats.sh
```

**Option 2: Manual open**
```bash
open data/bot_report.html
```

---

## 📊 WHAT THE DASHBOARD SHOWS

### Today's Metrics
- Jobs Applied
- Jobs Skipped
- Questions Answered
- External Redirects

### This Month
- Total Applied
- Total Skipped
- Total Questions
- Success Rate

### This Year
- Annual Applied
- Annual Skipped
- Total Runs
- Annual Redirects

### All-Time Stats
- Total Jobs Applied
- Total Skipped
- Total Questions Answered
- Total External Redirects

### Detailed Table (Today)
- Total Runs
- Jobs Loaded
- Jobs Filtered
- Jobs Applied
- Jobs Skipped
- Questions Answered
- Questions Unanswered
- LLM Calls
- Decision Tree Calls
- Cache Hits
- Success Rate

### External URLs
- List of all company redirects

---

## 📝 STATISTICS STORED

**File:** `data/bot_statistics.json`

**Tracks:**
```json
{
  "daily": {
    "2026-05-22": { stats... }
  },
  "weekly": {
    "2026-W20": { stats... }
  },
  "monthly": {
    "2026-05": { stats... }
  },
  "yearly": {
    "2026": { stats... }
  },
  "all_time": { stats... }
}
```

---

## 🤖 HOW BOT UPDATES STATS

Each time the bot runs (every 15 minutes with cron):

1. **Collects metrics:**
   - Jobs loaded/filtered/applied/skipped
   - Questions answered/unanswered
   - External redirects
   - LLM calls vs decision tree calls
   - Cache hits
   - Execution time

2. **Records in JSON:**
   - Adds to today's stats
   - Adds to this week's stats
   - Adds to this month's stats
   - Adds to this year's stats
   - Adds to all-time stats

3. **Regenerates HTML:**
   - Updates `bot_report.html`
   - Shows fresh data
   - Pretty dashboard with colors

---

## 🔄 AUTO-REFRESH

After each 15-minute cron run, stats update automatically in `bot_report.html`.

View dashboard anytime:
```bash
./view_stats.sh
```

---

## 📈 EXAMPLE STATS

After 1 week of 15-minute runs (96 runs):
```
Daily:     5 jobs applied, 25 skipped
Weekly:   560 jobs applied, 2400 skipped
Monthly: 2400 jobs applied, 10800 skipped
Yearly:  2400 jobs applied, 10800 skipped
All-Time: 2400 jobs applied, 10800 skipped
```

---

## 🎯 YOUR FIRST REPORT

Just generated with sample data:
- **Created:** today
- **Jobs Applied:** 5
- **Jobs Skipped:** 25
- **Questions Answered:** 23
- **External Redirects:** 3

Now run the real bot with cron, and stats will accumulate automatically!

---

**Open report now:** 
```bash
./view_stats.sh
```
