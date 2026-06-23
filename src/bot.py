"""
Naukri Bot v3 - Using Strong Job Utilities API & Ollama (Primary) + Gemini (Fallback)
"""

import re
import sys
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import json
import os
from datetime import datetime
from typing import Dict, Optional, Tuple
from difflib import SequenceMatcher

from playwright.sync_api import sync_playwright, Page, Locator
from google import genai
import urllib.request
import urllib.error

from naukri_jobs_handler import JobList, Job
from conf import (
    EMAIL, PASSWORD, MY_EXPERIENCE, EXTERNAL_JOBS_FILE, BOT_LOG_FILE,
    API_KEY, MODEL, OLLAMA_MODEL, OLLAMA_URL, USE_OLLAMA_FIRST, QA_FILE, RESUME_FILE, JOB_FILTERS, PREDEFINED_ANSWERS
)
from question_analyzer import QuestionAnalyzer, QuestionType
from resume_analyzer import ResumeAnalyzer, load_resume
from csv_logger import CSVLogger
from smart_answer_matcher import SmartAnswerMatcher
from answer_decision_tree import AnswerDecisionTree
from bot_statistics import BotStatistics
from dynamic_dashboard import DynamicDashboard

# ═══════════════════════════════════════════════════════════════
# AI BACKEND INTEGRATION (Ollama Primary + Gemini Fallback)
# ═══════════════════════════════════════════════════════════════

class SkipJobException(Exception):
    """Raised when the job should be skipped (e.g. unknown answer)"""
    pass

# Global state
_client = None
_resume_analyzer = None
_qa_cache = {}
_stats = {'calls': 0, 'cached': 0, 'generated': 0, 'ollama_used': 0, 'gemini_used': 0}


class AIAnswerEngine:
    """Enhanced answer generation with Ollama (primary) + Gemini (fallback)"""
    
    def __init__(self):
        self.resume_text = load_resume(RESUME_FILE)
        self.resume_analyzer = ResumeAnalyzer(self.resume_text)
        self.smart_matcher = SmartAnswerMatcher(current_ctc_annual=500000, expected_ctc_annual=800000)
        self.decision_tree = AnswerDecisionTree()
        self._init_client()
        self._load_cache()
    
    def _init_client(self):
        """Initialize Gemini client"""
        global _client
        if _client is None:
            _client = genai.Client(api_key=API_KEY)
    
    def _load_cache(self):
        """Load Q&A cache from file"""
        global _qa_cache
        if os.path.exists(QA_FILE):
            try:
                with open(QA_FILE, 'r') as f:
                    _qa_cache = json.load(f)
                    print(f"✅ Loaded {len(_qa_cache)} cached Q&A pairs")
            except Exception as e:
                print(f"⚠️  Error loading cache: {e}")
    
    def _save_cache(self):
        """Save Q&A cache to file"""
        try:
            with open(QA_FILE, 'w') as f:
                json.dump(_qa_cache, f, indent=2)
        except Exception as e:
            print(f"⚠️  Error saving cache: {e}")
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        return re.sub(r'\s+', ' ', text.lower().strip())
    
    def _find_similar_cached_question(self, question: str, threshold: float = 0.85) -> Optional[str]:
        """Find similar question in cache"""
        normalized_q = self._normalize_text(question)
        
        for cached_q, cached_a in _qa_cache.items():
            similarity = SequenceMatcher(None, normalized_q, self._normalize_text(cached_q)).ratio()
            if similarity >= threshold:
                return cached_a
        
        return None
    
    def _build_context_prompt(self, question: str, analyzer: QuestionAnalyzer) -> str:
        """Ultra-minimal prompt - answer like real job applicant in 5 seconds"""
        context = self.resume_analyzer.get_context_for_question(question)
        conf_skills = JOB_FILTERS.get("must_have_keywords", [])
        all_skills = list(context['skills']) + conf_skills
        all_skills = list(dict.fromkeys(all_skills))[:8]
        
        # Minimal direct prompt
        lines = [
            "ANSWER THIS LIKE A REAL JOB APPLICANT FILLING A FORM IN 5 SECONDS.",
            "",
            f"CANDIDATE: {MY_EXPERIENCE} years experience. Skills: {', '.join(all_skills)}",
            f"QUESTION: {question}",
            "",
            f"ANSWER STYLE: {analyzer.get_prompt_template()}",
            "",
            "DO NOT:",
            "- Use sentences or periods",
            "- Say 'I' or 'we' or 'the'",
            "- Explain or add details",
            "- Use adjectives or articles",
            "",
            "EXAMPLES:",
            "Q: Python experience? -> A: 2.5",
            "Q: Strengths? -> A: Python, ML, Analysis",
            "Q: Why join? -> A: Growing tech, challenging work",
            "Q: Willing relocate? -> A: Yes",
            "Q: Salary? -> A: 500000",
            "",
            "ANSWER NOW (ONLY THE ANSWER, NOTHING ELSE):",
        ]
        
        return "\n".join(lines)


    def _clean_answer(self, answer: str) -> str:
        """Clean and minimize answer - remove all fluff"""
        if not answer:
            return ""
        
        # Remove common prefixes
        answer = answer.strip()
        answer = re.sub(r'^(answer|response|here|the answer is|my answer|a:)[\s:]*', '', answer, flags=re.IGNORECASE)
        answer = re.sub(r'^(i would say|i think|i believe|i feel)[\s]*', '', answer, flags=re.IGNORECASE)
        answer = re.sub(r'^(based on|according to)[\s]*', '', answer, flags=re.IGNORECASE)
        
        # Remove trailing explanations
        answer = re.sub(r'\.(\s+.*)?$', '', answer)  # Remove period and anything after
        answer = re.sub(r'thank you.*?$', '', answer, flags=re.IGNORECASE)
        answer = re.sub(r'hope this helps.*?$', '', answer, flags=re.IGNORECASE)
        
        # Remove common suffixes
        answer = re.sub(r'(\.|!|\?|;)$', '', answer)
        
        # Clean whitespace
        answer = ' '.join(answer.split())
        
        return answer.strip()

    

    def _try_decision_tree(self, question: str) -> Optional[str]:
        """Try decision tree first (fastest, most reliable)"""
        answer, category = self.decision_tree.find_answer(question)
        if answer:
            print(f"✅ Tree match [{category}]: {answer}")
            return answer
        return None

    def _try_smart_answer(self, question: str) -> Optional[str]:
        """Try to get answer from smart matcher first (no LLM call)"""
        answer, source = self.smart_matcher.find_best_answer(question, use_llm_fallback=False)
        if answer and source != 'llm_needed':
            print(f"✅ Smart match [{source}]: {answer}")
            return answer
        return None

    def _generate_answer_ollama(self, prompt: str) -> Optional[str]:
        """Generate answer using Ollama"""
        try:
            print(f"🔌 Trying Ollama ({OLLAMA_MODEL})...")
            data = json.dumps({"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}).encode("utf-8")
            req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))
                answer = result.get("response", "").strip()
                if answer:
                    _stats['ollama_used'] += 1
                    print(f"✅ Answer generated by Ollama: {answer[:40]}...")
                    return answer
        except Exception as e:
            print(f"⚠️  Ollama failed: {e}")
        return None
    
    def _generate_answer_gemini(self, prompt: str) -> Optional[str]:
        """Generate answer using Gemini as fallback"""
        try:
            print(f"🔲 Trying Gemini ({MODEL})...")
            models_to_try = [MODEL, "gemini-3.5-flash", "gemini-2.5-flash"]
            models_to_try = list(dict.fromkeys(models_to_try))
            
            for m in models_to_try:
                try:
                    response = _client.models.generate_content(
                        model=m,
                        contents=prompt
                    )
                    answer = response.text.strip()
                    if m != MODEL:
                        print(f"⚠️  Fell back to model: {m}")
                    _stats['gemini_used'] += 1
                    print(f"✅ Answer generated by Gemini: {answer[:40]}...")
                    return answer
                except Exception as e:
                    print(f"⚠️  Model {m} failed: {e}")
        except Exception as e:
            print(f"⚠️  Gemini fallback failed: {e}")
        return None
    
    def _generate_answer(self, question: str, analyzer: QuestionAnalyzer, history: str = "") -> str:
        """Generate answer using Ollama (primary) or Gemini (fallback)"""
        self._current_history = history
        try:
            prompt = self._build_context_prompt(question, analyzer)
            print(f"🤖 Generating answer for: {question[:50]}...")
            
            answer = None
            
            # Try Ollama first if enabled
            if USE_OLLAMA_FIRST:
                answer = self._generate_answer_ollama(prompt)
            
            # Fallback to Gemini if Ollama failed or disabled
            if not answer:
                answer = self._generate_answer_gemini(prompt)
            
            if not answer:
                raise Exception("All backends failed to generate answer")
            
            # Clean up the answer
            answer = self._clean_answer(answer)
            
            if answer == "UNKNOWN_ANSWER":
                raise SkipJobException("AI does not know the answer to this question.")
            
            return answer
        
        except SkipJobException:
            raise
        except Exception as e:
            print(f"❌ Error generating answer: {e}")
            raise SkipJobException(f"Failed to generate answer: {e}")
    
    def answer_question(self, question: str, job_context: str = "", history: str = "") -> Tuple[str, Dict]:
        """
        Main method to answer a question with caching and analysis
        
        Returns:
            Tuple of (answer, metadata)
        """
        _stats['calls'] += 1
        
        # 0. Try decision tree first (fastest, most reliable)
        tree_answer = self._try_decision_tree(question)
        if tree_answer:
            _stats['cached'] += 1
            return tree_answer, {'source': 'decision_tree', 'analyzer': None}
        
        # 1a. Try smart matcher (backup)
        smart_answer = self._try_smart_answer(question)
        if smart_answer:
            _stats['cached'] += 1
            return smart_answer, {'source': 'smart_matcher', 'analyzer': None}
        
        # 1. Predefined answers override
        q_lower = question.lower()
        for kw, ans in PREDEFINED_ANSWERS.items():
            # Match if ALL words in the key are present anywhere in the question
            # e.g., "expected ctc" will match "What is your expected and current ctc?"
            if all(k in q_lower for k in kw.split()):
                _stats['cached'] += 1
                
                # Automatically convert to Lacs if the question asks for it
                if str(ans).isdigit() and int(ans) >= 100000:
                    if any(l in q_lower for l in ["lakh", "lac", "lpa"]):
                        ans = str(int(ans) / 100000).rstrip('0').rstrip('.')
                        
                log("⚡", f"Rule override triggered for '{kw}'")
                return str(ans), {'source': 'rule', 'analyzer': None}
        
        # Analyze question
        analyzer = QuestionAnalyzer(question)
        
        # Check if should skip
        if analyzer.should_skip():
            raise SkipJobException("Question analyzer identified this as a skip.")
        
        # Check cache
        cached_answer = self._find_similar_cached_question(question)
        if cached_answer:
            _stats['cached'] += 1
            print(f"✅ Using cached answer")
            return cached_answer, {'source': 'cache', 'analyzer': analyzer}
        
        # Generate new answer
        answer = self._generate_answer(question, analyzer, history)
        _stats['generated'] += 1
        
        # Cache the answer
        _qa_cache[question] = answer
        self._save_cache()
        
        return answer, {'source': 'generated', 'analyzer': analyzer}
    
    def get_stats(self) -> Dict:
        """Get usage statistics"""
        return {
            'total_calls': _stats['calls'],
            'cached_answers': _stats['cached'],
            'generated_answers': _stats['generated'],
            'ollama_used': _stats['ollama_used'],
            'gemini_used': _stats['gemini_used'],
            'cache_hit_rate': _stats['cached'] / max(_stats['calls'], 1),
            'cache_size': len(_qa_cache),
        }


# Global engine instance
_engine = None

def get_engine() -> AIAnswerEngine:
    """Get or create the answer engine"""
    global _engine
    if _engine is None:
        _engine = AIAnswerEngine()
    return _engine


def answer_question(question: str, job_context: str = "", history: str = "") -> str:
    """
    Answer a job application question
    
    Args:
        question: The question to answer
        job_context: Optional job/company context
        history: String of previously answered questions for context
    
    Returns:
        The answer string
    """
    engine = get_engine()
    answer, metadata = engine.answer_question(question, job_context, history)
    return answer


def get_stats() -> Dict:
    """Get API usage statistics"""
    engine = get_engine()
    return engine.get_stats()


# ═══════════════════════════════════════════════════════════════
# BOT SETTINGS & LOGGING
# ═══════════════════════════════════════════════════════════════
MAX_ROUNDS = 20
BUFFER_MS = 3000


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
# STATUS CHECKS
# ═══════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════
# MAIN - USING JOB UTILITIES
# ═══════════════════════════════════════════════════════════════

def main():
        csv_logger = CSVLogger()
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
            total_jobs = len(job_list)
            log("📌", f"Found {total_jobs} jobs")

            # Print all jobs summary
            count = min(len(job_list), 1000)
            print(f"\n📋 Total Jobs: {len(job_list)}")
            print(f"🔍 Showing first {count} jobs:\n")
            for i in range(count):
                j = job_list[i]
                print(f"{i+1}. {j.get_company():<30} | {j.get_role():<40} | {j.get_experience()}")
            log("", "")

            # Filter jobs using strong utilities
            log("🔍", "Filtering jobs...")
            must_have = JOB_FILTERS.get("must_have_keywords", [])
            must_not_have = JOB_FILTERS.get("must_not_have_keywords", [])
            women_only = JOB_FILTERS.get("women_only")
            remote_only = JOB_FILTERS.get("remote_only")
        
            # Custom filter for user experience
            def check_exp(job: Job) -> bool:
                exp_str = job.get_experience()
                if not exp_str: 
                    return True
                match = re.search(r'(\d+)\s*(?:-|to)\s*(\d+)', exp_str)
                if match:
                    min_e = int(match.group(1))
                    return MY_EXPERIENCE >= min_e - 1
                match = re.search(r'(\d+)\s*\+', exp_str)
                if match:
                    return MY_EXPERIENCE >= int(match.group(1))
                match = re.search(r'(\d+)', exp_str)
                if match:
                    return MY_EXPERIENCE >= int(match.group(1)) - 1
                return True

            valid_jobs = []
            for job in job_list:
                try:
                    role = job.get_role()
                    role_lower = role.lower()
                    
                    if must_have:
                        if not any(re.search(rf'\b{re.escape(k.lower())}\b', role_lower) for k in must_have):
                            log("⏭️", f"Skipped [{job.index}] {role[:100]}... : Missing 'must_have' keywords in Role")
                            csv_logger.log_skipped(job.get_company(), role, job.get_experience(), job.get_location(), "Missing must_have keywords")
                            job.hide()
                            continue
                            
                    if must_not_have:
                        if any(re.search(rf'\b{re.escape(k.lower())}\b', role_lower) for k in must_not_have):
                            log("⏭️", f"Skipped [{job.index}] {role[:100]}... : Contains 'must_not_have' keywords in Role")
                            csv_logger.log_skipped(job.get_company(), role, job.get_experience(), job.get_location(), "Contains must_not_have keywords")
                            job.hide()
                            continue
                            
                    if women_only:
                        if not job.is_women_only():
                            log("⏭️", f"Skipped [{job.index}] {role[:100]}... : Not a women-only job")
                            csv_logger.log_skipped(job.get_company(), role, job.get_experience(), job.get_location(), "Not a women-only job")
                            job.hide()
                            continue
                    else:
                        if job.is_women_only():
                            log("⏭️", f"Skipped [{job.index}] {role[:100]}... : Women-only job (candidate is male)")
                            csv_logger.log_skipped(job.get_company(), role, job.get_experience(), job.get_location(), "Women-only job (candidate is male)")
                            job.hide()
                            continue
                        
                    if remote_only and not job.is_remote():
                        log("⏭️", f"Skipped [{job.index}] {role[:100]}... : Not a remote job")
                        csv_logger.log_skipped(job.get_company(), role, job.get_experience(), job.get_location(), "Not a remote job")
                        job.hide()
                        continue
                        
                    if not check_exp(job):
                        log("⏭️", f"Skipped [{job.index}] {role[:100]}... : Experience requirement mismatch")
                        csv_logger.log_skipped(job.get_company(), role, job.get_experience(), job.get_location(), "Experience mismatch")
                        job.hide()
                        continue
                        
                    valid_jobs.append(job)
                except Exception as e:
                    log("⏭️", f"Skipped [{job.index}]: Error parsing card - {e}")
            
            log("📊", f"Valid jobs (Config Match + Exp Match): {len(valid_jobs)}")
            log("", "")

            applied = 0
            external = 0
            skipped = 0

            # Apply to first 5 jobs
            for job in valid_jobs[:5]:
                log("\n" + "="*60, "")
                log("🔎", f"Processing job index {job.index}")
            
                # Print job summary
                print(f"{'='*60}")
                print(f"📍 {job.get_company()} - {job.get_role()}")
                print(f"📅 Experience: {job.get_experience()}")
                print(f"📍 Location: {job.get_location()}")
                print(f"💰 Salary: {job.get_salary()}")
                print(f"🏷️  Skills: {', '.join(job.get_skills()[:5])}")
                print(f"🔥 Urgent Hiring: {'Yes' if job.is_urgent_hiring() else 'No'}")
                print(f"👩 Women Only: {'Yes' if job.is_women_only() else 'No'}")
                print(f"{'='*60}")
            
                job_page = None

                try:
                    # Open in new tab (strictly one by one)
                    with context.expect_page() as new_tab:
                        # Use evaluate to click using JS for reliability
                        job._loc.locator("p.title").first.evaluate("el => el.click()")
                
                    job_page = new_tab.value
                    job_page.wait_for_load_state("domcontentloaded")
                    wait(job_page, 3000)

                    # Check for external redirect
                    if "naukri.com" not in job_page.url:
                        log("🏢", "External company site!")
                    
                        job_data = extract_job_details(job_page)
                        job_data["company"] = job.get_company()
                        job_data["role"] = job.get_role()
                        save_external_job(job_data)
                        external += 1
                        
                        csv_logger.log_external(job.get_company(), job.get_role(), job.get_experience(), job.get_location(), job_page.url)
                    
                        job_page.close()
                        wait(page, 1000)
                        continue

                    # Apply
                    res, data = apply_job(job_page)
                    if res is True:
                        applied += 1
                        log("🎉", f"APPLIED! ({applied})")
                        csv_logger.log_applied(job.get_company(), job.get_role(), job.get_experience(), job.get_location(), data)
                    elif res == "External":
                        external += 1
                        log("🔗", "External application redirected")
                        csv_logger.log_external(job.get_company(), job.get_role(), job.get_experience(), job.get_location(), data)
                    else:
                        log("❌", "Failed")
                        csv_logger.log_skipped(job.get_company(), job.get_role(), job.get_experience(), job.get_location(), f"Application Failed (Answered {data} questions)")

                except SkipJobException as e:
                    log("⏭️", f"Skipped job: {e}")
                    skipped += 1
                except Exception as e:
                    log("💥", f"Error: {e}")

                finally:
                    # Ensure the tab is always closed before moving to the next job
                    # This guarantees we only have one application tab open at a time
                    if job_page and not job_page.is_closed():
                        job_page.close()
                        log("🚫", "Closed Job Tab")
                    wait(page, 1000)

            # Print final stats
            log("\n" + "="*60, "")
            log("🏁", f"DONE - Applied: {applied} | External: {external} | Skipped: {skipped}")
            
            stats = get_stats()
            print(f"\n📊 AI Backend Statistics:")
            print(f"   Total Questions: {stats['total_calls']}")
            print(f"   Cached Answers: {stats['cached_answers']}")
            print(f"   Generated Answers: {stats['generated_answers']}")
            print(f"   Ollama Used: {stats['ollama_used']}")
            print(f"   Gemini Used: {stats['gemini_used']}")
            print(f"   Cache Hit Rate: {stats['cache_hit_rate']:.1%}")
            
            # Record statistics for dashboard
            run_data = {
                'jobs_loaded': total_jobs,
                'jobs_filtered': len(valid_jobs),
                'jobs_applied': applied,
                'jobs_skipped': skipped,
                'questions_total': stats['total_calls'],
                'questions_answered': stats['generated_answers'] + stats['cached_answers'],
                'questions_unanswered': 0,
                'questions_by_type': {},
                'external_redirects': external,
                'external_urls': [],
                'llm_calls': stats['gemini_used'],
                'decision_tree_calls': stats['cached_answers'],
                'cache_hits': stats['cached_answers'],
                'errors': 0,
                'error_list': [],
                'duration': 0,
            }
            
            try:
                bot_stats = BotStatistics()
                bot_stats.record_run(run_data)
                dashboard = DynamicDashboard()
                dashboard.generate_dynamic_dashboard()
                print(f"\n✅ Statistics recorded and dashboard updated!")
                print(f"   View dashboard: data/dashboard.html")
            except Exception as e:
                print(f"⚠️  Could not update dashboard: {e}")


if __name__ == "__main__":
    main()
