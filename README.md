# Naukri AI Auto Apply

Automated job application bot for Naukri.com powered by Gemini AI — intelligently applies to jobs and answers screening questions automatically.

## Overview

**Naukri AI Auto Apply** is an intelligent job application automation tool that applies for jobs on Naukri.com and automatically answers employer screening questions using Google's Gemini AI API. 

Built with Playwright and Python, it intelligently:
- 🤖 **Automates** job applications at scale
- 🧠 **Uses AI** (Gemini Flash) to answer employer questions contextually
- 🎯 **Filters** jobs by experience level
- 📄 **Manages** resume uploads
- 📋 **Handles** all question types (radio, dropdowns, text inputs, textareas)
- 📊 **Tracks** application history and company redirects

Stop manually filling out job forms. Let AI do it for you.

## Features

- Automates job application on Naukri.com
- Skips already applied or expired job listings
- Answers questions during the application process using Gemini AI API
- Logs the count of successfully applied and failed job applications
- Handles multiple question types: radio buttons, dropdowns, text inputs, textareas
- Automatically detects and skips company site redirects
- Experience level matching and filtering

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.8+ installed on your local machine
- `playwright` library installed (`pip install playwright`)
- `google-generativeai` library for Gemini API
- Firefox browser installed
- Gemini AI API key ([Get API Key](https://ai.google.dev/gemini-api/docs/api-key))

## Installation

1. **Clone the repository:**

```bash
git clone https://github.com/koushiksr/naukri_ai_bot_automatic_job_apply.git
cd naukri_ai_bot_automatic_job_apply
```

2. **Create a virtual environment (optional but recommended):**

```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
playwright install firefox
```

4. **Configure your credentials:**

Copy `conf.example.py` to `conf.py` and update with your details:

```python
EMAIL = "your_naukri_email@example.com"
PASSWORD = "your_naukri_password"
API_KEY = "your_gemini_api_key"
OLLAMA_URL = "http://localhost:11434/api/generate"  # Optional
MODEL = "gemini-2.5-flash"
MY_EXPERIENCE = 2.5  # Your years of experience
```

5. **Prepare your resume:**

Place your resume as `Resume.pdf` in the project root directory.

## Usage

Run the automation script:

```bash
python apply_jobs.py
```

The script will:
1. Log into your Naukri account
2. Fetch recommended jobs
3. Filter by experience level
4. Apply to each job
5. Answer screening questions using Gemini AI
6. Track applications and company redirects

## Project Structure

```
naukri_ai_bot_automatic_job_apply/
├── apply_jobs.py          # Main automation script
├── gemini_api.py          # Gemini AI integration
├── conf.py                # Configuration (add to .gitignore)
├── rag_store.py           # RAG/knowledge base storage
├── storage.py             # Data persistence
├── company_sites.json     # Tracked company redirects
├── Resume.pdf             # Your resume (dummy provided)
└── requirements.txt       # Python dependencies
```

## How It Works

1. **Login** - Authenticates with your Naukri credentials
2. **Fetch Jobs** - Retrieves recommended job listings
3. **Filter** - Skips jobs requiring more experience than you have
4. **Apply** - Clicks the Apply button and waits for the chatbot
5. **Answer** - Uses Gemini AI to intelligently answer screening questions
6. **Track** - Logs successful and failed applications

## Important Notes

- The script uses Playwright for browser automation (headless=False by default)
- AI answers are contextual based on your profile and the question
- Questions are cached in `qa_store.json` to reduce API calls
- Company site redirects are tracked to avoid accidental external applications
- Ensure your Naukri account settings allow automation

## Disclaimer

Use this script responsibly and ensure compliance with Naukri.com's terms of service. Automating job applications may violate their policies and could result in account suspension or other consequences.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.
