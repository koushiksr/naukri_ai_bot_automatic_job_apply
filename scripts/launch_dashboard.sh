#!/bin/bash
# Launch dynamic dashboard server with auto-refresh

PROJECT_PATH="/Users/koushik/Documents/naukri_ai_bot_automatic_job_apply"
cd "$PROJECT_PATH"

echo "🚀 Generating dynamic dashboard..."

# Generate dashboard
python3 << 'EOF'
import sys
sys.path.insert(0, 'src')
from dynamic_dashboard import DynamicDashboard

dashboard = DynamicDashboard()
output = dashboard.generate_dynamic_dashboard()
print(f"✅ Dashboard ready: {output}")
EOF

# Open in browser
echo "📊 Opening dashboard..."
open data/dashboard.html

echo "✅ Dashboard running (auto-refreshes every 5 seconds)"
echo ""
echo "🔗 Dashboard URL: file://$(pwd)/data/dashboard.html"
echo ""
echo "📝 To update dashboard manually:"
echo "   python3 -c \"import sys; sys.path.insert(0, 'src'); from dynamic_dashboard import DynamicDashboard; DynamicDashboard().generate_dynamic_dashboard()\""
