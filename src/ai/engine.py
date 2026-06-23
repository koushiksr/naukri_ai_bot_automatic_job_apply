
import os
import re
import json
import urllib.request
from difflib import SequenceMatcher
from typing import Dict, Optional, Tuple
from google import genai
from conf import (API_KEY, MODEL, 
                 QA_FILE, RESUME_FILE, JOB_FILTERS, PREDEFINED_ANSWERS, MY_EXPERIENCE)
from ai.question_analyzer import QuestionAnalyzer
from ai.resume_analyzer import ResumeAnalyzer, load_resume
from ai.smart_answer_matcher import SmartAnswerMatcher
from ai.answer_decision_tree import AnswerDecisionTree
from core.common import log, SkipJobException

_client = None
_qa_cache = {}
_stats = {'calls': 0, 'cached': 0, 'generated': 0, 'gemini_used': 0}

class AIAnswerEngine:
    """Enhanced answer generation with Gemini"""
    
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
                
        # Auto-ingest manually answered questions
        unanswered_file = "data/unanswered_questions.txt"
        if os.path.exists(unanswered_file):
            try:
                with open(unanswered_file, 'r') as f:
                    content = f.read()
                
                new_answers = False
                blocks = content.split("Q: ")
                remaining_blocks = []
                
                for block in blocks:
                    if not block.strip():
                        continue
                    if "\nA: " in block:
                        q_part, a_part = block.split("\nA: ", 1)
                        q = q_part.strip()
                        a = a_part.strip()
                        if a:  # User provided an answer
                            _qa_cache[q] = a
                            new_answers = True
                            print(f"✅ Imported manual answer for: '{q[:30]}...'")
                        else:
                            remaining_blocks.append(f"Q: {block.strip()}\n\n")
                    else:
                        remaining_blocks.append(f"Q: {block.strip()}\n\n")
                
                if new_answers:
                    self._save_cache()
                    # Rewrite the unanswered file without the answered questions
                    with open(unanswered_file, 'w') as f:
                        for rb in remaining_blocks:
                            f.write(rb)
                            
            except Exception as e:
                print(f"⚠️  Error loading manual answers: {e}")
    
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
        # Loop to remove prefixes iteratively until no more changes are made
        while True:
            old_ans = answer
            answer = re.sub(r'^(answer|response|here|the answer is|my answer|a:)[\s:]*', '', answer, flags=re.IGNORECASE)
            answer = re.sub(r'^(i would say|i think|i believe|i feel)[\s]*', '', answer, flags=re.IGNORECASE)
            answer = re.sub(r'^(based on|according to)[^,]*,\s*', '', answer, flags=re.IGNORECASE)
            answer = answer.strip()
            if answer == old_ans:
                break
        
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

    def _generate_answer_gemini(self, prompt: str, question: str) -> Optional[str]:
        """Generate answer using Gemini"""
        try:
            print(f"🔲 Trying Gemini ({MODEL}) for question: '{question}'...")
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
                    print(f"✅ Answer generated by Gemini [{m}]:\nQuestion: {question}\nAnswer: {answer}\n")
                    return answer
                except Exception as e:
                    print(f"⚠️  Model {m} failed: {e}")
        except Exception as e:
            print(f"⚠️  Gemini fallback failed: {e}")
        return None
    
    def _log_unanswered_question(self, question: str):
        """Log questions the AI couldn't answer for the user to answer manually"""
        unanswered_file = "data/unanswered_questions.txt"
        
        # Check if already in the file
        if os.path.exists(unanswered_file):
            with open(unanswered_file, 'r') as f:
                if question in f.read():
                    return
                    
        # Append to the file
        try:
            with open(unanswered_file, 'a') as f:
                f.write(f"Q: {question}\nA: \n\n")
            print(f"📝 Logged unanswered question to {unanswered_file}")
        except Exception as e:
            print(f"⚠️  Failed to log unanswered question: {e}")

    def _generate_answer(self, question: str, analyzer: QuestionAnalyzer, history: str = "") -> str:
        """Generate answer using Gemini"""
        self._current_history = history
        try:
            prompt = self._build_context_prompt(question, analyzer)
            print(f"🤖 Generating answer for: {question[:50]}...")
            
            answer = self._generate_answer_gemini(prompt, question)
            
            if not answer:
                self._log_unanswered_question(question)
                raise SkipJobException("AI does not know the answer to this question.")
            
            # Clean up the answer
            answer = self._clean_answer(answer)
            
            if answer == "UNKNOWN_ANSWER":
                self._log_unanswered_question(question)
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


