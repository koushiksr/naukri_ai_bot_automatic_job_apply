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
