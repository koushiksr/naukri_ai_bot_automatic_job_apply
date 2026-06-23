#!/bin/bash
# Auto-generate and open HTML statistics report

PROJECT_PATH="/Users/koushik/Documents/naukri_ai_bot_automatic_job_apply"
REPORT_FILE="$PROJECT_PATH/data/bot_report.html"

cd "$PROJECT_PATH"

# Generate latest report
python3 << 'PYTHON_EOF'
import sys
sys.path.insert(0, 'src')
from bot_statistics import BotStatistics

stats = BotStatistics()
report_file = stats.generate_html_report()
print(f"✅ Report updated: {report_file}")
PYTHON_EOF

# Open in browser
if [ -f "$REPORT_FILE" ]; then
    echo "📊 Opening dashboard..."
    open "$REPORT_FILE"  # macOS
    # For Linux: xdg-open "$REPORT_FILE"
    # For Windows: start "$REPORT_FILE"
else
    echo "❌ Report file not found: $REPORT_FILE"
fi
