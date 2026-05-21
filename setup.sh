#!/bin/bash

# Naukri Bot Setup Script

echo "🔧 Setting up Naukri Job Application Bot..."

# Check Python version
python3 --version > /dev/null 2>&1 || { echo "❌ Python 3 not found"; exit 1; }

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Install Playwright
echo "🌐 Installing Playwright browsers..."
playwright install chromium

# Create directories
echo "📂 Creating directories..."
mkdir -p data output logs

# Create example config
echo "⚙️  Creating config template..."
cat > src/conf.py.example << 'EOF'
# Naukri Credentials
EMAIL = "your_email@example.com"
PASSWORD = "your_password"

# Gemini API Configuration
API_KEY = "your_gemini_api_key"
MODEL = "gemini-2.5-flash"

# Application Settings
MY_EXPERIENCE = 2.5
QA_FILE = "data/qa_store.json"
RESUME_FILE = "data/Resume.pdf"

# Automation Settings
HEADLESS = False
BROWSER_TIMEOUT = 60000
WAIT_TIME = 2

# File locations
EXTERNAL_JOBS_FILE = "output/external_jobs.json"
BOT_LOG_FILE = "logs/bot.log"
EOF

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Copy your resume to: data/Resume.pdf"
echo "  2. Edit src/conf.py with your credentials:"
echo "     cp src/conf.py.example src/conf.py"
echo "     # Edit EMAIL, PASSWORD, API_KEY"
echo "  3. Run the bot:"
echo "     source venv/bin/activate"
echo "     python3 src/bot.py"
echo ""
