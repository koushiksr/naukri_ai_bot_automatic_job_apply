import pytest
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ai.smart_answer_matcher import SmartAnswerMatcher

def test_salary_conversion():
    matcher = SmartAnswerMatcher(current_ctc_annual=500000, expected_ctc_annual=800000)
    
    assert matcher.convert_salary_format('5', 'annual') == '500000'
    assert matcher.convert_salary_format('500000', 'lakhs') == '5.0'
    assert matcher.convert_salary_format('8 LPA', 'annual') == '800000'

def test_find_best_answer_predefined():
    matcher = SmartAnswerMatcher(current_ctc_annual=500000, expected_ctc_annual=800000)
    
    # Keyword match
    ans, source = matcher.find_best_answer("Are you willing to relocate to Bangalore?")
    assert ans == "Yes"
    assert source == "predefined_direct"

    # Format match
    ans, source = matcher.find_best_answer("What is your current CTC?")
    assert ans == "500000"
    assert source == "predefined_formatted"

def test_find_best_answer_llm_fallback():
    matcher = SmartAnswerMatcher()
    
    # Unmatched question
    ans, source = matcher.find_best_answer("Why do you want to switch jobs?")
    assert ans is None
    assert source == "llm_needed"

def test_match_answer_to_options():
    matcher = SmartAnswerMatcher()
    
    options = ["Yes", "No", "Maybe"]
    assert matcher.match_answer_to_options("yes", options) == "Yes"
    
    # Partial match
    options = ["Immediate", "Within 15 days", "1 Month"]
    assert matcher.match_answer_to_options("immediately", options) == "Immediate"
