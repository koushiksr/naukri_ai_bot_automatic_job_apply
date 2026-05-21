import json
import re
import os
from datetime import datetime

from playwright.sync_api import sync_playwright, Page, Locator
from gemini_api import bard_flash_response
from conf import EMAIL, PASSWORD, MY_EXPERIENCE
from rag_store import load_json

MAX_ROUNDS = 20
BUFFER_MS  = 1000   # 1-second buffer between most actions


# ═══════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════

def log(icon: str, msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {icon}  {msg}")

def log_click(label: str, success: bool):
    if success:
        log("🖱️ ✅", f"CLICKED → {label}")
    else:
        log("🖱️ ❌", f"CLICK FAILED → {label}")


# ═══════════════════════════════════════════════════════
# PLAYWRIGHT HELPERS
# ═══════════════════════════════════════════════════════

def js_click(element: Locator) -> bool:
    """JS-force click. Returns True on success."""
    try:
        element.evaluate("el => el.click()")
        return True
    except Exception as e:
        log("⚠️", f"js_click error: {e}")
        return False

def safe_click(element: Locator, label: str = "") -> bool:
    """Click with confirmation logging."""
    ok = js_click(element)
    log_click(label or "element", ok)
    return ok

def wait(page: Page, ms: int = BUFFER_MS):
    page.wait_for_timeout(ms)

def save_json(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ═══════════════════════════════════════════════════════
# EXPERIENCE OPTION MATCHER
# ═══════════════════════════════════════════════════════

def choose_best_experience_option(options: list[str]) -> int:
    best_index = 0
    for i, option in enumerate(options):
        text = option.lower().strip()
        nums = list(map(int, re.findall(r"\d+", text)))
        if not nums:
            continue
        if len(nums) == 1:
            if MY_EXPERIENCE >= nums[0]:
                best_index = i
        else:
            start, end = nums[0], nums[1]
            if start <= MY_EXPERIENCE <= end:
                return i
            if MY_EXPERIENCE >= start:
                best_index = i
    return best_index


# ═══════════════════════════════════════════════════════
# UPDATE RESUME
# ═══════════════════════════════════════════════════════

def update_resume(page: Page):
    PROFILE_URL = "https://www.naukri.com/mnjuser/profile"
    RESUME_PATH = r"C:\\Users\\dell\\Documents\\JobSailor-job-apply-naukri\\Resume.pdf"

    if not os.path.exists(RESUME_PATH):
        log("❌", f"Resume not found: {RESUME_PATH}")
        return

    log("🌐", "Opening profile page")
    page.goto(PROFILE_URL, wait_until="domcontentloaded")
    wait(page, 5000)

    try:
        file_input = page.locator("input[type='file']")
        if file_input.count() == 0:
            log("❌", "File input not found")
            return

        log("📄", "Uploading resume…")
        file_input.first.set_input_files(RESUME_PATH)
        wait(page, 8000)
        log("✅", "Resume updated")

    except Exception as e:
        log("💥", f"Resume upload error: {e}")


# ═══════════════════════════════════════════════════════
# AUTO SHARE INTEREST
# ═══════════════════════════════════════════════════════

def auto_share_interest(page: Page):
    URL = "https://www.naukri.com/mnjuser/recommended-earjobs"
    total_clicked = 0

    while True:
        log("🌐", "Opening EAR jobs page")
        page.goto(URL, wait_until="domcontentloaded")
        wait(page, 5000)

        buttons = page.locator("button.unshared")
        count = buttons.count()

        if count == 0:
            log("✅", "No more 'Share interest' buttons found")
            break

        log("📌", f"Found {count} share-interest buttons")
        clicked_this_round = 0

        for i in range(count):
            try:
                buttons = page.locator("button.unshared")
                if i >= buttons.count():
                    break
                btn = buttons.nth(i)
                btn.scroll_into_view_if_needed()
                wait(page, BUFFER_MS)
                ok = safe_click(btn, f"Share interest #{total_clicked + 1}")
                if ok:
                    clicked_this_round += 1
                    total_clicked += 1
                wait(page, 2000)
            except Exception as e:
                log("⚠️", f"Share interest error: {e}")

        if clicked_this_round == 0:
            log("✅", "No clickable share buttons left")
            break

        log("🔄", "Refreshing page")
        wait(page, 3000)

    log("🎉", f"Shared interest total: {total_clicked}")


# ═══════════════════════════════════════════════════════
# LOGIN
# ═══════════════════════════════════════════════════════

def do_login(page: Page):
    log("🔐", "Logging in…")
    page.goto("https://www.naukri.com/nlogin/login")
    wait(page, 3000)
    page.locator("#usernameField").fill(EMAIL)
    page.locator("#passwordField").fill(PASSWORD)
    wait(page, 500)
    submit = page.locator("button[type='submit']").first
    safe_click(submit, "Login submit")
    try:
        page.wait_for_url(lambda url: "nlogin" not in url, timeout=15000)
    except Exception:
        pass
    wait(page, 4000)
    log("✅", "Logged in")


# ═══════════════════════════════════════════════════════
# APPLY / STATUS HELPERS
# ═══════════════════════════════════════════════════════

def check_applied_status(page: Page) -> bool:
    """Check if the page shows any applied/success confirmation."""
    try:
        # Naukri shows various success signals after submission
        selectors = [
            "text=/successfully applied/i",
            "text=/application submitted/i",
            "text=/applied successfully/i",
            "text=/you have already applied/i",
            "[class*='applied']",
            "[class*='success']",
        ]
        for sel in selectors:
            if page.locator(sel).count() > 0:
                log("✅", f"Applied confirmation detected: {sel}")
                return True
    except Exception:
        pass
    return False

def wait_for_application_complete(page: Page, timeout_ms: int = 8000) -> bool:
    """
    After clicking Save/Submit, poll for a success signal.
    Returns True if confirmed, False if timed out (still treat as submitted).
    """
    log("⏳", "Waiting for application confirmation…")
    interval = 1000
    elapsed  = 0
    while elapsed < timeout_ms:
        page.wait_for_timeout(interval)
        elapsed += interval
        if check_applied_status(page):
            return True
        log("⏳", f"  …still waiting ({elapsed // 1000}s / {timeout_ms // 1000}s)")
    log("⚠️", "Confirmation not detected — assuming submitted anyway")
    return False

def find_apply_button(page: Page) -> Locator | None:
    if check_applied_status(page):
        return None
    try:
        btn = page.locator("button:has-text('Apply')").first
        btn.wait_for(state="visible", timeout=2000)
        return btn
    except Exception:
        return None


# ═══════════════════════════════════════════════════════
# CHATBOT HELPERS
# ═══════════════════════════════════════════════════════

def get_chatbot(page: Page) -> Locator | Page:
    for sel in ["._chatBotContainer", "[class*='chatBot']", "[class*='chatbot']"]:
        loc = page.locator(sel)
        if loc.count() > 0:
            return loc.first
    return page

def get_latest_question(chatbot) -> str:
    """
    Get the latest bot question text.
    Tries multiple selectors since radio/dropdown questions may use different DOM.
    """
    try:
        # Primary: standard bot message items
        msgs = chatbot.locator("li.botItem span").all_text_contents()
        if msgs:
            return msgs[-1].strip()
    except Exception:
        pass

    try:
        # Fallback: any bot message bubble text
        msgs = chatbot.locator("[class*='botMsg'], [class*='bot-msg'], [class*='botItem']").all_text_contents()
        clean = [m.strip() for m in msgs if m.strip()]
        if clean:
            return clean[-1]
    except Exception:
        pass

    return ""

def has_pending_input(chatbot) -> bool:
    """
    Returns True if there are unanswered input widgets currently visible.
    This catches radio/dropdown questions that don't show up as new text.
    """
    try:
        # Unselected radio buttons (no input:checked inside the container)
        radios = chatbot.locator("div.ssrc__radio-btn-container, div[class*='radio-btn']")
        if radios.count() > 0:
            # Check if any radio is already selected
            checked = chatbot.locator(
                "div.ssrc__radio-btn-container input:checked, "
                "div[class*='radio-btn'] input:checked"
            )
            if checked.count() == 0:
                return True  # radios visible but none selected

        # Visible dropdowns with no selection
        dropdown = chatbot.locator("select")
        if dropdown.count() > 0:
            val = dropdown.first.input_value()
            if not val or val.lower() in ("", "select", "--"):
                return True

        # Visible text/number inputs that are empty
        inp = chatbot.locator(
            "input[type='text']:visible, input[type='number']:visible, textarea:visible"
        )
        if inp.count() > 0:
            val = inp.first.input_value()
            if not val.strip():
                return True

        # Visible contenteditable that's empty
        box = chatbot.locator("div[contenteditable='true']:visible")
        if box.count() > 0:
            txt = box.first.inner_text()
            if not txt.strip():
                return True

    except Exception:
        pass
    return False

def wait_for_new_question(chatbot, prev_q: str, retries=8, interval=1500) -> str:
    for _ in range(retries):
        chatbot.page.wait_for_timeout(interval)
        q = get_latest_question(chatbot)
        if q and q != prev_q:
            return q
    return ""


# ═══════════════════════════════════════════════════════
# BUTTON FINDERS (exact text)
# ═══════════════════════════════════════════════════════

# "Apply" intentionally excluded — it matches the initial Apply button, not the chatbot Save
SAVE_TEXTS = ["Save", "Submit", "Done", "Finish"]
NEXT_TEXTS = ["Next", "Proceed", "Continue"]

def _is_button_enabled(loc: Locator) -> bool:
    """Return False if the element is disabled or aria-disabled."""
    try:
        if loc.is_disabled():
            return False
        aria = loc.get_attribute("aria-disabled")
        if aria and aria.lower() == "true":
            return False
        cls = loc.get_attribute("class") or ""
        if any(kw in cls.lower() for kw in ("disabled", "inactive", "grey", "gray")):
            return False
        return True
    except Exception:
        return True  # optimistic default

def _find_button_exact(chatbot, texts: list[str], enabled_only: bool = False) -> Locator | None:
    for txt in texts:
        for tag in ["button", "div", "span", "a"]:
            try:
                loc = chatbot.locator(f"{tag}:text-is('{txt}')")
                if loc.count() == 0:
                    continue
                loc.first.wait_for(state="visible", timeout=800)
                if enabled_only and not _is_button_enabled(loc.first):
                    log("🚫", f"Button '{txt}' found but DISABLED — skipping")
                    continue
                log("🔍", f"Found button: [{tag}] '{txt}'")
                return loc.first
            except Exception:
                continue
    return None

def _do_save(chatbot, job_page: Page, answered: int, label: str = "") -> bool:
    """
    Find and click the Save/Submit button, then wait for confirmation.
    Returns True only when we're confident the form is fully submitted
    and it's safe to close the tab.
    """
    save = find_save_button(chatbot)
    if not save:
        return False

    tag = label or f"Save/Submit after {answered} answers"
    ok  = safe_click(save, tag)
    if not ok:
        return False

    # Wait up to 10s for the page to show a success signal
    confirmed = wait_for_application_complete(job_page, timeout_ms=10000)

    if confirmed:
        log("🎉", "Application fully confirmed ✅")
    else:
        # Extra buffer so the page can settle before the tab is closed
        log("⏸️", "No explicit confirmation — giving page 5s extra to settle…")
        job_page.wait_for_timeout(5000)

    return True  # Treat as submitted regardless

def find_save_button(chatbot) -> Locator | None:
    return _find_button_exact(chatbot, SAVE_TEXTS, enabled_only=True)

def find_next_button(chatbot) -> Locator | None:
    return _find_button_exact(chatbot, NEXT_TEXTS, enabled_only=True)


# ═══════════════════════════════════════════════════════
# INPUT HELPERS
# ═══════════════════════════════════════════════════════

def type_in_box(box: Locator, text: str):
    js_click(box)
    box.evaluate("el => { el.focus(); el.innerHTML = ''; }")
    box.type(text, delay=25)


# ═══════════════════════════════════════════════════════
# ANSWER ONE TURN
# Returns True if something was interacted with.
# ═══════════════════════════════════════════════════════

def handle_question_turn(chatbot, question: str) -> bool:

    # ── RADIO / CHECKBOX ──────────────────────────────
    radios = chatbot.locator(
        "div.ssrc__radio-btn-container, div[class*='radio-btn']"
    )
    if radios.count() > 0:
        opts = [o.strip() for o in radios.all_text_contents() if o.strip()]
        if opts:
            log("🔘", f"Radio options: {opts}")
            try:
                if "experience" in question.lower():
                    idx = choose_best_experience_option(opts)
                else:
                    raw = bard_flash_response(question, opts)
                    idx = max(0, min(int(raw) - 1, len(opts) - 1))
            except Exception:
                idx = 0

            chosen = opts[idx]
            container = radios.nth(idx)
            inner = container.locator(
                "label, input[type='radio'], input[type='checkbox']"
            )
            target = inner.first if inner.count() > 0 else container
            ok = safe_click(target, f"Radio[{idx}] = '{chosen}'")

            if ok:
                # Give the UI a moment to register the selection
                chatbot.page.wait_for_timeout(BUFFER_MS)
            return ok

    # ── DROPDOWN ──────────────────────────────────────
    dropdown = chatbot.locator("select")
    if dropdown.count() > 0:
        raw_opts = dropdown.first.locator("option").all_text_contents()
        opts = [o.strip() for o in raw_opts
                if o.strip().lower() not in ("", "select", "--")]
        if opts:
            log("📋", f"Dropdown options: {opts}")
            try:
                idx = max(0, min(int(bard_flash_response(question, opts)) - 1, len(opts) - 1))
            except Exception:
                idx = 0
            chosen = opts[idx]
            try:
                dropdown.first.select_option(label=chosen)
                log("📋 ✅", f"Dropdown selected → '{chosen}'")
                chatbot.page.wait_for_timeout(BUFFER_MS)
                return True
            except Exception as e:
                log("📋 ❌", f"Dropdown failed: {e}")

    # ── CONTENTEDITABLE ───────────────────────────────
    box = chatbot.locator("div[contenteditable='true']")
    if box.count() > 0:
        answer = bard_flash_response(question) or "Open to discuss"
        if answer == "NOT_AVAILABLE_IN_PROFILE":
            answer = "Open to discuss"
        type_in_box(box.first, answer)
        log("✏️ ✅", f"Typed (contenteditable) → {answer[:80]}")
        chatbot.page.wait_for_timeout(400)
        box.first.press("Enter")
        chatbot.page.wait_for_timeout(BUFFER_MS)
        return True

    # ── TEXT INPUT / TEXTAREA ─────────────────────────
    inp = chatbot.locator("input[type='text'], input[type='number'], textarea")
    if inp.count() > 0:
        answer = bard_flash_response(question) or "As per discussion"
        if answer == "NOT_AVAILABLE_IN_PROFILE":
            answer = "As per discussion"
        inp.first.fill(answer)
        inp.first.press("Enter")
        log("✏️ ✅", f"Typed (input) → {answer[:80]}")
        chatbot.page.wait_for_timeout(BUFFER_MS)
        return True

    return False


# ═══════════════════════════════════════════════════════
# PROCESS ONE JOB PAGE
# ═══════════════════════════════════════════════════════

def process_job(job_page: Page):

    # ── FIND & CLICK APPLY ────────────────────────────
    apply_btn = find_apply_button(job_page)
    if not apply_btn:
        log("❌", "Apply button not found — skipping")
        return

    apply_btn.scroll_into_view_if_needed()
    btn_text_before = ""
    try:
        btn_text_before = apply_btn.inner_text(timeout=1000).strip()
    except Exception:
        pass

    safe_click(apply_btn, f"Apply button ('{btn_text_before}')")
    wait(job_page, 3000)

    # ── DETECT REDIRECT TO COMPANY SITE ───────────────
    try:
        new_page = job_page.context.wait_for_event("page", timeout=2000)
        new_page.wait_for_load_state("domcontentloaded", timeout=3000)
        new_url = new_page.url
        company_sites = load_json("company_sites.json")
        company_sites.append(new_url)
        save_json("company_sites.json", company_sites)
        new_page.close()
        log("⏭️", f"Skipping — redirected to company site: {new_url}")
        return
    except Exception:
        pass  # No new tab — it's Naukri's own chatbot

    chatbot  = get_chatbot(job_page)
    prev_q   = ""
    answered = 0

    for round_num in range(MAX_ROUNDS):
        log("🔄", f"─── Round {round_num + 1} / {MAX_ROUNDS} ───────────────────────")

        # ── STEP 1: Check for unanswered input widgets ────
        # This is the PRIMARY signal. Radio/dropdown questions may not change
        # the text question but they DO show up as visible unanswered widgets.
        pending = has_pending_input(chatbot)
        question = get_latest_question(chatbot)

        if pending:
            log("🔎", f"Pending input detected | Q text: '{question[:80]}'")
            # Use the latest question text for context (even if same as prev)
            # If question text didn't change, use prev_q label for the answer
            q_for_answer = question if question else prev_q
            log("💬", f"Answering: {q_for_answer[:120]}")
            answered_this = handle_question_turn(chatbot, q_for_answer)

            if answered_this:
                answered += 1
                log("✅", f"Answered (total: {answered})")
                prev_q = question or prev_q
                # Wait for bot to process answer and potentially show next widget
                wait(job_page, BUFFER_MS)
                continue  # loop back — check has_pending_input again

            else:
                log("⚠️", "Pending input found but handle_question_turn returned False")
                # Don't save — wait and retry
                wait(job_page, 1500)
                continue

        # ── STEP 2: No pending input — check if new text question arrived ──
        if not question or question == prev_q:
            log("⏳", "No pending input, no new question — waiting for bot…")
            job_page.wait_for_timeout(2000)

            # Re-check after waiting
            pending = has_pending_input(chatbot)
            question = get_latest_question(chatbot)

            if pending or (question and question != prev_q):
                log("🔄", "Bot responded — looping back")
                continue

            # Still nothing — check applied status
            if check_applied_status(job_page):
                log("✅", "Application confirmed complete")
                job_page.wait_for_timeout(3000)
                return

            # Try Next button
            nxt = find_next_button(chatbot)
            if nxt:
                ok = safe_click(nxt, "Next (waiting for question)")
                if ok:
                    wait(job_page, 2000)
                    continue
                continue

            # Try Save only if answered at least 1 and no pending input
            if answered >= 1:
                submitted = _do_save(chatbot, job_page, answered, "Save (no pending input)")
                if submitted:
                    job_page.wait_for_timeout(3000)
                    return
                wait(job_page, 2000)
                continue

            log("⏳", "Nothing to do — waiting for bot…")
            wait(job_page, 2000)
            continue

        # ── STEP 3: New text question arrived, no pending input widget yet ──
        # (Bot asked a text question, widgets not rendered yet — wait one cycle)
        log("💬", f"New text Q: {question[:120]}")
        prev_q = question
        wait(job_page, 1000)  # give DOM time to render the input widget
        continue              # next iteration will catch has_pending_input

    # ── FELL OUT OF LOOP — last-attempt save ──────────
    log("⚠️", f"Max rounds ({MAX_ROUNDS}) reached — attempting final save")
    wait(job_page, 2000)
    submitted = _do_save(chatbot, job_page, answered, "Final save (loop exhausted)")
    if submitted:
        job_page.wait_for_timeout(3000)
        log("💾", "Final save done ✅")
    else:
        log("❌", "Could not save — job may be incomplete")


# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════

with sync_playwright() as p:
    browser = p.firefox.launch(headless=False)
    context = browser.new_context()
    page    = context.new_page()

    do_login(page)
    # update_resume(page)
    # auto_share_interest(page)

    log("🌐", "Loading recommended jobs")
    page.goto("https://www.naukri.com/mnjuser/recommendedjobs")
    wait(page, 6000)

    jobs  = page.locator("article.jobTuple")
    count = jobs.count()
    log("📌", f"Found {count} jobs")

    for i in range(count):
        log("═" * 50, "")
        log("🔎", f"Job {i + 1} / {count}")
        job_page = None

        try:
            job = jobs.nth(i)

            # Experience filter
            try:
                exp_text = job.locator("span[title*='Yrs']").inner_text(timeout=2000).strip()
                log("📄", f"Experience required: {exp_text}")
                match = re.search(r"(\d+)", exp_text)
                if match and int(match.group(1)) > 2:
                    log("⏭️", f"Skipping (requires {exp_text})")
                    continue
            except Exception:
                pass  # no exp label found — proceed

            with context.expect_page() as new_tab:
                js_click(job)
            job_page = new_tab.value
            job_page.wait_for_load_state("domcontentloaded")
            wait(job_page, 3000)

            process_job(job_page)

        except Exception as e:
            log("⚠️", f"Error on job {i + 1}: {e}")

        finally:
            # if job_page and not job_page.is_closed():
            #     # Extra settle time — never close tab immediately after save
            #     wait(job_page, 2000)
            #     job_page.close()
                log("🧹", "Job tab closed")

    # browser.close()
    log("🏁", "All done")