from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ada.llm.client import completion, completion_with_metadata


def _make_response(content: str, prompt_tokens: int = 10, completion_tokens: int = 5):
    usage = MagicMock()
    usage.prompt_tokens = prompt_tokens
    usage.completion_tokens = completion_tokens
    usage.total_tokens = prompt_tokens + completion_tokens

    message = MagicMock()
    message.content = content

    choice = MagicMock()
    choice.message = message

    response = MagicMock()
    response.choices = [choice]
    response.usage = usage
    response.model = "gpt-4o-mini"
    return response


@pytest.fixture
def mock_litellm():
    with patch("ada.llm.client.litellm") as mock:
        mock.acompletion = AsyncMock()
        yield mock


async def test_completion_returns_text(mock_litellm: MagicMock):
    mock_litellm.acompletion.return_value = _make_response("Hello world")
    result = await completion(messages=[{"role": "user", "content": "hi"}])
    assert result == "Hello world"
    mock_litellm.acompletion.assert_called_once()


async def test_completion_with_metadata(mock_litellm: MagicMock):
    mock_litellm.acompletion.return_value = _make_response(
        "Answer", prompt_tokens=20, completion_tokens=10
    )
    result = await completion_with_metadata(messages=[{"role": "user", "content": "question"}])
    assert result["content"] == "Answer"
    assert result["model"] == "gpt-4o-mini"
    assert result["usage"]["prompt_tokens"] == 20
    assert result["usage"]["completion_tokens"] == 10
    assert result["usage"]["total_tokens"] == 30
