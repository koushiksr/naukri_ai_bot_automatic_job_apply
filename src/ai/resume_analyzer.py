"""
Resume Analyzer - Extract and optimize resume data for job applications
Provides contextual information for better AI answers
"""

import re
from typing import Dict, List, Set
import json
import os

class ResumeAnalyzer:
    """Analyzes resume to extract key information for better answers"""
    
    def __init__(self, resume_text: str):
        self.resume_text = resume_text.lower()
        self.skills = self._extract_skills()
        self.experience_years = self._extract_experience()
        self.companies = self._extract_companies()
        self.qualifications = self._extract_qualifications()
        self.languages = self._extract_languages()
        self.summary = self._create_summary()
    
    def _extract_skills(self) -> Set[str]:
        """Extract technical and soft skills"""
        skills_keywords = {
            # Programming
            'python', 'javascript', 'typescript', 'java', 'cpp', 'c++', 'c#', 'golang', 'rust', 'php',
            'sql', 'html', 'css', 'r', 'matlab', 'kotlin', 'swift', 'objective-c',
            
            # Frameworks & Libraries
            'react', 'angular', 'vue', 'django', 'flask', 'fastapi', 'spring', 'express', 'nodejs',
            'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy', 'opencv',
            'langchain', 'huggingface', 'openai', 'gemini',
            
            # Databases
            'postgres', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'firebase',
            'cassandra', 'dynamodb', 'oracle', 'sqlserver',
            
            # Tools & Platforms
            'docker', 'kubernetes', 'aws', 'gcp', 'azure', 'git', 'linux', 'macos',
            'jenkins', 'gitlab', 'github', 'jira', 'confluence',
            
            # Methodologies
            'agile', 'scrum', 'kanban', 'ci/cd', 'devops', 'microservices', 'rest api', 'graphql',
            'machine learning', 'deep learning', 'nlp', 'computer vision', 'rag', 'llm',
            
            # Soft Skills
            'leadership', 'communication', 'teamwork', 'problem solving', 'critical thinking',
            'project management', 'mentoring', 'presentation'
        }
        
        found_skills = set()
        for skill in skills_keywords:
            if skill in self.resume_text:
                found_skills.add(skill.title())
        
        return found_skills
    
    def _extract_experience(self) -> float:
        """Extract years of experience"""
        patterns = [
            r'(\d+)\s*(?:\+)?\s*years?\s*(?:of\s*)?(?:experience|exp)',
            r'(?:experience|exp).*?(\d+)\s*(?:\+)?\s*years?',
            r'(\d+)\s*(?:years?|yrs?)\s*(?:professional|work)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, self.resume_text)
            if matches:
                return float(matches[0])
        
        return 0.0
    
    def _extract_companies(self) -> List[str]:
        """Extract company names mentioned in resume"""
        # Common company name patterns
        companies = re.findall(r'(?:at|worked at|company:|employer:)\s*([A-Z][A-Za-z\s&.,]+?)(?:\n|,|$)', self.resume_text)
        return [c.strip().title() for c in companies if c.strip()]
    
    def _extract_qualifications(self) -> Set[str]:
        """Extract educational qualifications"""
        qualifications = set()
        degrees = ['b.tech', 'b.e', 'mtech', 'm.e', 'bsc', 'msc', 'ba', 'ma', 'bca', 'mca', 'mba']
        
        for degree in degrees:
            if degree in self.resume_text:
                qualifications.add(degree.upper())
        
        return qualifications
    
    def _extract_languages(self) -> Set[str]:
        """Extract programming languages"""
        languages = {
            'python', 'javascript', 'java', 'cpp', 'c#', 'go', 'rust', 'php',
            'typescript', 'kotlin', 'swift', 'r', 'matlab', 'sql'
        }
        found = {lang for lang in languages if lang in self.resume_text}
        return found
    
    def _create_summary(self) -> str:
        """Create a summary of the candidate profile"""
        profile_parts = []
        
        if self.experience_years:
            profile_parts.append(f"{self.experience_years}+ years of experience")
        
        if self.skills:
            top_skills = list(self.skills)[:5]
            profile_parts.append(f"Expertise in {', '.join(top_skills)}")
        
        if self.qualifications:
            profile_parts.append(f"Holds {', '.join(self.qualifications)}")
        
        return ". ".join(profile_parts) + "."
    
    def get_context_for_question(self, question: str) -> Dict:
        """Get relevant context for answering a specific question"""
        question_lower = question.lower()
        
        context = {
            'skills': self.skills,
            'experience_years': self.experience_years,
            'companies': self.companies,
            'qualifications': self.qualifications,
            'languages': self.languages,
            'summary': self.summary
        }
        
        # Add question-specific context
        if any(word in question_lower for word in ['strength', 'skill', 'expert', 'knowledge']):
            context['focus'] = 'skills'
        elif any(word in question_lower for word in ['experience', 'worked', 'year', 'duration']):
            context['focus'] = 'experience'
        elif any(word in question_lower for word in ['leadership', 'manage', 'team', 'lead']):
            context['focus'] = 'leadership'
        elif any(word in question_lower for word in ['challenge', 'problem', 'difficult', 'overcome']):
            context['focus'] = 'problem_solving'
        elif any(word in question_lower for word in ['willing', 'relocate', 'travel', 'location']):
            context['focus'] = 'relocation'
        elif any(word in question_lower for word in ['notice', 'availability', 'start', 'join']):
            context['focus'] = 'availability'
        
        return context


def load_resume(filename: str = "Resume.pdf") -> str:
    """Load and extract resume text"""
    try:
        if not os.path.exists(filename):
            return ""
        
        if filename.endswith('.pdf'):
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(filename)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                return text
            except ImportError:
                return ""
        else:
            with open(filename, 'r') as f:
                return f.read()
    except Exception as e:
        print(f"Error loading resume: {e}")
        return ""


if __name__ == "__main__":
    resume_text = load_resume()
    analyzer = ResumeAnalyzer(resume_text)
    
    print("Resume Analysis:")
    print(f"  Skills: {analyzer.skills}")
    print(f"  Experience: {analyzer.experience_years} years")
    print(f"  Companies: {analyzer.companies}")
    print(f"  Qualifications: {analyzer.qualifications}")
    print(f"\nProfile Summary:")
    print(f"  {analyzer.summary}")
