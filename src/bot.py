"""
Naukri Bot v3 - Using Strong Job Utilities API
"""

import re
import json
import os
from datetime import datetime
from playwright.sync_api import sync_playwright, Page, Locator
from gemini_api_v2 import answer_question
from job_utils import JobList, JobDetails
from conf import EMAIL, PASSWORD, MY_EXPERIENCE, EXTERNAL_JOBS_FILE, BOT_LOG_FILE

MAX_ROUNDS = 20
BUFFER_MS = 1000


def log(icon: str, msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {icon}  {msg}"
    print(line)
    try:
        os.makedirs(os.path.dirname(BOT_LOG_FILE), exist_ok=True)
        with open(BOT_LOG_FILE, "a") as f:
            f.write(line + "\n")
    except:
        pass


def js_click(el: Locator) -> bool:
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
# STATUS CHECKS
# ═══════════════════════════════════════════════════════════════

def is_applied(page: Page) -> bool:
    sels = [
        "text=/successfully applied/i",
        "text=/application submitted/i",
        "text=/applied successfully/i",
    ]
    return any(page.locator(sel).count() > 0 for sel in sels)


def find_apply_btn(page: Page) -> Locator | None:
    if is_applied(page):
        return None
    try:
        btn = page.locator("button:has-text('Apply')").first
        btn.wait_for(state="visible", timeout=2000)
        return btn
    except:
        return None


# ═══════════════════════════════════════════════════════════════
# EXTRACT JOB DETAILS
# ═══════════════════════════════════════════════════════════════

def extract_job_details(job_page: Page) -> dict:
    """Extract job role, experience, JD from page"""
    try:
        role = ""
        try:
            role = job_page.locator("h1, .job-title, [class*='title']").first.inner_text().strip()
        except:
            pass
        
        exp = ""
        try:
            exp_elem = job_page.locator("span[title*='Yrs'], [class*='experience']").first.inner_text().strip()
            exp = exp_elem
        except:
            pass
        
        jd = ""
        try:
            jd_elem = job_page.locator("[class*='jd'], [class*='description'], .job-description").first.inner_text().strip()
            jd = jd_elem[:500]
        except:
            pass
        
        return {
            "role": role,
            "experience": exp,
            "jd": jd,
            "url": job_page.url,
            "timestamp": datetime.now().isoformat(),
            "company": "",
        }
    except Exception as e:
        log("⚠️", f"Extract error: {e}")
        return {"url": job_page.url, "timestamp": datetime.now().isoformat()}


# ═══════════════════════════════════════════════════════════════
# CHATBOT DETECTION & ANSWERING
# ═══════════════════════════════════════════════════════════════

def get_chatbot(page: Page) -> Locator | Page:
    for sel in ["._chatBotContainer", "[class*='chatBot']", "[class*='chatbot']"]:
        loc = page.locator(sel)
        if loc.count() > 0:
            return loc.first
    return page


def get_question(chatbot) -> str:
    try:
        msgs = chatbot.locator("li.botItem span").all_text_contents()
        if msgs:
            return msgs[-1].strip()
    except:
        pass
    try:
        msgs = chatbot.locator("[class*='botMsg'], [class*='bot-msg'], [class*='botItem']").all_text_contents()
        clean = [m.strip() for m in msgs if m.strip()]
        if clean:
            return clean[-1]
    except:
        pass
    return ""


def has_input(chatbot) -> bool:
    """Check if there's unanswered input"""
    try:
        radios = chatbot.locator("div.ssrc__radio-btn-container, div[class*='radio-btn']")
        if radios.count() > 0:
            checked = chatbot.locator(
                "div.ssrc__radio-btn-container input:checked, div[class*='radio-btn'] input:checked"
            )
            if checked.count() == 0:
                return True

        dropdown = chatbot.locator("select")
        if dropdown.count() > 0:
            val = dropdown.first.input_value()
            if not val or val.lower() in ("", "select", "--"):
                return True

        inp = chatbot.locator("input[type='text']:visible, input[type='number']:visible, textarea:visible")
        if inp.count() > 0:
            val = inp.first.input_value()
            if not val.strip():
                return True

        box = chatbot.locator("div[contenteditable='true']:visible")
        if box.count() > 0:
            txt = box.first.inner_text()
            if not txt.strip():
                return True
    except:
        pass
    return False


def answer_turn(chatbot, q: str) -> bool:
    """Answer ONE input element with AI help"""
    page = get_page(chatbot)
    
    # ── RADIO ──
    radios = chatbot.locator("div.ssrc__radio-btn-container, div[class*='radio-btn']")
    if radios.count() > 0:
        opts = [o.strip() for o in radios.all_text_contents() if o.strip()]
        if opts:
            log("🔘", f"Radio: {opts}")
            
            if "experience" in q.lower():
                idx = 0
                for i, opt in enumerate(opts):
                    nums = [int(n) for n in re.findall(r"\d+", opt)]
                    if len(nums) == 2:
                        start, end = nums
                        if start <= MY_EXPERIENCE <= end:
                            idx = i
                            break
                    elif nums and MY_EXPERIENCE >= nums[0]:
                        idx = i
            else:
                try:
                    ai_ans = answer_question(q)
                    log("🤖", f"AI: {ai_ans[:50]}")
                    
                    idx = 0
                    for i, opt in enumerate(opts):
                        if ai_ans.lower() in opt.lower():
                            idx = i
                            break
                except Exception as e:
                    log("❌", f"AI error: {e}")
                    idx = 0
            
            container = radios.nth(idx)
            label = container.locator("label, input[type='radio'], input[type='checkbox']")
            target = label.first if label.count() > 0 else container
            ok = js_click(target)
            log("🖱️", f"Clicked radio[{idx}]" + (" ✅" if ok else " ❌"))
            if ok:
                wait(page, BUFFER_MS)
            return ok

    # ── DROPDOWN ──
    dropdown = chatbot.locator("select")
    if dropdown.count() > 0:
        opts = [o.strip() for o in dropdown.first.locator("option").all_text_contents()]
        opts = [o for o in opts if o and o.lower() not in ("select", "--")]
        if opts:
            log("📋", f"Dropdown: {opts}")
            
            try:
                ai_ans = answer_question(q)
                idx = 0
                for i, opt in enumerate(opts):
                    if ai_ans.lower() in opt.lower():
                        idx = i
                        break
            except:
                idx = 0
            
            try:
                dropdown.first.select_option(label=opts[idx])
                log("📋", f"Selected ✅")
                wait(page, BUFFER_MS)
                return True
            except Exception as e:
                log("❌", f"Dropdown error: {e}")

    # ── TEXT BOX ──
    box = chatbot.locator("div[contenteditable='true']")
    if box.count() > 0:
        try:
            ans = answer_question(q)
        except:
            ans = "Open to discuss"
        
        js_click(box.first)
        box.first.evaluate("el => { el.focus(); el.innerHTML = ''; }")
        box.first.type(ans, delay=20)
        log("✏️", f"Typed ✅")
        wait(page, 400)
        box.first.press("Enter")
        wait(page, BUFFER_MS)
        return True

    # ── TEXT INPUT ──
    inp = chatbot.locator("input[type='text'], input[type='number'], textarea")
    if inp.count() > 0:
        try:
            ans = answer_question(q)
        except:
            ans = "As per discussion"
        
        inp.first.fill(ans)
        inp.first.press("Enter")
        log("✏️", f"Typed ✅")
        wait(page, BUFFER_MS)
        return True

    return False


# ═══════════════════════════════════════════════════════════════
# APPLY PROCESS
# ═══════════════════════════════════════════════════════════════

def apply_job(job_page: Page):
    """Apply to job with question handling"""
    
    btn = find_apply_btn(job_page)
    if not btn:
        log("❌", "No Apply button")
        return False

    btn.scroll_into_view_if_needed()
    js_click(btn)
    log("🖱️", "Clicked Apply")
    wait(job_page, 3000)

    chatbot = get_chatbot(job_page)
    prev_q = ""
    answered = 0

    for r in range(MAX_ROUNDS):
        has_inp = has_input(chatbot)
        q = get_question(chatbot)

        if has_inp:
            q_use = q if q else prev_q
            log("❓", f"Q: {q_use[:60]}")
            
            if answer_turn(chatbot, q_use):
                answered += 1
                log("✅", f"Answered ({answered})")
                prev_q = q or prev_q
                wait(get_page(chatbot), BUFFER_MS)
                continue
            else:
                log("⚠️", "Answer failed")
                wait(get_page(chatbot), 1500)
                continue

        if not q or q == prev_q:
            log("⏳", "Waiting...")
            wait(get_page(chatbot), 2000)

            has_inp = has_input(chatbot)
            q = get_question(chatbot)

            if has_inp or (q and q != prev_q):
                continue

            if is_applied(job_page):
                log("✅", "APPLIED!")
                wait(get_page(chatbot), 3000)
                return True

            found_button = False
            for btn_text in ["Next", "Proceed", "Continue"]:
                try:
                    nxt = chatbot.locator(f"button:text-is('{btn_text}')").first
                    nxt.wait_for(state="visible", timeout=500)
                    js_click(nxt)
                    log("🖱️", f"Clicked {btn_text}")
                    wait(get_page(chatbot), 2000)
                    found_button = True
                    break
                except:
                    pass

            if not found_button and answered >= 1:
                for btn_text in ["Save", "Submit", "Done", "Finish"]:
                    try:
                        save = chatbot.locator(f"button:text-is('{btn_text}')").first
                        save.wait_for(state="visible", timeout=500)
                        js_click(save)
                        log("🖱️", f"Clicked {btn_text}")
                        wait(get_page(chatbot), 3000)
                        return True
                    except:
                        pass

            wait(get_page(chatbot), 2000)
            continue

        log("💬", f"New Q: {q[:60]}")
        prev_q = q
        wait(get_page(chatbot), 1000)
        continue

    log("⚠️", "Max rounds reached")
    for btn_text in ["Save", "Submit", "Done", "Finish"]:
        try:
            save = chatbot.locator(f"button:text-is('{btn_text}')").first
            save.wait_for(state="visible", timeout=500)
            js_click(save)
            log("🖱️", f"Final {btn_text}")
            wait(get_page(chatbot), 3000)
            return True
        except:
            pass

    return False


# ═══════════════════════════════════════════════════════════════
# MAIN - USING JOB UTILITIES
# ═══════════════════════════════════════════════════════════════

try:
    os.makedirs(os.path.dirname(BOT_LOG_FILE), exist_ok=True)
    if os.path.exists(BOT_LOG_FILE):
        os.remove(BOT_LOG_FILE)
except:
    pass

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    login(page)

    log("🌐", "Loading jobs...")
    page.goto("https://www.naukri.com/mnjuser/recommendedjobs")
    wait(page, 6000)

    # Initialize job utilities
    job_list = JobList(page)
    total_jobs = job_list.count()
    log("📌", f"Found {total_jobs} jobs")

    # Print all jobs summary
    job_list.print_all_jobs(limit=10)
    log("", "")

    # Filter jobs using strong utilities
    log("🔍", "Filtering jobs...")
    
    # Example: Get matching experience
    matching_jobs = job_list.filter_by_experience(MY_EXPERIENCE)
    log("📊", f"Jobs matching {MY_EXPERIENCE} years: {len(matching_jobs)}")
    
    # Example: Get Python jobs (must contain)
    python_jobs = job_list.filter_by_keywords(["python", "django"])
    log("📊", f"Python/Django jobs: {len(python_jobs)}")
    
    # Example: Exclude certain keywords
    no_java = job_list.filter_by_keywords(["java"], must_contain=False)
    log("📊", f"Jobs without Java: {len(no_java)}")
    
    # Combined filter
    valid_jobs = job_list.filter_combined(
        user_experience=MY_EXPERIENCE,
        must_have_keywords=["python"],
        must_not_have_keywords=["java"],
        urgent_only=False
    )
    log("📊", f"Valid jobs (Python, no Java): {len(valid_jobs)}")
    log("", "")

    applied = 0
    external = 0
    skipped = 0

    # Apply to first 5 jobs
    for job_idx in valid_jobs[:5]:
        log("\n" + "="*60, "")
        log("🔎", f"Processing job index {job_idx}")
        
        # Get job details using utilities
        job = job_list.get_at_index(job_idx)
        
        # Print job summary
        job_list.print_job_summary(job_idx)
        
        job_page = None

        try:
            # Click with conditions
            clicked = job_list.click_with_conditions(
                job_idx,
                must_contain=["python"],
                must_not_contain=["java"]
            )
            
            if not clicked:
                log("⏭️", "Skipped (conditions not met)")
                skipped += 1
                continue

            # Open in new tab
            with context.expect_page() as new_tab:
                job_list.jobs_loc.nth(job_idx).evaluate("el => el.click()")
            
            job_page = new_tab.value
            job_page.wait_for_load_state("domcontentloaded")
            wait(job_page, 3000)

            # Check for external redirect
            if "naukri.com" not in job_page.url:
                log("🏢", "External company site!")
                
                job_data = extract_job_details(job_page)
                job_data["company"] = job.company
                job_data["role"] = job.role
                save_external_job(job_data)
                external += 1
                
                job_page.close()
                wait(page, 1000)
                continue

            # Apply
            if apply_job(job_page):
                applied += 1
                log("🎉", f"APPLIED! ({applied})")
            else:
                log("❌", "Failed")

        except Exception as e:
            log("💥", f"Error: {e}")

        finally:
            if job_page and not job_page.is_closed():
                job_page.close()

    log("\n" + "="*60, "")
    log("🏁", f"DONE - Applied: {applied} | External: {external} | Skipped: {skipped}")
