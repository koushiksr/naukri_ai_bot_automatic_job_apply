"""
Question Analyzer - Classify and analyze job application questions
Determines best strategy for answering each question type
"""

import re
from typing import Dict, List, Tuple
from enum import Enum

class QuestionType(Enum):
    """Types of questions in job applications"""
    SKILLS_STRENGTHS = "skills_strengths"
    EXPERIENCE = "experience"
    LEADERSHIP = "leadership"
    PROBLEM_SOLVING = "problem_solving"
    MOTIVATION = "motivation"
    TECHNICAL = "technical"
    AVAILABILITY = "availability"
    RELOCATION = "relocation"
    SALARY = "salary"
    LANGUAGE = "language"
    COMPANY_CULTURE = "company_culture"
    WORK_STYLE = "work_style"
    EDUCATION = "education"
    OTHER = "other"


class QuestionAnalyzer:
    """Analyzes questions to determine type and best answering strategy"""
    
    QUESTION_PATTERNS = {
        QuestionType.SKILLS_STRENGTHS: [
            r'(strength|weakness|skill|expertise|competent|proficient|knowledge)',
            r'(what.*?good at|good.*?at|capable of)',
            r'(technical.*?skill|programming.*?skill)',
        ],
        QuestionType.EXPERIENCE: [
            r'(experience.*?year|years.*?experience|work.*?experience)',
            r'(background|worked.*?before)',
            r'(previously|earlier.*?worked|past.*?work)',
        ],
        QuestionType.LEADERSHIP: [
            r'(leadership|lead.*?team|manage|mentor|supervise)',
            r'(team.*?lead|leading.*?team|manage.*?people)',
        ],
        QuestionType.PROBLEM_SOLVING: [
            r'(challenge|difficult|problem|overcome|solve)',
            r'(handled.*?crisis|managed.*?conflict|faced.*?issue)',
        ],
        QuestionType.MOTIVATION: [
            r'(why.*?job|interested.*?position|motivat)',
            r'(why.*?company|why.*?role|career.*?goal)',
        ],
        QuestionType.TECHNICAL: [
            r'(code|programming|technology|stack|framework|database)',
            r'(technical.*?question|coding|develop)',
        ],
        QuestionType.AVAILABILITY: [
            r'(notice.*?period|availability|when.*?start|join.*?date)',
            r'(how soon|available.*?from)',
        ],
        QuestionType.RELOCATION: [
            r'(relocate|relocation|willing.*?move|location)',
            r'(work.*?location|office.*?location)',
        ],
        QuestionType.SALARY: [
            r'(salary|compensation|pay|expectation|ctc)',
        ],
        QuestionType.LANGUAGE: [
            r'(language|speak|fluent|english)',
        ],
        QuestionType.COMPANY_CULTURE: [
            r'(culture|work.*?environment|team.*?environment)',
        ],
        QuestionType.WORK_STYLE: [
            r'(work.*?style|prefer.*?work|team.*?player|independent)',
        ],
        QuestionType.EDUCATION: [
            r'(education|degree|qualification|studied|university)',
        ],
    }
    
    def __init__(self, question: str):
        self.question = question
        self.question_lower = question.lower()
        self.question_type = self._classify()
        self.confidence = self._calculate_confidence()
        self.strategy = self._determine_strategy()
    
    def _classify(self) -> QuestionType:
        """Classify the question type"""
        for qtype, patterns in self.QUESTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, self.question_lower):
                    return qtype
        return QuestionType.OTHER
    
    def _calculate_confidence(self) -> float:
        """Calculate confidence in classification (0.0 to 1.0)"""
        if self.question_type == QuestionType.OTHER:
            return 0.5
        
        pattern_count = len(self.QUESTION_PATTERNS[self.question_type])
        matches = 0
        for pattern in self.QUESTION_PATTERNS[self.question_type]:
            if re.search(pattern, self.question_lower):
                matches += 1
        
        return min(matches / max(pattern_count, 1), 1.0)
    
    def _determine_strategy(self) -> Dict:
        """Determine answering strategy based on question type"""
        strategies = {
            QuestionType.SKILLS_STRENGTHS: {
                'focus': 'technical_and_soft',
                'length': 'medium',
                'examples': True,
                'context': 'resume_skills',
                'tone': 'confident',
            },
            QuestionType.EXPERIENCE: {
                'focus': 'professional_background',
                'length': 'medium',
                'examples': True,
                'context': 'resume_experience',
                'tone': 'professional',
            },
            QuestionType.LEADERSHIP: {
                'focus': 'management_ability',
                'length': 'medium',
                'examples': True,
                'context': 'resume_companies',
                'tone': 'assertive',
            },
            QuestionType.PROBLEM_SOLVING: {
                'focus': 'analytical_ability',
                'length': 'medium',
                'examples': True,
                'context': 'problem_solving',
                'tone': 'thoughtful',
            },
            QuestionType.MOTIVATION: {
                'focus': 'career_goals',
                'length': 'medium',
                'examples': False,
                'context': 'job_description',
                'tone': 'enthusiastic',
            },
            QuestionType.TECHNICAL: {
                'focus': 'technical_details',
                'length': 'long',
                'examples': True,
                'context': 'resume_skills',
                'tone': 'expert',
            },
            QuestionType.AVAILABILITY: {
                'focus': 'availability',
                'length': 'short',
                'examples': False,
                'context': 'none',
                'tone': 'direct',
            },
            QuestionType.RELOCATION: {
                'focus': 'relocation_willingness',
                'length': 'short',
                'examples': False,
                'context': 'none',
                'tone': 'flexible',
            },
            QuestionType.SALARY: {
                'focus': 'salary_expectations',
                'length': 'short',
                'examples': False,
                'context': 'experience_level',
                'tone': 'professional',
            },
            QuestionType.LANGUAGE: {
                'focus': 'language_proficiency',
                'length': 'short',
                'examples': False,
                'context': 'resume_languages',
                'tone': 'direct',
            },
            QuestionType.COMPANY_CULTURE: {
                'focus': 'culture_fit',
                'length': 'medium',
                'examples': False,
                'context': 'company_research',
                'tone': 'thoughtful',
            },
            QuestionType.WORK_STYLE: {
                'focus': 'work_approach',
                'length': 'medium',
                'examples': True,
                'context': 'none',
                'tone': 'balanced',
            },
            QuestionType.EDUCATION: {
                'focus': 'qualifications',
                'length': 'medium',
                'examples': False,
                'context': 'resume_qualifications',
                'tone': 'formal',
            },
            QuestionType.OTHER: {
                'focus': 'general',
                'length': 'medium',
                'examples': False,
                'context': 'resume',
                'tone': 'professional',
            }
        }
        return strategies.get(self.question_type, strategies[QuestionType.OTHER])
    
    def get_prompt_template(self) -> str:
        """Get AI prompt template based on question type"""
        templates = {
            QuestionType.SKILLS_STRENGTHS: """Based on the candidate's resume and the question asked, provide a confident answer highlighting relevant technical and soft skills. Keep it concise (2-3 sentences). Include specific examples where relevant.""",
            
            QuestionType.EXPERIENCE: """Based on the candidate's professional background, answer the experience question. Highlight relevant work history and achievements. Keep it concise (2-3 sentences).""",
            
            QuestionType.LEADERSHIP: """Answer the leadership question by highlighting relevant management experience and achievements from the resume. Show ability to lead and mentor. Keep it concise (2-3 sentences).""",
            
            QuestionType.PROBLEM_SOLVING: """Answer the problem-solving question by describing analytical approach and a relevant achievement. Show critical thinking skills. Keep it concise (2-3 sentences).""",
            
            QuestionType.MOTIVATION: """Answer why interested in this position by highlighting career goals and role alignment. Be enthusiastic but professional. Keep it concise (2-3 sentences).""",
            
            QuestionType.TECHNICAL: """Provide a detailed technical answer demonstrating expertise. Reference specific technologies or approaches. Keep it clear and professional. Keep it concise (2-4 sentences).""",
            
            QuestionType.AVAILABILITY: """Provide a direct, professional answer about availability. Be specific if possible.""",
            
            QuestionType.RELOCATION: """Answer the relocation question professionally. Be straightforward about willingness and flexibility.""",
            
            QuestionType.SALARY: """Provide a professional response about salary expectations based on experience level. Be reasonable and flexible.""",
            
            QuestionType.LANGUAGE: """Directly answer the language proficiency question with specifics.""",
            
            QuestionType.COMPANY_CULTURE: """Answer the culture fit question showing understanding of company values and how you align with them.""",
            
            QuestionType.WORK_STYLE: """Describe your work style/approach in a balanced, professional way with relevant examples.""",
            
            QuestionType.EDUCATION: """Answer the education question by highlighting relevant qualifications and learning achievements from the resume.""",
            
            QuestionType.OTHER: """Provide a professional, relevant answer to this question. Keep it concise and focused.""",
        }
        return templates.get(self.question_type, templates[QuestionType.OTHER])
    
    def should_skip(self) -> bool:
        """Determine if question should be skipped"""
        skip_keywords = ['optional', 'skip', 'n/a', 'not applicable', 'prefer not to answer']
        return any(keyword in self.question_lower for keyword in skip_keywords)


if __name__ == "__main__":
    test_questions = [
        "What are your top 3 strengths?",
        "Are you willing to relocate?",
        "What is your experience with Python?",
        "How would you handle a difficult situation?",
    ]
    
    for q in test_questions:
        analyzer = QuestionAnalyzer(q)
        print(f"\nQ: {q}")
        print(f"  Type: {analyzer.question_type.value}")
        print(f"  Confidence: {analyzer.confidence:.2%}")
        print(f"  Strategy: {analyzer.strategy}")
