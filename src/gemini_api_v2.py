"""
Enhanced Gemini API - Better question analysis and answering
"""

import json
import os
import re
from typing import Dict, Optional, Tuple
from difflib import SequenceMatcher
import google.generativeai as genai

from conf import API_KEY, MODEL, QA_FILE, RESUME_FILE
from question_analyzer import QuestionAnalyzer, QuestionType
from resume_analyzer import ResumeAnalyzer, load_resume

# Global state
_client = None
_resume_analyzer = None
_qa_cache = {}
_stats = {'calls': 0, 'cached': 0, 'generated': 0}


class GeminiAnswerEngine:
    """Enhanced answer generation with context awareness"""
    
    def __init__(self):
        self.resume_text = load_resume(RESUME_FILE)
        self.resume_analyzer = ResumeAnalyzer(self.resume_text)
        self._init_client()
        self._load_cache()
    
    def _init_client(self):
        """Initialize Gemini client"""
        global _client
        if _client is None:
            genai.configure(api_key=API_KEY)
            _client = genai.GenerativeModel(MODEL)
    
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
        """Build enhanced prompt with context"""
        strategy = analyzer.strategy
        context = self.resume_analyzer.get_context_for_question(question)
        
        prompt_parts = [
            "You are an expert job application assistant helping a candidate answer interview questions.",
            f"\nCANDIDATE PROFILE:\n{self.resume_analyzer.summary}",
            f"\nCANDIDATE SKILLS: {', '.join(list(context['skills'])[:8])}",
            f"\nQUESTION: {question}",
            f"\nQUESTION TYPE: {analyzer.question_type.value}",
            f"\nANSWER STRATEGY: {analyzer.get_prompt_template()}",
        ]
        
        # Add context-specific information
        if strategy['focus'] == 'technical_and_soft':
            prompt_parts.append(f"\nRELEVANT SKILLS: {', '.join(list(context['skills'])[:6])}")
        
        elif strategy['focus'] == 'professional_background':
            prompt_parts.append(f"\nEXPERIENCE: {context['experience_years']} years")
            prompt_parts.append(f"\nCOMPANIES: {', '.join(context['companies'][:3])}")
        
        elif strategy['focus'] == 'management_ability':
            prompt_parts.append(f"\nLeadership skills inferred from: {', '.join(list(context['skills'])[:4])}")
        
        # Add tone instruction
        prompt_parts.append(f"\nTONE: {strategy['tone'].capitalize()}, professional, and concise.")
        
        # Add length instruction
        if strategy['length'] == 'short':
            prompt_parts.append("\nKEEP IT SHORT: 1-2 sentences max.")
        elif strategy['length'] == 'medium':
            prompt_parts.append("\nKEEP IT CONCISE: 2-3 sentences max.")
        else:
            prompt_parts.append("\nKEEP IT DETAILED: 3-4 sentences max.")
        
        # Add example instruction if applicable
        if strategy['examples']:
            prompt_parts.append("\nInclude a brief relevant example if possible.")
        
        prompt_parts.append("\nProvide ONLY the answer - no explanations or extra text.")
        
        return "\n".join(prompt_parts)
    
    def _generate_answer(self, question: str, analyzer: QuestionAnalyzer) -> str:
        """Generate answer using Gemini with context"""
        try:
            prompt = self._build_context_prompt(question, analyzer)
            
            print(f"🤖 Generating answer for: {question[:50]}...")
            response = _client.generate_content(prompt)
            answer = response.text.strip()
            
            # Clean up the answer
            answer = re.sub(r'^(answer:|response:|here\'s.*?:)', '', answer, flags=re.IGNORECASE).strip()
            
            return answer
        
        except Exception as e:
            print(f"❌ Error generating answer: {e}")
            return "Unable to generate response at this time."
    
    def answer_question(self, question: str, job_context: str = "") -> Tuple[str, Dict]:
        """
        Main method to answer a question with caching and analysis
        
        Returns:
            Tuple of (answer, metadata)
        """
        _stats['calls'] += 1
        
        # Analyze question
        analyzer = QuestionAnalyzer(question)
        
        # Check if should skip
        if analyzer.should_skip():
            return "Skip this question", {'source': 'skip', 'analyzer': analyzer}
        
        # Check cache
        cached_answer = self._find_similar_cached_question(question)
        if cached_answer:
            _stats['cached'] += 1
            print(f"✅ Using cached answer")
            return cached_answer, {'source': 'cache', 'analyzer': analyzer}
        
        # Generate new answer
        answer = self._generate_answer(question, analyzer)
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
            'cache_hit_rate': _stats['cached'] / max(_stats['calls'], 1),
            'cache_size': len(_qa_cache),
        }


# Global engine instance
_engine = None

def get_engine() -> GeminiAnswerEngine:
    """Get or create the answer engine"""
    global _engine
    if _engine is None:
        _engine = GeminiAnswerEngine()
    return _engine


def answer_question(question: str, job_context: str = "") -> str:
    """
    Answer a job application question
    
    Args:
        question: The question to answer
        job_context: Optional job/company context
    
    Returns:
        The answer string
    """
    engine = get_engine()
    answer, metadata = engine.answer_question(question, job_context)
    return answer


def get_stats() -> Dict:
    """Get API usage statistics"""
    engine = get_engine()
    return engine.get_stats()


# Backward compatibility
def bard_flash_response(question: str, context: str = "") -> str:
    """Backward compatible function"""
    return answer_question(question, context)


if __name__ == "__main__":
    # Test
    engine = GeminiAnswerEngine()
    
    test_questions = [
        "What are your top 3 strengths?",
        "Why do you want to join our company?",
        "Are you willing to relocate?",
    ]
    
    for q in test_questions:
        print(f"\n📝 Q: {q}")
        answer = engine.answer_question(q)[0]
        print(f"✅ A: {answer}")
    
    print(f"\n📊 Stats: {engine.get_stats()}")
