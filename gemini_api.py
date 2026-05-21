import json
import os
import re
from difflib import SequenceMatcher

from google import genai
from google.genai import types
from PyPDF2 import PdfReader

from conf import API_KEY, MODEL, QA_FILE, RESUME_FILE


# ═══════════════════════════════════════════════════════
# CLIENT
# ═══════════════════════════════════════════════════════

_client        = genai.Client(api_key=API_KEY)
_resume_cache  = None
_qa_cache      = None


# ═══════════════════════════════════════════════════════
# CANDIDATE PROFILE  (edit here — checked FIRST)
# ═══════════════════════════════════════════════════════

PROFILE = {
    "total_experience":   "2",
    "current_location":   "Bengaluru",
    "preferred_location": "Bengaluru",
    "notice_period":      "Immediate",
    "ready_to_relocate":  "Yes",
    "current_ctc":        "500000",
    "expected_ctc":       "open to discuss",
    "skill_experience": {
        "default":       "1",

        # AI / ML / LLM
        "python":        "2.6",
        "ai":            "2.6",
        "ml":            "2.6",
        "llm":           "2",
        "rag":           "2",
        "langchain":     "2",
        "prompt":        "2",
        "embedding":     "2",
        "semantic":      "2",
        "vector":        "2",
        "hallucination": "2",
        "transformers":  "2",
        "huggingface":   "2",
        "hugging face":  "2",

        # Models
        "gpt":           "2",
        "claude":        "2",
        "llama":         "2",
        "mistral":       "2",
        "phi":           "2",
        "gemma":         "1",
        "whisper":       "1",
        "nomic":         "1",
        "esrgan":        "1",
        "real-esrgan":   "1",

        # Backend / APIs
        "fastapi":       "2",
        "rest":          "2",
        "api":           "2",
        "node":          "1",
        "express":       "1",

        # Frontend
        "react":         "2",
        "recoil":        "1",
        "tailwind":      "1",

        # Databases
        "mongodb":       "1",

        # Languages
        "typescript":    "1",
        "javascript":    "2",
        "java":          "1",
        "c#":            "1",
        ".net":          "1",

        # DevOps / Infra
        "docker":        "2",
        "nginx":         "1",
        "pm2":           "1",
        "jenkins":       "1",
        "ci/cd":         "1",
        "linux":         "2",
        "gpu":           "2",
        "cloud":         "1",
        "aws":           "1",
        "azure":         "1",

        # Data / ML libs
        "pytorch":       "1",
        "scikit":        "1",
        "pandas":        "1",

        # Other
        "ollama":        "2",
        "multimodal":    "1",
        "observability": "1",
    },
}

# Question keyword → profile key
_PROFILE_RULES = [
    (["current location", "your location", "located", "city",
      "where are you", "base location"],                         "current_location"),
    (["preferred location", "prefer to work", "work location"],  "preferred_location"),
    (["notice period", "joining", "how soon",
      "available from", "start date", "last working day",
      "when can you join"],                                       "notice_period"),
    (["relocat"],                                                 "ready_to_relocate"),
    (["total experience", "years of experience", "overall experience",
      "how many years", "work experience", "professional experience",
      "total exp"],                                               "total_experience"),
    (["current ctc", "current salary", "current package"],        "current_ctc"),
    (["expected ctc", "expected salary", "salary expectation",
      "expected annual ctc"],                                     "expected_ctc"),
]


def _match_profile(question: str) -> str | None:
    """Return a direct answer from PROFILE if question matches a known key."""
    q = question.lower()

    for keywords, profile_key in _PROFILE_RULES:
        if any(kw in q for kw in keywords):
            return PROFILE[profile_key]

    # Skill-specific experience
    if "experience" in q or "years" in q:
        for skill_kw, years in PROFILE["skill_experience"].items():
            if skill_kw != "default" and skill_kw in q:
                return years
        return PROFILE["total_experience"]   # generic fallback

    return None


# ═══════════════════════════════════════════════════════
# STRING UTILS
# ═══════════════════════════════════════════════════════

def _norm(t: str) -> str:
    return re.sub(r"\s+", " ", str(t).lower().strip())

def _sim(a: str, b: str) -> float:
    return SequenceMatcher(None, _norm(a), _norm(b)).ratio()


# ═══════════════════════════════════════════════════════
# QA MEMORY
# ═══════════════════════════════════════════════════════

def _load_qa() -> list:
    global _qa_cache
    if _qa_cache is not None:
        return _qa_cache
    if not os.path.exists(QA_FILE):
        _qa_cache = []
        return _qa_cache
    try:
        with open(QA_FILE, "r", encoding="utf-8") as f:
            _qa_cache = json.load(f)
    except Exception:
        _qa_cache = []
    return _qa_cache

def _save_qa(question: str, answer: str):
    global _qa_cache
    store = _load_qa()
    if any(_sim(question, item.get("q", "")) >= 0.95 for item in store):
        return
    store.append({"q": question, "a": str(answer)})
    _qa_cache = store
    try:
        with open(QA_FILE, "w", encoding="utf-8") as f:
            json.dump(store, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[QA save error] {e}")

def _search_qa(question: str) -> str | None:
    best, score = None, 0.0
    for item in _load_qa():
        s = _sim(question, item.get("q", ""))
        if s > score:
            best, score = item, s
    return best["a"] if best and score >= 0.85 else None


# ═══════════════════════════════════════════════════════
# RESUME
# ═══════════════════════════════════════════════════════

def _load_resume() -> str:
    global _resume_cache
    if _resume_cache is not None:
        return _resume_cache
    if not os.path.exists(RESUME_FILE):
        _resume_cache = ""
        return ""
    try:
        reader = PdfReader(RESUME_FILE)
        _resume_cache = "\n".join(p.extract_text() or "" for p in reader.pages)
    except Exception as e:
        print(f"[Resume error] {e}")
        _resume_cache = ""
    return _resume_cache

def _top_resume_lines(question: str) -> str:
    lines  = [l.strip() for l in _load_resume().split("\n") if len(l.strip()) > 10]
    scored = sorted(lines, key=lambda l: _sim(question, l), reverse=True)
    return "\n".join(scored[:5])


# ═══════════════════════════════════════════════════════
# GEMINI CALL
# ═══════════════════════════════════════════════════════

def _call_gemini(prompt: str, retries: int = 2) -> str:
    for attempt in range(retries + 1):
        try:
            response = _client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(max_output_tokens=200),
            )
            return (response.text or "").strip()
        except Exception as e:
            print(f"[Gemini error attempt {attempt + 1}] {e}")
    return ""

def _profile_block() -> str:
    return (
        "CANDIDATE PROFILE (highest priority — use directly):\n"
        f"- Total experience    : {PROFILE['total_experience']} years\n"
        f"- Current location    : {PROFILE['current_location']}\n"
        f"- Preferred location  : {PROFILE['preferred_location']}\n"
        f"- Notice period       : {PROFILE['notice_period']}\n"
        f"- Ready to relocate   : {PROFILE['ready_to_relocate']}\n"
        f"- Current CTC         : {PROFILE['current_ctc']}\n"
        f"- Expected CTC        : {PROFILE['expected_ctc']}\n"
        "- Python/ML/AI/LLM exp: 2 years\n"
        "- PyTorch/Cloud/AWS   : 1 year\n"
    )


# ═══════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════

def bard_flash_response(question: str, options: list[str] | None = None) -> str:
    question = question.strip()

    # 1. Fastest: direct profile match
    profile_ans = _match_profile(question)
    if profile_ans:
        print(f"[Profile] {question[:60]} → {profile_ans}")
        if options:
            q_lower = profile_ans.lower()
            for i, opt in enumerate(options):
                if q_lower in opt.lower() or opt.lower() in q_lower:
                    return str(i + 1)
            return "1"
        return profile_ans

    # 2. QA cache
    cached = _search_qa(question)
    if cached:
        print(f"[Cache]   {question[:60]} → {cached}")
        return cached

    # 3. Gemini
    context = _top_resume_lines(question)

    if options:
        opts_text = "\n".join(f"{i+1}. {o}" for i, o in enumerate(options))
        prompt = (
            "You are filling a job application for an AI/ML Engineer in India.\n"
            "Pick the BEST answer. Return ONLY the option number. No explanation.\n\n"
            f"{_profile_block()}\n"
            f"RESUME CONTEXT:\n{context}\n\n"
            f"QUESTION: {question}\n\n"
            f"OPTIONS:\n{opts_text}\n\n"
            f"ANSWER (number only):"
        )
        out    = _call_gemini(prompt)
        nums   = re.findall(r"\d+", out)
        answer = str(max(1, min(int(nums[0]), len(options)))) if nums else "1"
        _save_qa(question, answer)
        return answer

    prompt = (
        "You are filling a job application for an AI/ML Engineer in India.\n"
        "Answer concisely (1 sentence or just a number). Use first person.\n"
        "If the answer is a number, return ONLY the number.\n"
        "Never say 0 or 'no experience'; use 1 or 2 as minimum.\n"
        "If truly unknown, return: NOT_AVAILABLE_IN_PROFILE\n\n"
        f"{_profile_block()}\n"
        f"RESUME:\n{_load_resume()[:3000]}\n\n"
        f"QUESTION: {question}\n\n"
        "ANSWER:"
    )
    out    = _call_gemini(prompt)
    answer = out if out else "NOT_AVAILABLE_IN_PROFILE"
    if answer != "NOT_AVAILABLE_IN_PROFILE":
        _save_qa(question, answer)
    return answer