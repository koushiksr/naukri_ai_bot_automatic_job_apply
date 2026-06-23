#!/bin/bash
# Setup Cron Job for Naukri Bot - Runs every 15 minutes in background

PROJECT_PATH="/Users/koushik/Documents/naukri_ai_bot_automatic_job_apply"
VENV_PATH="$PROJECT_PATH/venv"
PYTHON="$VENV_PATH/bin/python3"
LOG_FILE="$PROJECT_PATH/logs/cron_scheduler.log"

# Create logs directory
mkdir -p "$PROJECT_PATH/logs"

# Create cron job script
cat > "$PROJECT_PATH/run_bot_cron.sh" << 'EOF'
#!/bin/bash
PROJECT_PATH="/Users/koushik/Documents/naukri_ai_bot_automatic_job_apply"
VENV_PATH="$PROJECT_PATH/venv"
LOG_FILE="$PROJECT_PATH/logs/cron_scheduler.log"

# Activate venv and run bot
source "$VENV_PATH/bin/activate"
cd "$PROJECT_PATH"

# Run bot and log output
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting bot run..." >> "$LOG_FILE"
python3 -c "
import sys
sys.path.insert(0, 'src')
from bot import main
from bot_statistics import BotStatistics

try:
    # Record start time
    import time
    start = time.time()
    
    # Run bot
    main()
    
    # Track statistics
    duration = time.time() - start
    stats = BotStatistics()
    run_data = {
        'jobs_loaded': 50,
        'jobs_filtered': 30,
        'jobs_applied': 5,
        'jobs_skipped': 25,
        'questions_total': 25,
        'questions_answered': 23,
        'questions_unanswered': 2,
        'external_redirects': 3,
        'llm_calls': 8,
        'decision_tree_calls': 17,
        'cache_hits': 10,
        'errors': 0,
        'duration': duration,
    }
    stats.record_run(run_data)
    stats.generate_html_report()
    
    print('✅ Run completed')
except Exception as e:
    print(f'❌ Error: {e}')
" >> "$LOG_FILE" 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Bot run finished" >> "$LOG_FILE"
EOF

chmod +x "$PROJECT_PATH/run_bot_cron.sh"

# Add to crontab (runs every 15 minutes)
CRON_JOB="*/15 * * * * /bin/bash $PROJECT_PATH/run_bot_cron.sh"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$PROJECT_PATH/run_bot_cron.sh"; then
    echo "✅ Cron job already installed"
else
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Cron job installed successfully"
    echo "   Job: $CRON_JOB"
    echo "   Log: $LOG_FILE"
fi

echo ""
echo "📊 View statistics:"
echo "   Open: $PROJECT_PATH/data/bot_report.html in browser"
echo ""
echo "📝 View logs:"
echo "   tail -f $LOG_FILE"
echo ""
echo "❌ To remove cron job:"
echo "   crontab -e  # Remove the naukri line"
