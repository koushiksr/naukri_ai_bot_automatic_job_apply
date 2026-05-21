# 🤖 Naukri Automated Job Application Bot

AI-powered automated job application bot for Naukri.com with intelligent question answering using Google Gemini API.

## 📂 Project Structure

```
naukri_ai_bot_automatic_job_apply/
├── src/                         # Source code
│   ├── bot.py                  # Main bot logic (START HERE)
│   ├── conf.py                 # Configuration & credentials
│   ├── gemini_api_v2.py       # Gemini API wrapper
│   ├── question_analyzer.py   # Question type detection
│   └── resume_analyzer.py     # Resume parsing
├── data/                        # Data files
│   ├── Resume.pdf             # Your resume
│   ├── qa_store.json          # Cached Q&A pairs
│   └── company_sites.json     # Tracked redirects
├── output/                      # Bot output
│   └── external_jobs.json     # Jobs redirected to company sites
├── logs/                        # Application logs
│   └── bot.log               # Detailed execution log
├── main.py                      # Entry point
├── setup.sh                     # Setup script
└── README.md                    # This file
```

## 🚀 Quick Start

### Step 1: Setup

```bash
chmod +x setup.sh
./setup.sh
```

This will:
- Create virtual environment
- Install dependencies
- Create config template
- Setup directories

### Step 2: Configure

```bash
# Copy config template
cp src/conf.py.example src/conf.py

# Edit with your credentials
nano src/conf.py
```

Required settings:
```python
EMAIL = "your_naukri_email@example.com"
PASSWORD = "your_password"
API_KEY = "your_gemini_api_key"
MY_EXPERIENCE = 2.5  # Your years of experience
```

### Step 3: Add Resume

Place your resume at `data/Resume.pdf` (PDF format)

### Step 4: Run Bot

```bash
source venv/bin/activate
python3 src/bot.py
```

## ✨ Features

### ✅ Core Functionality
- **Auto Login** - Handles Naukri authentication
- **Job Discovery** - Finds recommended jobs
- **Smart Filtering** - Skips jobs above your experience level
- **Question Detection** - Identifies all question types

### ✅ Question Types Handled
- Radio buttons / Checkboxes
- Dropdowns / Select fields
- Text inputs
- Text areas
- Contenteditable fields

### ✅ Intelligent Answering
- **AI-Powered** - Uses Gemini to generate contextual answers
- **Experience Matching** - Smart selection for experience range questions
- **Caching** - Stores answers for reuse (faster subsequent runs)
- **Pattern Recognition** - Learns from previous applications

### ✅ External Site Handling
- **Auto Detection** - Detects redirects to company websites
- **Smart Save** - Saves job details (role, company, URL, JD)
- **Clean Exit** - Closes tab and continues to next job
- **Organized Output** - Results in `output/external_jobs.json`

### ✅ Logging & Transparency
- **Detailed Logs** - Saves to `logs/bot.log`
- **Console Output** - Real-time status with emoji indicators
- **Error Tracking** - Captures all issues for debugging

## 📊 Output Files

### Jobs Applied
Success logged to console with job count

### External Jobs (output/external_jobs.json)
```json
[
  {
    "company": "Tech Company Inc",
    "role": "Senior Software Engineer",
    "experience": "3-5 Yrs",
    "jd": "Job description excerpt...",
    "url": "https://techcompany.com/apply/job123",
    "timestamp": "2024-05-21T20:30:45.123456"
  }
]
```

### Q&A Cache (data/qa_store.json)
Stores answered questions for faster future runs

### Logs (logs/bot.log)
```
[20:30:45] 🔐  Logging in...
[20:30:49] ✅  Logged in
[20:30:49] 🌐  Loading jobs...
[20:30:55] 📌  Found 52 jobs
[20:30:55] 🔎  Job 1/52
[20:30:55] 📍  TechCorp - Senior Engineer
[20:31:00] 🖱️  Clicked Apply
[20:31:03] 🔘  Radio: ['Yes', 'No', 'Maybe']
[20:31:03] 🤖  AI: Yes, I am
[20:31:03] 🖱️  Clicked radio[0] ✅
```

## ⚙️ Configuration (src/conf.py)

```python
# REQUIRED
EMAIL              # Naukri login email
PASSWORD           # Naukri login password
API_KEY            # Google Gemini API key
MY_EXPERIENCE      # Years of experience (float)

# Optional
HEADLESS           # Run without browser GUI (False = show browser)
BROWSER_TIMEOUT    # Page load timeout in milliseconds
WAIT_TIME          # Wait between actions in seconds

# File Paths
QA_FILE            # Path to Q&A cache
RESUME_FILE        # Path to your resume
EXTERNAL_JOBS_FILE # Path to save external jobs
BOT_LOG_FILE       # Path to save logs
```

## 🔐 Security Notes

⚠️ **Important**
- Never commit `src/conf.py` with real credentials
- Add to `.gitignore` (already done)
- Use environment variables for sensitive data
- Keep API keys private
- Logs may contain partial credential info

### Secure Setup (Optional)

Use `.env` file instead:
```bash
echo "NAUKRI_EMAIL=your_email@example.com" > .env.local
echo "NAUKRI_PASSWORD=your_password" >> .env.local
echo "GEMINI_API_KEY=your_api_key" >> .env.local
chmod 600 .env.local
```

Then modify `src/conf.py` to load from `.env.local`

## 🎯 Console Indicators

| Icon | Meaning |
|------|---------|
| 🔐 | Login activity |
| ✅ | Success |
| ❌ | Error |
| 🌐 | Navigation |
| 📌 | Job discovery |
| 🔎 | Job processing |
| ❓ | Question detected |
| 🤖 | AI response |
| 🖱️ | Click action |
| 🏢 | External company site |
| 💾 | Data saved |
| 🎉 | Application submitted |
| ⏭️ | Job skipped |

## 🔧 Troubleshooting

### Browser Not Opening
```
Set HEADLESS = False in src/conf.py
Check: playwright install chromium
```

### Login Fails
```
Verify EMAIL and PASSWORD in src/conf.py
Check if Naukri changed login page
```

### Questions Not Answered
```
Check logs/bot.log for errors
Verify GEMINI_API_KEY is valid
Test internet connection
```

### External Jobs Not Saving
```
Verify output/ directory exists
Check disk space
Review file permissions
```

### Slow Performance
```
Set HEADLESS = True for faster runs
Reduce MY_EXPERIENCE to match more jobs
Clear data/qa_store.json and rebuild cache
```

## 📦 Dependencies

See `requirements.txt`:
- `playwright` - Browser automation
- `google-generativeai` - Gemini API
- `python-dotenv` - Environment variables

## 📋 Workflow

```
1. Login to Naukri
   ↓
2. Load recommended jobs page
   ↓
3. Filter jobs (skip if exp > YOUR_EXP)
   ↓
4. For each job:
   ├─ Open job in new tab
   ├─ Check if external company site
   │  ├─ YES → Save details & skip
   │  └─ NO → Continue
   ├─ Click Apply button
   ├─ For each question:
   │  ├─ Detect question type
   │  ├─ Generate AI response
   │  └─ Fill & submit
   ├─ Save application when complete
   └─ Move to next job
   ↓
5. Print summary (applied count, external count)
```

## 🎓 How It Works

### Question Detection
- Analyzes DOM to identify input type
- Extracts options/placeholder text
- Caches for future reference

### AI Answering
- Sends question to Gemini API
- Context includes your experience & skills
- Generates contextual response
- Matches response to available options

### Experience Matching
- Parses "X-Y years" format
- Selects closest match to MY_EXPERIENCE
- Special handling for "3-5 years" vs "5+ years"

### External Detection
- Monitors URL changes after "Apply" click
- Identifies redirects to non-Naukri domains
- Saves job details before closing tab

## 💡 Tips

1. **First Run** - Slower due to Q&A cache building
2. **Subsequent Runs** - Faster with cached answers
3. **Monitor Console** - Watch for 🤖 AI responses
4. **Check Logs** - Review `logs/bot.log` for details
5. **Test Questions** - Try with 1-2 jobs first
6. **Adjust Experience** - Lower MY_EXPERIENCE to test more

## 🐛 Debugging

Enable detailed output:
```bash
python3 -u src/bot.py 2>&1 | tee debug.log
```

Check logs:
```bash
tail -f logs/bot.log
```

## 📞 Support

1. Check `logs/bot.log` for error details
2. Verify all config settings in `src/conf.py`
3. Ensure resume at `data/Resume.pdf`
4. Test with `MY_EXPERIENCE = 1` to match more jobs
5. Review console emoji indicators

## 📄 License

Private Project

## ✨ Version

Bot v3.0 - Clean, organized, production-ready
