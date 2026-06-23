import pytest
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ai.engine import AIAnswerEngine

def test_clean_answer():
    engine = AIAnswerEngine()
    
    # Remove fluff
    assert engine._clean_answer("I think the answer is Python.") == "Python"
    assert engine._clean_answer("Based on my experience, 3 years.") == "3 years"
    assert engine._clean_answer("Yes, I am.") == "Yes, I am"
    
    # Handle multiple lines/whitespaces
    assert engine._clean_answer("   Here:   Data Analysis   ") == "Data Analysis"

def test_answer_question_mocked_gemini(mocker):
    # Mock the _generate_answer_gemini method so we don't use real API credits
    mocker.patch('ai.engine.AIAnswerEngine._generate_answer_gemini', return_value="Mocked Answer")
    mocker.patch('ai.engine.AIAnswerEngine._try_decision_tree', return_value=None)
    mocker.patch('ai.engine.AIAnswerEngine._try_smart_answer', return_value=None)
    mocker.patch('ai.engine.AIAnswerEngine._load_cache', return_value=None)
    mocker.patch('ai.engine.AIAnswerEngine._save_cache', return_value=None)
    mocker.patch.dict('ai.engine._qa_cache', {}, clear=True)
    
    # We also mock out checking the config PREDEFINED_ANSWERS so it hits the generator
    mocker.patch('ai.engine.PREDEFINED_ANSWERS', {})

    engine = AIAnswerEngine()
    
    ans, metadata = engine.answer_question("What is an unusual question?", "", "")
    assert ans == "Mocked Answer"
    assert metadata['source'] == 'generated'

def test_answer_question_cached(mocker):
    # Mock the cache to already have the answer
    mocker.patch.dict('ai.engine._qa_cache', {"What is an unusual question?": "Cached Mocked Answer"}, clear=True)
    mocker.patch('ai.engine.AIAnswerEngine._load_cache', return_value=None)
    mocker.patch('ai.engine.AIAnswerEngine._try_decision_tree', return_value=None)
    mocker.patch('ai.engine.AIAnswerEngine._try_smart_answer', return_value=None)
    mocker.patch('ai.engine.PREDEFINED_ANSWERS', {})

    engine = AIAnswerEngine()
    
    ans, metadata = engine.answer_question("What is an unusual question?", "", "")
    assert ans == "Cached Mocked Answer"
    assert metadata['source'] == 'cache'

from core.common import SkipJobException

def test_gemini_model_fallback(mocker):
    # Test that _generate_answer_gemini falls back to alternative models if the primary model throws an exception
    mocker.patch('ai.engine.AIAnswerEngine._load_cache', return_value=None)
    engine = AIAnswerEngine()

    # Mock the internal gemini client
    class MockResponse:
        text = "Flash Answer"
    
    mock_generate = mocker.Mock()
    # First call raises exception, second call succeeds
    mock_generate.side_effect = [Exception("API Key Invalid"), MockResponse()]
    
    mocker.patch('ai.engine._client.models.generate_content', mock_generate)
    
    result = engine._generate_answer_gemini("Test Prompt", "Test Question")
    
    assert result == "Flash Answer"
    # Should have been called twice (once for pro, once for flash fallback)
    assert mock_generate.call_count == 2

def test_gemini_unknown_answer_skips_job(mocker):
    # Test that returning UNKNOWN_ANSWER raises SkipJobException
    mocker.patch('ai.engine.AIAnswerEngine._generate_answer_gemini', return_value="UNKNOWN_ANSWER")
    mocker.patch('ai.engine.AIAnswerEngine._try_decision_tree', return_value=None)
    mocker.patch('ai.engine.AIAnswerEngine._try_smart_answer', return_value=None)
    mocker.patch('ai.engine.AIAnswerEngine._load_cache', return_value=None)
    mocker.patch.dict('ai.engine._qa_cache', {}, clear=True)
    mocker.patch('ai.engine.PREDEFINED_ANSWERS', {})

    engine = AIAnswerEngine()
    
    with pytest.raises(SkipJobException):
        engine.answer_question("Question?", "", "")
