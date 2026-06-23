"""
Advanced Predefined Answers - Smart question-answer mapping
Maps patterns to answers with auto-conversion for different formats
"""

# ===== SALARY / CTC =====
SALARY_ANSWERS = {
    # Current CTC (auto-converts based on question format)
    'current ctc': {
        'annual': 500000,
        'lakhs': 5,
        'monthly': 41667,
        'match_keywords': ['current ctc', 'current salary', 'current compensation', 'current pay', 'current package'],
    },
    
    # Expected CTC (auto-converts)
    'expected ctc': {
        'annual': 800000,
        'lakhs': 8,
        'monthly': 66667,
        'match_keywords': ['expected ctc', 'expected salary', 'salary expectation', 'salary range', 'ctc expectation'],
    },
    
    # Take home salary
    'take home': {
        'monthly': 29167,  # 70% of monthly (after tax)
        'annual': 350000,
        'match_keywords': ['take home', 'net salary', 'in hand', 'home salary'],
    },
}

# ===== EXPERIENCE =====
EXPERIENCE_ANSWERS = {
    'total experience': '2.5',
    'python': '2.5',
    'javascript': '1.5',
    'java': '1',
    'machine learning': '2.5',
    'ml': '2.5',
    'deep learning': '2',
    'data science': '2.5',
    'data analysis': '2.5',
    'sql': '2.5',
    'docker': '1.5',
    'kubernetes': '1',
    'aws': '1.5',
    'cloud': '1.5',
}

# ===== LOCATION / RELOCATION =====
LOCATION_ANSWERS = {
    'current location': 'Bangalore',
    'city': 'Bangalore',
    'location': 'Bangalore',
    'willing to relocate': 'Yes',
    'relocate': 'Yes',
    'relocation': 'Yes',
    'can relocate': 'Yes',
    'open to relocation': 'Yes',
    'willing move': 'Yes',
    'preferred location': 'Bangalore, Remote',
    'preference': 'Remote, Bangalore',
}

# ===== AVAILABILITY / NOTICE PERIOD =====
AVAILABILITY_ANSWERS = {
    'notice period': '0',
    'available': 'Immediate',
    'can start': 'Immediate',
    'availability': 'Immediate',
    'when can you join': 'Immediate',
    'when can you start': 'Immediate',
    'earliest start': 'Immediate',
}

# ===== COMPANY HISTORY =====
COMPANY_ANSWERS = {
    'current company': 'Capgemini',
    'working at': 'Capgemini',
    'current role': 'AI/ML Engineer',
    'current designation': 'AI/ML Engineer',
    'current job title': 'AI/ML Engineer',
    'previous company': 'QuGates Technologies',
    'worked at': 'QuGates Technologies',
    'last company': 'QuGates Technologies',
}

# ===== SKILLS =====
SKILLS_ANSWERS = {
    'programming language': 'Python, JavaScript, SQL',
    'languages': 'Python, JavaScript, SQL',
    'technical skills': 'Python, ML, Data Analysis, Problem Solving',
    'tools and technologies': 'Python, Docker, AWS, PostgreSQL',
    'frameworks': 'Django, Flask, React',
    'databases': 'PostgreSQL, MongoDB, Redis',
    'cloud': 'AWS, GCP',
}

# ===== MOTIVATION & GOALS =====
MOTIVATION_ANSWERS = {
    'why join us': 'Growing tech, challenging work, team culture',
    'why company': 'Growing tech, challenging work, team culture',
    'why role': 'Align with career goals, use my skills',
    'interested': 'Opportunity to grow, challenging problems',
    'career goal': 'Senior ML Engineer, Tech Lead',
    'future plan': 'Lead tech team, mentor others',
}

# ===== YES/NO QUESTIONS =====
YES_NO_ANSWERS = {
    'willing to travel': 'Yes',
    'open to travel': 'Yes',
    'can travel': 'Yes',
    'flexible with hours': 'Yes',
    'open to shift': 'Yes',
    'shift work': 'Yes',
    'ready to work': 'Yes',
    'can you work': 'Yes',
    'work on weekends': 'Sometimes',
    'work on holidays': 'Sometimes',
}

# ===== CONSOLIDATED MATCHER =====
def match_question_to_answer(question: str) -> tuple:
    """
    Match question to predefined answer
    Returns: (answer, category, confidence)
    """
    q_lower = question.lower()
    
    # Check salary answers
    for key, data in SALARY_ANSWERS.items():
        for keyword in data.get('match_keywords', [key]):
            if keyword in q_lower:
                # Return annual format by default
                return (str(data.get('annual', data.get('lakhs'))), 'salary', 0.95)
    
    # Check experience
    for skill, years in EXPERIENCE_ANSWERS.items():
        if skill in q_lower or f'{skill} experience' in q_lower:
            return (years, 'experience', 0.9)
    
    # Check location
    for keyword, answer in LOCATION_ANSWERS.items():
        if keyword in q_lower:
            return (answer, 'location', 0.9)
    
    # Check availability
    for keyword, answer in AVAILABILITY_ANSWERS.items():
        if keyword in q_lower:
            return (answer, 'availability', 0.9)
    
    # Check company
    for keyword, answer in COMPANY_ANSWERS.items():
        if keyword in q_lower:
            return (answer, 'company', 0.9)
    
    # Check skills
    for keyword, answer in SKILLS_ANSWERS.items():
        if keyword in q_lower:
            return (answer, 'skills', 0.85)
    
    # Check motivation
    for keyword, answer in MOTIVATION_ANSWERS.items():
        if keyword in q_lower:
            return (answer, 'motivation', 0.85)
    
    # Check yes/no
    for keyword, answer in YES_NO_ANSWERS.items():
        if keyword in q_lower:
            return (answer, 'yes_no', 0.9)
    
    return (None, 'no_match', 0.0)


# Test function
if __name__ == "__main__":
    test_questions = [
        "What is your current CTC?",
        "Expected salary?",
        "Python experience?",
        "Current location?",
        "Notice period?",
        "Can you start immediately?",
        "Why do you want to join?",
        "Are you willing to relocate?",
    ]
    
    print("=" * 70)
    print("ADVANCED PREDEFINED ANSWERS - MATCHER TEST")
    print("=" * 70)
    
    for q in test_questions:
        answer, category, confidence = match_question_to_answer(q)
        print(f"\nQ: {q}")
        print(f"A: {answer} | Category: {category} | Confidence: {confidence:.0%}")
