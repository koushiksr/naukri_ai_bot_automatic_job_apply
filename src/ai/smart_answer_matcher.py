"""
Smart Answer Matcher - Intelligent Q&A matching with value extraction
Handles CTC conversion, regex patterns, and context-aware matching
"""

import re
from typing import Tuple, Optional, Dict
from enum import Enum

class AnswerFormat(Enum):
    """Different answer formats"""
    EXACT = "exact"
    REGEX = "regex"
    KEYWORD = "keyword"
    NUMERIC = "numeric"
    BOOLEAN = "boolean"
    SALARY = "salary"
    DATE = "date"

class SmartAnswerMatcher:
    """Intelligent answer matching and extraction"""
    
    def __init__(self, current_ctc_annual: int = 500000, expected_ctc_annual: int = 800000):
        """
        Initialize with salary values
        Args:
            current_ctc_annual: Current CTC in annual amount (default: 500000)
            expected_ctc_annual: Expected CTC in annual amount (default: 800000)
        """
        self.current_ctc = current_ctc_annual
        self.expected_ctc = expected_ctc_annual
        
        # Pre-compute common values
        self.current_lakhs = round(current_ctc_annual / 100000, 1)
        self.expected_lakhs = round(expected_ctc_annual / 100000, 1)
        self.current_monthly = round(current_ctc_annual / 12)
        self.expected_monthly = round(expected_ctc_annual / 12)
        
        # Define predefined patterns (most common questions)
        self.answer_patterns = self._build_patterns()
    
    def _build_patterns(self) -> Dict:
        """Build comprehensive answer patterns for common questions"""
        return {
            # ===== SALARY / CTC QUESTIONS =====
            'current_ctc': {
                'keywords': ['current ctc', 'current salary', 'current compensation', 'current pay'],
                'formats': {
                    'annual': str(self.current_ctc),
                    'lakhs': str(self.current_lakhs),
                    'monthly': str(self.current_monthly),
                    'lpa': f"{self.current_lakhs} LPA",
                },
                'priority': 'annual',  # Return annual by default
            },
            'expected_ctc': {
                'keywords': ['expected ctc', 'expected salary', 'salary expectation', 'expected compensation'],
                'formats': {
                    'annual': str(self.expected_ctc),
                    'lakhs': str(self.expected_lakhs),
                    'monthly': str(self.expected_monthly),
                    'lpa': f"{self.expected_lakhs} LPA",
                },
                'priority': 'annual',
            },
            'take_home': {
                'keywords': ['take home', 'net salary', 'in hand'],
                'formats': {
                    'monthly': str(round(self.current_monthly * 0.7)),  # Assume 30% tax
                    'annual': str(round(self.current_ctc * 0.7)),
                },
                'priority': 'monthly',
            },
            
            # ===== EXPERIENCE QUESTIONS =====
            'total_experience': {
                'keywords': ['total experience', 'years of experience', 'how many years', 'experience overall'],
                'answer': '2.5',  # Will be read from config
            },
            'python_experience': {
                'keywords': ['python', 'experience.*python', 'python.*experience', 'years.*python'],
                'answer': '2.5',
            },
            'ml_experience': {
                'keywords': ['machine learning', 'ml experience', 'deep learning'],
                'answer': '2.5',
            },
            'data_science_experience': {
                'keywords': ['data science', 'analytics', 'data analyst'],
                'answer': '2.5',
            },
            
            # ===== LOCATION / RELOCATION =====
            'current_location': {
                'keywords': ['current location', 'where are you', 'based in', 'location now'],
                'answer': 'Bangalore',
            },
            'willing_relocate': {
                'keywords': ['willing to relocate', 'open to relocation', 'relocate', 'willing move'],
                'answer': 'Yes',
            },
            'preferred_location': {
                'keywords': ['preferred location', 'prefer to work', 'choice of location'],
                'answer': 'Bangalore, Remote',
            },
            
            # ===== NOTICE PERIOD =====
            'notice_period': {
                'keywords': ['notice period', 'notice', 'availability', 'can start'],
                'answer': '0',
            },
            'availability': {
                'keywords': ['available to join', 'when can you start', 'earliest start date'],
                'answer': 'Immediate',
            },
            
            # ===== COMPANY / JOB HISTORY =====
            'current_company': {
                'keywords': ['current company', 'working at', 'employed at', 'company name'],
                'answer': 'Capgemini',
            },
            'current_designation': {
                'keywords': ['current designation', 'current role', 'job title', 'position'],
                'answer': 'AI/ML Engineer',
            },
            'previous_company': {
                'keywords': ['previous company', 'last company', 'worked at'],
                'answer': 'QuGates Technologies',
            },
            
            # ===== SKILLS =====
            'programming_languages': {
                'keywords': ['programming language', 'languages', 'language skills'],
                'answer': 'Python, JavaScript, SQL',
            },
            'technical_skills': {
                'keywords': ['technical skills', 'technical expertise', 'tools'],
                'answer': 'Python, ML, Data Analysis, Problem Solving',
            },
            'soft_skills': {
                'keywords': ['soft skill', 'communication', 'teamwork', 'strength'],
                'answer': 'Problem Solving, Communication, Teamwork',
            },
            
            # ===== MOTIVATION =====
            'why_join': {
                'keywords': ['why.*company', 'why.*role', 'interested in', 'why join'],
                'answer': 'Growing tech, challenging work, team culture',
            },
            'career_goal': {
                'keywords': ['career goal', 'future plan', 'career path'],
                'answer': 'Senior ML Engineer, Tech Lead',
            },
            
            # ===== YES/NO QUESTIONS =====
            'willing_travel': {
                'keywords': ['willing to travel', 'travel', 'commute'],
                'answer': 'Yes',
            },
            'open_to_shift': {
                'keywords': ['open to shift', 'shift work', 'flexible timing'],
                'answer': 'Yes',
            },
            'ready_to_work': {
                'keywords': ['ready to work', 'can work', 'ready for'],
                'answer': 'Yes',
            },
        }
    
    def _normalize_question(self, question: str) -> str:
        """Normalize question for matching"""
        return re.sub(r'\s+', ' ', question.lower().strip())
    
    def convert_salary_format(self, value: str, to_format: str) -> str:
        """
        Convert salary between formats
        Examples: 
            "5" + "annual" → "500000"
            "500000" + "lakhs" → "5"
            "8 lpa" + "annual" → "800000"
        """
        # Extract number from input
        num_match = re.search(r'[\d.]+', value)
        if not num_match:
            return value
        
        num = float(num_match.group())
        
        # Determine input format and convert
        if 'lpa' in value.lower() or 'lakh' in value.lower() or (0 < num < 100):
            # Input is in lakhs
            num_annual = int(num * 100000)
        else:
            # Input is in rupees
            num_annual = int(num)
        
        # Convert to target format
        if to_format == 'annual' or to_format == 'rupees':
            return str(num_annual)
        elif to_format == 'lakhs' or to_format == 'lpa':
            lakhs = num_annual / 100000
            return str(lakhs if lakhs == int(lakhs) else f"{lakhs:.1f}")
        elif to_format == 'monthly':
            return str(round(num_annual / 12))
        
        return value
    
    def extract_salary_from_context(self, question: str) -> Optional[Dict]:
        """Extract salary amounts mentioned in question"""
        # Look for numbers with potential salary keywords
        matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:lakh|lac|lpa|lakhs|lacs|rupees|rs)', question, re.IGNORECASE)
        
        if matches:
            amounts = []
            for match in matches:
                annual = int(float(match) * 100000) if float(match) < 100 else int(float(match))
                amounts.append({
                    'lakhs': float(match),
                    'annual': annual,
                    'monthly': annual // 12,
                })
            return {'salaries': amounts, 'count': len(amounts)}
        
        return None
    
    def find_best_answer(self, question: str, use_llm_fallback: bool = True) -> Tuple[Optional[str], str]:
        """
        Find best predefined answer for question
        Returns: (answer, source) where source is 'predefined', 'extracted', or 'llm_needed'
        """
        q_normalized = self._normalize_question(question)
        
        # Try exact keyword matching
        for pattern_key, pattern_data in self.answer_patterns.items():
            keywords = pattern_data.get('keywords', [])
            
            for keyword in keywords:
                if re.search(keyword, q_normalized):
                    # Found matching pattern
                    if 'answer' in pattern_data:
                        return (pattern_data['answer'], 'predefined_direct')
                    
                    elif 'formats' in pattern_data:
                        # Return priority format or context-aware format
                        priority = pattern_data.get('priority', 'annual')
                        answer = pattern_data['formats'].get(priority)
                        return (answer, 'predefined_formatted')
        
        # Try salary extraction from question content
        salary_context = self.extract_salary_from_context(question)
        if salary_context:
            # If asking about salary in question, use that
            if 'expected' in q_normalized or 'offer' in q_normalized:
                return (str(salary_context['salaries'][0]['annual']), 'extracted_from_question')
            elif 'current' in q_normalized:
                return (str(salary_context['salaries'][0]['annual']), 'extracted_from_question')
        
        # No predefined answer found
        if use_llm_fallback:
            return (None, 'llm_needed')
        else:
            return (None, 'no_match')
    
    def match_answer_to_options(self, answer: str, options: list) -> Optional[str]:
        """
        Match AI-generated answer to available form options
        Handles partial matches, synonyms, and close values
        """
        if not options:
            return None
        
        answer_lower = answer.lower().strip()
        
        # Exact match first
        for opt in options:
            if opt.lower() == answer_lower:
                return opt
        
        # Partial match
        for opt in options:
            if answer_lower in opt.lower() or opt.lower() in answer_lower:
                return opt
        
        # For numbers (like salary), find closest value
        try:
            answer_num = float(re.search(r'[\d.]+', answer).group())
            best_match = None
            best_diff = float('inf')
            
            for opt in options:
                opt_match = re.search(r'[\d.]+', opt)
                if opt_match:
                    opt_num = float(opt_match.group())
                    diff = abs(answer_num - opt_num)
                    if diff < best_diff:
                        best_diff = diff
                        best_match = opt
            
            if best_match and best_diff < answer_num * 0.1:  # Within 10%
                return best_match
        except:
            pass
        
        # No match found
        return None


# Example usage and testing
if __name__ == "__main__":
    matcher = SmartAnswerMatcher(current_ctc_annual=500000, expected_ctc_annual=800000)
    
    test_questions = [
        "What is your current CTC?",
        "What is your expected salary?",
        "How many years of Python experience?",
        "Current location?",
        "Are you willing to relocate?",
        "What is your notice period?",
        "Why do you want to join our company?",
    ]
    
    print("=" * 70)
    print("SMART ANSWER MATCHER - TEST")
    print("=" * 70)
    
    for q in test_questions:
        answer, source = matcher.find_best_answer(q)
        print(f"\nQ: {q}")
        print(f"A: {answer} [{source}]")
    
    print("\n" + "=" * 70)
    print("SALARY CONVERSION TEST")
    print("=" * 70)
    print(f"5 lakhs → annual: {matcher.convert_salary_format('5', 'annual')}")
    print(f"500000 → lakhs: {matcher.convert_salary_format('500000', 'lakhs')}")
    print(f"8 LPA → monthly: {matcher.convert_salary_format('8 LPA', 'monthly')}")
