#!/bin/bash
# Setup Cron Job for Naukri Bot - Runs every 4 hours in background

PROJECT_PATH="/Users/koushik/Documents/naukri_ai_bot_automatic_job_apply"
VENV_PATH="$PROJECT_PATH/venv"
LOG_FILE="$PROJECT_PATH/logs/cron_scheduler.log"

# Create logs directory
mkdir -p "$PROJECT_PATH/logs"

# Create cron job script
cat > "$PROJECT_PATH/scripts/run_bot_cron.sh" << 'EOF'
#!/bin/bash
PROJECT_PATH="/Users/koushik/Documents/naukri_ai_bot_automatic_job_apply"
VENV_PATH="$PROJECT_PATH/venv"
LOG_FILE="$PROJECT_PATH/logs/cron_scheduler.log"

export HEADLESS=True

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ----------------------------------" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Waking up for 4-hour background run" >> "$LOG_FILE"

# Network Check Failsafe
if ! ping -c 1 -W 5 8.8.8.8 > /dev/null 2>&1; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  Network offline. Aborting run." >> "$LOG_FILE"
    # Log network failure directly via Python
    "$VENV_PATH/bin/python" -c "
import sys
sys.path.insert(0, '$PROJECT_PATH/src')
from analytics.bot_statistics import BotStatistics
import time
stats = BotStatistics()
stats.record_run({
    'jobs_loaded': 0, 'jobs_filtered': 0, 'jobs_applied': 0, 'jobs_skipped': 0,
    'questions_total': 0, 'questions_answered': 0, 'questions_unanswered': 0,
    'external_redirects': 0, 'llm_calls': 0, 'decision_tree_calls': 0,
    'cache_hits': 0, 'errors': 1, 'error_list': ['Network Offline'],
    'duration': 0
})
"
    exit 1
fi

# Activate venv and run bot
cd "$PROJECT_PATH"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Network OK. Starting headless bot..." >> "$LOG_FILE"
"$VENV_PATH/bin/python" src/main.py >> "$LOG_FILE" 2>&1
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Run complete." >> "$LOG_FILE"
EOF

chmod +x "$PROJECT_PATH/scripts/run_bot_cron.sh"

# Add to crontab (runs every 4 hours at minute 0)
CRON_JOB="0 */4 * * * /bin/bash $PROJECT_PATH/scripts/run_bot_cron.sh"

# Clean old cron jobs for naukri
crontab -l 2>/dev/null | grep -v "run_bot_cron.sh" | crontab -

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "✅ 4-Hour Background Cron job installed successfully"
echo "   Job: $CRON_JOB"
echo "   Log: $LOG_FILE"
echo ""
echo "📊 The dashboard has been configured to log network failures."
echo "   Open: data/dashboard.html in your browser to view run history."
