
from playwright.sync_api import Page, Locator
from conf import EMAIL, PASSWORD, EXTERNAL_JOBS_FILE, RESUME_FILE
import json
import os
from datetime import datetime
from .common import log

MAX_ROUNDS = 20
BUFFER_MS = 3000



def js_click(el: Locator) -> bool:
    try:
        el.click(force=True, timeout=2000)
        return True
    except:
        try:
            el.evaluate("el => el.click()")
            return True
        except:
            return False


def wait(page: Page, ms: int = BUFFER_MS):
    page.wait_for_timeout(ms)


def get_page(chatbot) -> Page:
    """Get page from chatbot (handle both Locator and Page)"""
    if isinstance(chatbot, Page):
        return chatbot
    return chatbot.page


def save_external_job(job_data: dict):
    """Save job that redirects to external company site"""
    try:
        if os.path.exists(EXTERNAL_JOBS_FILE):
            with open(EXTERNAL_JOBS_FILE, 'r') as f:
                jobs = json.load(f)
        else:
            jobs = []
        
        jobs.append(job_data)
        
        with open(EXTERNAL_JOBS_FILE, 'w') as f:
            json.dump(jobs, f, indent=2)
        
        log("💾", f"Saved external job: {job_data.get('role', 'Unknown')}")
    except Exception as e:
        log("❌", f"Save error: {e}")


# ═══════════════════════════════════════════════════════════════
# LOGIN
# ═══════════════════════════════════════════════════════════════

def login(page: Page):
    log("🔐", "Logging in...")
    page.goto("https://www.naukri.com/nlogin/login")
    wait(page, 3000)
    page.locator("#usernameField").fill(EMAIL)
    page.locator("#passwordField").fill(PASSWORD)
    wait(page, 500)
    js_click(page.locator("button[type='submit']").first)
    try:
        page.wait_for_url(lambda url: "nlogin" not in url, timeout=15000)
    except:
        pass
    wait(page, 4000)
    log("✅", "Logged in")


# ═══════════════════════════════════════════════════════════════
# RESUME UPDATE
# ═══════════════════════════════════════════════════════════════

def update_resume_if_needed(page: Page):
    """Update profile by re-uploading resume, at most once per day."""
    last_update_file = "data/last_resume_update.txt"
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    if os.path.exists(last_update_file):
        with open(last_update_file, "r") as f:
            last_update = f.read().strip()
        if last_update == today_str:
            log("📄", f"Resume already updated today ({last_update}). Skipping profile bump.")
            return

    if not os.path.exists(RESUME_FILE):
        log("❌", f"Resume not found at {RESUME_FILE}")
        return

    log("🌐", "Opening profile page to bump resume...")
    page.goto("https://www.naukri.com/mnjuser/profile", wait_until="domcontentloaded")
    wait(page, 5000)

    try:
        file_input = page.locator("input[type='file']")
        if file_input.count() == 0:
            log("❌", "Resume file input not found on profile page.")
        else:
            log("📄", "Uploading resume...")
            file_input.first.set_input_files(RESUME_FILE)
            wait(page, 8000)
            
            with open(last_update_file, "w") as f:
                f.write(today_str)
            log("✅", "Resume updated successfully!")
    except Exception as e:
        log("❌", f"Failed to update resume: {e}")
