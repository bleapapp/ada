from unittest.mock import AsyncMock, patch

import pytest

from ada.llm.router import Intent, classify_intent


@pytest.fixture
def mock_completion():
    with patch("ada.llm.router.completion", new_callable=AsyncMock) as mock:
        yield mock


async def test_classify_structured_query(mock_completion: AsyncMock):
    mock_completion.return_value = "STRUCTURED"
    result = await classify_intent("How many users signed up last week?")
    assert result == Intent.STRUCTURED


async def test_classify_unstructured_query(mock_completion: AsyncMock):
    mock_completion.return_value = "UNSTRUCTURED"
    result = await classify_intent("What is our refund policy?")
    assert result == Intent.UNSTRUCTURED


async def test_classify_defaults_to_unstructured(mock_completion: AsyncMock):
    mock_completion.return_value = "I'm not sure about this one"
    result = await classify_intent("Tell me something")
    assert result == Intent.UNSTRUCTURED


async def test_classify_handles_whitespace(mock_completion: AsyncMock):
    mock_completion.return_value = "  STRUCTURED  \n"
    result = await classify_intent("Count of active subscriptions")
    assert result == Intent.STRUCTURED
