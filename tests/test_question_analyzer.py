import pytest
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ai.question_analyzer import QuestionAnalyzer, QuestionType

def test_question_classification():
    tests = [
        ("Are you willing to relocate to Bangalore?", QuestionType.RELOCATION),
        ("How many years of experience do you have in Python?", QuestionType.EXPERIENCE),
        ("What are your salary expectations?", QuestionType.SALARY),
        ("Tell me about a time you solved a difficult problem.", QuestionType.PROBLEM_SOLVING),
        ("What is your current notice period?", QuestionType.AVAILABILITY),
        ("Are you fluent in English?", QuestionType.LANGUAGE),
        ("What is your highest degree of education?", QuestionType.EDUCATION),
        ("What is your primary programming language?", QuestionType.TECHNICAL),
        ("Why do you want to join our company?", QuestionType.MOTIVATION),
        ("Tell me about a time you had to lead a team.", QuestionType.LEADERSHIP),
    ]

    for q, expected_type in tests:
        analyzer = QuestionAnalyzer(q)
        assert analyzer.question_type == expected_type, f"Failed on: {q}"

def test_should_skip():
    analyzer1 = QuestionAnalyzer("This question is optional, you can skip it.")
    assert analyzer1.should_skip() is True

    analyzer2 = QuestionAnalyzer("What is your experience in machine learning?")
    assert analyzer2.should_skip() is False

def test_confidence():
    analyzer = QuestionAnalyzer("How many years of experience?")
    # 'experience' keyword matches pattern
    assert analyzer.confidence > 0.0
