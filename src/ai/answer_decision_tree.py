"""
Centralized Answer Decision Tree System
Single configuration file for all Q&A patterns with decision logic
Maintains key-value pairs and similar question detection
"""

from typing import Dict, Optional, Tuple, List
from enum import Enum
import re

class AnswerCategory(Enum):
    """Answer categories with decision logic"""
    SALARY = "salary"
    EXPERIENCE = "experience"
    LOCATION = "location"
    AVAILABILITY = "availability"
    COMPANY = "company"
    SKILLS = "skills"
    MOTIVATION = "motivation"
    YES_NO = "yes_no"
    EDUCATION = "education"
    LANGUAGES = "languages"

# ===== CENTRALIZED CONFIGURATION =====
ANSWER_CONFIG = {
    # ===== CANDIDATE PROFILE =====
    "candidate_profile": {
        "name": "Your Name",
        "experience_years": 2.5,
        "current_company": "Capgemini",
        "current_designation": "AI/ML Engineer",
        "previous_company": "QuGates Technologies",
        "current_location": "Bangalore",
        "education": {
            "degree": "B.Tech",
            "field": "Computer Science",
            "university": "Your University"
        },
    },
    
    # ===== SALARY CONFIGURATION (Core Values) =====
    "salary": {
        "current": {
            "annual": 500000,          # Source of truth
            "lakhs": 5,                # Calculated: annual / 100000
            "monthly": 41667,          # Calculated: annual / 12
            "take_home_monthly": 29167,  # Calculated: annual * 0.7 / 12
        },
        "expected": {
            "annual": 800000,
            "lakhs": 8,
            "monthly": 66667,
            "take_home_monthly": 46667,
        },
        # Similar question patterns for salary
        "patterns": {
            "current": [
                "current ctc", "current salary", "current compensation", "current pay",
                "current package", "current earnings", "current income",
                "what.*current.*salary", "how much.*current", "ctc now"
            ],
            "expected": [
                "expected ctc", "expected salary", "salary expectation", "expected compensation",
                "salary range", "ctc expectation", "target salary", "desired salary",
                "what.*expect.*salary", "how much.*expect", "ask"
            ],
            "take_home": [
                "take home", "net salary", "in hand", "home salary", "net pay",
                "after tax", "disposable", "hand money"
            ],
            "monthly": [
                "monthly salary", "monthly ctc", "per month", "monthly income",
                "monthly earnings", "monthly pay"
            ],
            "by_format": {
                "lakhs": ["lakh", "lac", "lpa", "in lakhs", "in lacs"],
                "rupees": ["rupees", "rs", "₹", "annual", "yearly"],
                "monthly": ["monthly", "month", "per month"]
            }
        },
    },
    
    # ===== EXPERIENCE CONFIGURATION =====
    "experience": {
        "overall": 2.5,  # Default experience
        "by_skill": {  # Technology-specific experience
            "python": 2.5,
            "machine learning": 2.5,
            "ml": 2.5,
            "deep learning": 2.0,
            "data science": 2.5,
            "data analysis": 2.5,
            "data analyst": 2.5,
            "sql": 2.5,
            "javascript": 1.5,
            "java": 1.0,
            "docker": 1.5,
            "kubernetes": 1.0,
            "aws": 1.5,
            "cloud": 1.5,
            "devops": 1.0,
            "react": 1.5,
            "django": 2.0,
            "flask": 1.5,
        },
        "patterns": {
            "total": [
                "total experience", "years of experience", "work experience",
                "how many years", "experience overall", "professional experience"
            ],
            "specific": [
                "experience.*", "years.*", "how many.*", "background.*",
                "expertise.*", "knowledge.*"
            ]
        }
    },
    
    # ===== LOCATION CONFIGURATION =====
    "location": {
        "current": "Bangalore",
        "preferred": ["Bangalore", "Remote"],
        "patterns": {
            "current": [
                "current location", "where are you", "based in", "city", "location now",
                "current city", "living in"
            ],
            "willing_relocate": [
                "willing to relocate", "open to relocation", "relocate", "willing move",
                "can relocate", "open to relocation", "willing to move", "ready to relocate"
            ],
            "preferred": [
                "preferred location", "prefer to work", "choice of location",
                "ideal location", "where.*like.*work"
            ]
        }
    },
    
    # ===== AVAILABILITY CONFIGURATION =====
    "availability": {
        "notice_period": "0",
        "can_start": "Immediate",
        "patterns": {
            "notice_period": [
                "notice period", "notice", "how much notice", "notice days",
                "notice duration", "notice requirement"
            ],
            "can_start": [
                "available to join", "when can you start", "earliest start date",
                "can you join", "when can you", "when.*available", "ready to start"
            ]
        }
    },
    
    # ===== COMPANY CONFIGURATION =====
    "company": {
        "current": "Capgemini",
        "current_role": "AI/ML Engineer",
        "previous": "QuGates Technologies",
        "patterns": {
            "current": [
                "current company", "working at", "employed at", "company name",
                "where do you work", "current employer"
            ],
            "current_role": [
                "current role", "current designation", "job title", "position",
                "current position", "what.*do.*do"
            ],
            "previous": [
                "previous company", "last company", "worked at", "last employer",
                "before.*company", "prior.*company"
            ]
        }
    },
    
    # ===== SKILLS CONFIGURATION =====
    "skills": {
        "technical": ["Python", "ML", "Data Analysis", "Problem Solving"],
        "languages": ["Python", "JavaScript", "SQL"],
        "tools": ["Python", "Docker", "AWS", "PostgreSQL"],
        "frameworks": ["Django", "Flask", "React"],
        "databases": ["PostgreSQL", "MongoDB", "Redis"],
        "soft_skills": ["Communication", "Teamwork", "Problem Solving"],
        "patterns": {
            "technical": [
                "technical skills", "technical expertise", "technical knowledge",
                "technical abilities", "tech skills"
            ],
            "programming": [
                "programming language", "languages", "language skills",
                "programming skills", "coding"
            ],
            "strength": [
                "strength", "strengths", "strong in", "good at", "expertise",
                "competent", "proficient", "knowledge"
            ],
            "tools": [
                "tools", "technologies", "tech stack", "tools and tech",
                "frameworks", "libraries"
            ]
        }
    },
    
    # ===== MOTIVATION CONFIGURATION =====
    "motivation": {
        "why_join": "Growing tech, challenging work, team culture",
        "career_goal": "Senior ML Engineer, Tech Lead",
        "patterns": {
            "why_join": [
                "why.*company", "why.*role", "interested in", "why join",
                "why.*us", "reason for joining", "attraction"
            ],
            "career_goal": [
                "career goal", "future plan", "career path", "where.*see",
                "long term", "next step"
            ]
        }
    },
    
    # ===== YES/NO CONFIGURATION =====
    "yes_no": {
        "willing_travel": "Yes",
        "open_to_shift": "Yes",
        "ready_to_work": "Yes",
        "work_weekends": "Sometimes",
        "patterns": {
            "travel": [
                "willing to travel", "open to travel", "can travel",
                "travel required", "willing.*travel"
            ],
            "shift": [
                "open to shift", "shift work", "flexible timing", "shift.*work",
                "willing.*shift"
            ],
            "ready": [
                "ready to work", "can you work", "ready for", "prepared",
                "comfortable"
            ],
            "weekends": [
                "work on weekends", "weekends", "work weekends", "weekend work",
                "weekend."
            ]
        }
    },
    
    # ===== EDUCATION CONFIGURATION =====
    "education": {
        "degree": "B.Tech",
        "field": "Computer Science",
        "patterns": {
            "degree": [
                "degree", "qualification", "education", "studied",
                "graduated", "bachelor", "master"
            ],
            "field": [
                "field", "specialization", "major", "branch", "stream"
            ]
        }
    },
    
    # ===== LANGUAGES CONFIGURATION =====
    "languages": {
        "english": "Fluent",
        "hindi": "Native",
        "patterns": {
            "english": [
                "english", "language", "language proficiency", "speak english",
                "english fluency"
            ]
        }
    },
}

# ===== DECISION TREE LOGIC =====
class AnswerDecisionTree:
    """Decision tree for intelligent answer selection"""
    
    def __init__(self, config: Dict = None):
        self.config = config or ANSWER_CONFIG
    
    def find_answer(self, question: str) -> Tuple[Optional[str], str]:
        """
        Find answer using decision tree logic
        Returns: (answer, category)
        """
        q_lower = question.lower()
        
        # Decision Tree: Check categories in priority order
        
        # 1. SALARY - Most specific patterns first
        if self._match_patterns(q_lower, self.config["salary"]["patterns"]["current"]):
            return self._get_salary_answer("current", q_lower), "salary_current"
        
        if self._match_patterns(q_lower, self.config["salary"]["patterns"]["expected"]):
            return self._get_salary_answer("expected", q_lower), "salary_expected"
        
        if self._match_patterns(q_lower, self.config["salary"]["patterns"]["take_home"]):
            return self._get_salary_answer("take_home", q_lower), "salary_take_home"
        
        # 2. EXPERIENCE
        if self._match_patterns(q_lower, self.config["experience"]["patterns"]["total"]):
            return str(self.config["experience"]["overall"]), "experience_total"
        
        # Check if asking about specific technology
        for tech, years in self.config["experience"]["by_skill"].items():
            if tech in q_lower:
                return str(years), f"experience_{tech}"
        
        # 3. LOCATION
        if self._match_patterns(q_lower, self.config["location"]["patterns"]["current"]):
            return self.config["location"]["current"], "location_current"
        
        if self._match_patterns(q_lower, self.config["location"]["patterns"]["willing_relocate"]):
            return "Yes", "location_relocate"
        
        if self._match_patterns(q_lower, self.config["location"]["patterns"]["preferred"]):
            return ", ".join(self.config["location"]["preferred"]), "location_preferred"
        
        # 4. AVAILABILITY
        if self._match_patterns(q_lower, self.config["availability"]["patterns"]["notice_period"]):
            return self.config["availability"]["notice_period"], "availability_notice"
        
        if self._match_patterns(q_lower, self.config["availability"]["patterns"]["can_start"]):
            return self.config["availability"]["can_start"], "availability_start"
        
        # 5. COMPANY
        if self._match_patterns(q_lower, self.config["company"]["patterns"]["current"]):
            return self.config["company"]["current"], "company_current"
        
        if self._match_patterns(q_lower, self.config["company"]["patterns"]["current_role"]):
            return self.config["company"]["current_role"], "company_role"
        
        if self._match_patterns(q_lower, self.config["company"]["patterns"]["previous"]):
            return self.config["company"]["previous"], "company_previous"
        
        # 6. SKILLS
        if self._match_patterns(q_lower, self.config["skills"]["patterns"]["strength"]):
            return ", ".join(self.config["skills"]["technical"]), "skills_technical"
        
        if self._match_patterns(q_lower, self.config["skills"]["patterns"]["programming"]):
            return ", ".join(self.config["skills"]["languages"]), "skills_languages"
        
        # 7. MOTIVATION
        if self._match_patterns(q_lower, self.config["motivation"]["patterns"]["why_join"]):
            return self.config["motivation"]["why_join"], "motivation_why"
        
        if self._match_patterns(q_lower, self.config["motivation"]["patterns"]["career_goal"]):
            return self.config["motivation"]["career_goal"], "motivation_goal"
        
        # 8. YES/NO
        if self._match_patterns(q_lower, self.config["yes_no"]["patterns"]["travel"]):
            return self.config["yes_no"]["willing_travel"], "yes_no_travel"
        
        if self._match_patterns(q_lower, self.config["yes_no"]["patterns"]["shift"]):
            return self.config["yes_no"]["open_to_shift"], "yes_no_shift"
        
        if self._match_patterns(q_lower, self.config["yes_no"]["patterns"]["weekends"]):
            return self.config["yes_no"]["work_weekends"], "yes_no_weekends"
        
        # 9. EDUCATION
        if self._match_patterns(q_lower, self.config["education"]["patterns"]["degree"]):
            return f"{self.config['education']['degree']} {self.config['education']['field']}", "education"
        
        # 10. LANGUAGES
        if self._match_patterns(q_lower, self.config["languages"]["patterns"]["english"]):
            return f"English - {self.config['languages']['english']}", "language_english"
        
        # No match found
        return None, "no_match"
    
    def _match_patterns(self, question: str, patterns: List[str]) -> bool:
        """Check if question matches any pattern"""
        for pattern in patterns:
            if re.search(pattern, question):
                return True
        return False
    
    def _get_salary_answer(self, salary_type: str, question: str) -> str:
        """Get salary answer with format detection"""
        salary_data = self.config["salary"][salary_type]
        
        # Detect requested format from question
        if self._match_patterns(question, self.config["salary"]["patterns"]["by_format"]["lakhs"]):
            return str(int(salary_data["lakhs"]))
        elif self._match_patterns(question, self.config["salary"]["patterns"]["by_format"]["monthly"]):
            return str(salary_data["monthly"])
        else:
            # Default: return annual
            return str(salary_data["annual"])
    
    def get_config_value(self, path: str) -> any:
        """
        Get any config value by path
        Example: "salary.current.annual" → 500000
        """
        keys = path.split(".")
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value
    
    def set_config_value(self, path: str, value: any) -> bool:
        """
        Set any config value by path
        Example: set_config_value("salary.current.annual", 550000)
        """
        keys = path.split(".")
        config = self.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
        return True


# ===== TESTING =====
if __name__ == "__main__":
    tree = AnswerDecisionTree()
    
    print("=" * 70)
    print("CENTRALIZED ANSWER DECISION TREE - TEST")
    print("=" * 70)
    
    test_questions = [
        "What is your current CTC?",
        "Expected salary in lakhs?",
        "Monthly take-home?",
        "Python experience?",
        "Current location?",
        "Willing to relocate?",
        "Notice period?",
        "Can you start immediately?",
        "Current company?",
        "Current role?",
        "Why do you want to join?",
        "Career goals?",
        "Are you willing to travel?",
        "Education?",
    ]
    
    for question in test_questions:
        answer, category = tree.find_answer(question)
        print(f"\nQ: {question}")
        print(f"A: {answer} [{category}]")
    
    print("\n" + "=" * 70)
    print("CONFIG ACCESS TEST")
    print("=" * 70)
    
    print(f"\nCurrent Annual Salary: {tree.get_config_value('salary.current.annual')}")
    print(f"Expected Lakhs: {tree.get_config_value('salary.expected.lakhs')}")
    print(f"Experience Years: {tree.get_config_value('experience.overall')}")
    
    print("\n" + "=" * 70)
    print("✅ Decision Tree Ready!")
    print("=" * 70)
