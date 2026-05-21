import json
import os
import re
from difflib import SequenceMatcher

QA_FILE = "qa_store.json"
RESUME_FILE = "Resume.pdf"

def _norm(t):
    return re.sub(r"\s+", " ", t.lower().strip())

def load_json(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ---------------------------
# SIMPLE RAG MATCHER
# ---------------------------
def similarity(a, b):
    return SequenceMatcher(None, _norm(a), _norm(b)).ratio()

def search_qa(question):
    data = load_json(QA_FILE)
    best = None
    best_score = 0

    for item in data:
        score = similarity(question, item["q"])
        if score > best_score:
            best_score = score
            best = item

    if best_score > 0.75:
        return best["a"]
    return None

def search_resume(question):
    if not os.path.exists(RESUME_FILE):
        return None

    with open(RESUME_FILE, "r", encoding="utf-8") as f:
        text = f.read()

    qn = _norm(question)

    # simple keyword overlap RAG
    lines = text.split("\n")
    best = None
    best_score = 0

    for line in lines:
        score = similarity(qn, line)
        if score > best_score:
            best_score = score
            best = line

    if best_score > 0.4:
        return best.strip()

    return None