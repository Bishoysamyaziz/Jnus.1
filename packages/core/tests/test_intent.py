"""Tests for IntentClassifier"""
from __future__ import annotations

import pytest

from packages.core.intent.classifier import IntentClassifier
from packages.core.models import IntentType


@pytest.fixture
def classifier():
    return IntentClassifier()


@pytest.mark.asyncio
async def test_classify_code_intent(classifier):
    """CODE intent should be detected for programming requests"""
    tests = [
        ("اكتب API للـ user authentication", IntentType.CODE),
        ("build a REST API in Python", IntentType.CODE),
        ("fix this bug in the code", IntentType.CODE),
        ("implement a sorting algorithm", IntentType.CODE),
        ("write a function to calculate fibonacci", IntentType.CODE),
    ]
    for text, expected in tests:
        intent = await classifier.classify(text)
        assert intent.type == expected, f"Expected {expected} for '{text}', got {intent.type}"
        assert 0 <= intent.confidence <= 1.0


@pytest.mark.asyncio
async def test_classify_research_intent(classifier):
    """RESEARCH intent should be detected for research requests"""
    tests = [
        ("ابحث عن معلومات عن الذكاء الاصطناعي", IntentType.RESEARCH),
        ("research the latest AI trends", IntentType.RESEARCH),
        ("tell me about machine learning", IntentType.RESEARCH),
        ("what is quantum computing", IntentType.RESEARCH),
    ]
    for text, expected in tests:
        intent = await classifier.classify(text)
        assert intent.type == expected, f"Expected {expected} for '{text}', got {intent.type}"


@pytest.mark.asyncio
async def test_classify_data_intent(classifier):
    """DATA intent should be detected for data analysis requests"""
    tests = [
        ("حلل هذا الـ CSV", IntentType.DATA),
        ("analyze this dataset", IntentType.DATA),
        ("create a chart from this data", IntentType.DATA),
        ("run statistics on this data", IntentType.DATA),
    ]
    for text, expected in tests:
        intent = await classifier.classify(text)
        assert intent.type == expected, f"Expected {expected} for '{text}', got {intent.type}"


@pytest.mark.asyncio
async def test_classify_planning_intent(classifier):
    """PLANNING intent should be detected for planning requests"""
    tests = [
        ("خطط لمشروع تعلم الآلة", IntentType.PLANNING),
        ("create a project roadmap", IntentType.PLANNING),
        ("plan a 3-month learning schedule", IntentType.PLANNING),
        ("what's the strategy for this goal", IntentType.PLANNING),
    ]
    for text, expected in tests:
        intent = await classifier.classify(text)
        assert intent.type == expected, f"Expected {expected} for '{text}', got {intent.type}"


@pytest.mark.asyncio
async def test_classify_conversation_intent(classifier):
    """CONVERSATION intent should be detected for casual chat"""
    tests = [
        ("مرحبا كيف حالك", IntentType.CONVERSATION),
        ("hello how are you", IntentType.CONVERSATION),
        ("what's up", IntentType.CONVERSATION),
        ("hey there", IntentType.CONVERSATION),
    ]
    for text, expected in tests:
        intent = await classifier.classify(text)
        assert intent.type == expected, f"Expected {expected} for '{text}', got {intent.type}"


@pytest.mark.asyncio
async def test_classify_creative_intent(classifier):
    """CREATIVE intent should be detected for creative tasks"""
    tests = [
        ("اكتب قصة قصيرة", IntentType.CREATIVE),
        ("write a poem about nature", IntentType.CREATIVE),
        ("design a logo for my startup", IntentType.CREATIVE),
        ("create content for social media", IntentType.CREATIVE),
    ]
    for text, expected in tests:
        intent = await classifier.classify(text)
        assert intent.type == expected, f"Expected {expected} for '{text}', got {intent.type}"


@pytest.mark.asyncio
async def test_classify_automation_intent(classifier):
    """AUTOMATION intent should be detected for automation tasks"""
    tests = [
        ("اتمتة عملية إرسال الإيميلات", IntentType.AUTOMATION),
        ("automate the backup process", IntentType.AUTOMATION),
        ("set up a CI/CD pipeline", IntentType.AUTOMATION),
        ("create a workflow for data processing", IntentType.AUTOMATION),
    ]
    for text, expected in tests:
        intent = await classifier.classify(text)
        assert intent.type == expected, f"Expected {expected} for '{text}', got {intent.type}"


@pytest.mark.asyncio
async def test_classify_with_context(classifier):
    """Classification should work with context"""
    context = {"previous_intent": "CODE", "user_preferences": {"language": "python"}}
    intent = await classifier.classify("write a function", context)
    assert intent.type == IntentType.CODE
    assert intent.context == context


@pytest.mark.asyncio
async def test_classify_cache(classifier):
    """Cache should return same result for identical input"""
    text = "write a Python API"
    intent1 = await classifier.classify(text)
    intent2 = await classifier.classify(text)
    assert intent1.type == intent2.type
    assert intent1.confidence == intent2.confidence


@pytest.mark.asyncio
async def test_classify_batch(classifier):
    """Batch classification should work"""
    inputs = ["write code", "research topic", "analyze data"]
    results = await classifier.classify_batch(inputs)
    assert len(results) == 3
    assert all(isinstance(r.type, IntentType) for r in results)


def test_clear_cache(classifier):
    """Clearing cache should work"""
    classifier._cache["test"] = "cached"
    classifier.clear_cache()
    assert len(classifier._cache) == 0


@pytest.mark.asyncio
async def test_fallback_classify(classifier):
    """Fallback classification should work when LLM is unavailable"""
    intent = classifier._fallback_classify("hello world", {})
    assert intent.type == IntentType.CONVERSATION
    assert intent.confidence > 0


@pytest.mark.asyncio
async def test_classify_unknown_input(classifier):
    """Unknown input should default to CODE with lower confidence"""
    intent = await classifier.classify("xyz123 random text")
    assert intent.type == IntentType.CODE
