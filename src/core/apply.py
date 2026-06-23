
import re
import json
from typing import Tuple
from playwright.sync_api import Page, Locator
from datetime import datetime
from conf import MY_EXPERIENCE
from ai.engine import answer_question
from core.common import log, SkipJobException
from core.browser import js_click, wait, get_page, save_external_job, BUFFER_MS, MAX_ROUNDS

def is_applied(page: Page) -> bool:
    """Check for success indicators using XPath and text matching"""
    try:
        # Check using XPath for applied status element
        try:
            # Full XPath
            elem_full = page.locator("xpath=/html/body/div/main/div[1]/div[1]/div[1]/div[1]/div/div[2]/div[1]/div[1]")
            if elem_full.count() > 0:
                text = elem_full.inner_text().lower()
                if "applied" in text or "You were redirected" in text:
                    log("✅", "Applied detected via XPath (full)")
                    return True
        except:
            pass
        
        try:
            # Short XPath with root ID
            elem_short = page.locator("xpath=//*[@id='root']/main/div[1]/div[1]/div[1]/div[1]/div/div[2]/div[1]/div[1]")
            if elem_short.count() > 0:
                text = elem_short.inner_text().lower()
                if "applied" in text:
                    log("✅", "Applied detected via XPath (short)")
                    return True
        except:
            pass
        
        # Fallback: check page content for success phrases
        content = page.content().lower()
        success_phrases = [
            "successfully applied", 
            "application submitted", 
            "applied successfully",
            "already applied"
        ]
        if any(phrase in content for phrase in success_phrases):
            log("✅", "Applied detected via content search")
            return True
            
        # Check if the Apply button has changed to an 'Applied' state
        try:
            applied_elem = page.locator("button:text-is('Applied'), div:text-is('Applied'), span:text-is('Applied')").first
            if applied_elem.count() > 0 and applied_elem.is_visible():
                log("✅", "Applied detected via button text")
                return True
        except:
            pass
            
        return False
    except Exception as e:
        log("⚠️", f"Error checking applied status: {e}")
        return False


def find_apply_btn(page: Page) -> Locator | None:
    if is_applied(page):
        return None
    try:
        btn = page.locator("button:has-text('Apply')").first
        btn.wait_for(state="visible", timeout=6000)
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
        radios = chatbot.locator("div.ssrc__radio-btn-container, div[class*='radio-btn'], label:has(input[type='radio'])")
        if radios.count() > 0:
            checked = chatbot.locator(
                "div.ssrc__radio-btn-container input:checked, div[class*='radio-btn'] input:checked, label:has(input[type='radio']:checked), input[type='radio']:checked"
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


def click_save_or_next(chatbot):
    for btn_text in ["Save", "Next", "Submit", "Proceed", "Continue"]:
        try:
            btn = chatbot.locator(f"button:has-text('{btn_text}'), div.sendMsg:has-text('{btn_text}'), [class*='btn']:has-text('{btn_text}')").last
            if btn.count() > 0:
                btn.wait_for(state="visible", timeout=1500)
                js_click(btn)
                log("🖱️", f"Clicked '{btn_text}' after answering")
                wait(get_page(chatbot), 2000)
                return True
        except:
            pass
    return False


def answer_turn(chatbot, q: str, history: str = "") -> Tuple[bool, str]:
    """Answer ONE input element with AI help"""
    page = get_page(chatbot)
    
    # ── RADIO ──
    radios = chatbot.locator("div.ssrc__radio-btn-container, div[class*='radio-btn'], label:has(input[type='radio'])")
    if radios.count() > 0:
        opts = [o.strip() for o in radios.all_text_contents() if o.strip()]
        if opts:
            log("🔘", f"Radio: {opts}")
            
            ai_ans = ""
            if "experience" in q.lower():
                idx = 0
                for i, opt in enumerate(opts):
                    nums = [int(n) for n in re.findall(r"\d+", opt)]
                    if len(nums) == 2:
                        start, end = nums
                        if start <= MY_EXPERIENCE <= end:
                            idx = i
                            ai_ans = opt
                            break
                    elif nums and MY_EXPERIENCE >= nums[0]:
                        idx = i
                        ai_ans = opt
                if not ai_ans: ai_ans = opts[idx]
            else:
                try:
                    ai_ans = answer_question(q, history=history)
                    log("🤖", f"AI: {ai_ans[:50]}")
                    
                    idx = 0
                    for i, opt in enumerate(opts):
                        if ai_ans.lower() in opt.lower():
                            idx = i
                            ai_ans = opt
                            break
                except SkipJobException:
                    raise
                except Exception as e:
                    log("❌", f"AI error: {e}")
                    idx = 0
                    ai_ans = opts[idx] if opts else ""
            
            container = radios.nth(idx)
            label = container.locator("label, input[type='radio'], input[type='checkbox']")
            target = label.first if label.count() > 0 else container
            ok = js_click(target)
            log("🖱️", f"Clicked radio[{idx}]" + (" ✅" if ok else " ❌"))
            if ok:
                click_save_or_next(chatbot)
                wait(page, BUFFER_MS)
            return (ok, ai_ans)

    # ── DROPDOWN ──
    dropdown = chatbot.locator("select")
    if dropdown.count() > 0:
        opts = [o.strip() for o in dropdown.first.locator("option").all_text_contents()]
        opts = [o for o in opts if o and o.lower() not in ("select", "--")]
        if opts:
            log("📋", f"Dropdown: {opts}")
            
            ai_ans = ""
            try:
                ai_ans = answer_question(q, history=history)
                idx = 0
                for i, opt in enumerate(opts):
                    if ai_ans.lower() in opt.lower():
                        idx = i
                        ai_ans = opt
                        break
            except SkipJobException:
                raise
            except:
                idx = 0
                ai_ans = opts[idx] if opts else ""
            
            try:
                dropdown.first.select_option(label=opts[idx])
                log("📋", f"Selected ✅")
                click_save_or_next(chatbot)
                wait(page, BUFFER_MS)
                return (True, ai_ans)
            except Exception as e:
                log("❌", f"Dropdown error: {e}")

    # ── TEXT BOX ──
    box = chatbot.locator("div[contenteditable='true']")
    if box.count() > 0:
        try:
            ans = answer_question(q, history=history)
        except SkipJobException:
            raise
        except:
            ans = "Open to discuss"
        
        js_click(box.first)
        box.first.evaluate("el => { el.focus(); el.innerHTML = ''; }")
        box.first.type(ans, delay=20)
        log("✏️", f"Typed ✅")
        wait(page, 400)
        box.first.press("Enter")
        click_save_or_next(chatbot)
        wait(page, BUFFER_MS)
        return (True, ans)

    # ── TEXT INPUT ──
    inp = chatbot.locator("input[type='text'], input[type='number'], textarea")
    if inp.count() > 0:
        try:
            ans = answer_question(q, history=history)
        except SkipJobException:
            raise
        except:
            ans = "As per discussion"
        inp.first.fill(ans)
        inp.first.press("Enter")
        log("✏️", f"Typed ✅")
        click_save_or_next(chatbot)
        wait(page, BUFFER_MS)
        return (True, ans)

    return (False, "")


# ═══════════════════════════════════════════════════════════════
# APPLY PROCESS
# ═══════════════════════════════════════════════════════════════

def apply_job(job_page: Page) -> Tuple[bool | str, any]:
    """Apply to job with question handling."""
    
    btn = find_apply_btn(job_page)
    if not btn:
        log("❌", "No Apply button")
        return (False, None)

    btn.scroll_into_view_if_needed()
    btn_text = btn.inner_text().strip().lower()
    if "company site" in btn_text:
        log("🌐", "Button says 'Apply on company site'")
        
    try:
        # Detect if clicking opens a new tab (external site)
        with job_page.context.expect_page(timeout=2000) as new_page_info:
            js_click(btn)
        new_page = new_page_info.value
        ext_url = new_page.url
        log("🌐", "External company site opened in new tab")
        try:
            new_page.close()
        except:
            pass
        return ("External", ext_url)
    except:
        # No new tab opened. Standard Naukri apply or it just clicked it normally.
        pass

    log("🖱️", "Clicked Apply")
    wait(job_page, 3000)

    # Check if the current tab got redirected to an external site
    if "naukri.com" not in job_page.url:
        log("🌐", "Redirected to external company site")
        return ("External", job_page.url)

    # Immediately check if it applied successfully without any questions
    if is_applied(job_page):
        log("✅", "APPLIED!")
        return (True, 0)

    chatbot = get_chatbot(job_page)
    prev_q = ""
    answered = 0
    qa_history_list = []
    stuck_counter = 0
    idle_counter = 0

    for r in range(MAX_ROUNDS):
        has_inp = has_input(chatbot)
        q = get_question(chatbot)

        if has_inp:
            idle_counter = 0  # reset idle if we have inputs
            q_use = q if q else prev_q
            log("❓", f"Q: {q_use[:60]}")
            
            history_str = "\n".join(qa_history_list[-5:])
            ok, ans_text = answer_turn(chatbot, q_use, history=history_str)
            if ok:
                answered += 1
                qa_history_list.append(f"Q: {q_use} A: {ans_text}")
                log("✅", f"Answered ({answered})")
                
                if q_use == prev_q:
                    stuck_counter += 1
                else:
                    stuck_counter = 0
                
                if stuck_counter >= 3:
                    log("❌", "Stuck on the exact same question. Aborting loop.")
                    return (False, answered)
                
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
                return (True, answered)

            found_button = False
            for btn_text in ["Next", "Proceed", "Continue"]:
                try:
                    nxt = chatbot.locator(f"button:has-text('{btn_text}'), div.sendMsg:has-text('{btn_text}'), [class*='btn']:has-text('{btn_text}')").first
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
                        save = chatbot.locator(f"button:has-text('{btn_text}'), div.sendMsg:has-text('{btn_text}'), [class*='btn']:has-text('{btn_text}')").first
                        save.wait_for(state="visible", timeout=500)
                        js_click(save)
                        log("🖱️", f"Clicked {btn_text}")
                        wait(get_page(chatbot), 3000)
                        if is_applied(job_page):
                            log("✅", "APPLIED!")
                            return (True, answered)
                    except:
                        pass
                        
            if not found_button:
                idle_counter += 1
                if idle_counter >= 3:
                    log("⚠️", "Page is idle with no questions. Assuming completion.")
                    return (True, answered)

            wait(get_page(chatbot), 2000)
            continue

        log("💬", f"New Q: {q[:60]}")
        prev_q = q
        wait(get_page(chatbot), 1000)
        continue

    log("⚠️", "Max rounds reached")
    for btn_text in ["Save", "Submit", "Done", "Finish"]:
        try:
            save = chatbot.locator(f"button:has-text('{btn_text}'), div.sendMsg:has-text('{btn_text}'), [class*='btn']:has-text('{btn_text}')").first
            save.wait_for(state="visible", timeout=500)
            js_click(save)
            log("🖱️", f"Final {btn_text}")
            wait(get_page(chatbot), 3000)
            if is_applied(job_page):
                log("✅", "APPLIED!")
                return (True, answered)
        except:
            pass

    return (False, answered)


