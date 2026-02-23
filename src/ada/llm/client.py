from typing import Any

import litellm
import structlog

logger = structlog.get_logger()

# Suppress LiteLLM's verbose logging
litellm.suppress_debug_info = True


async def completion(
    messages: list[dict[str, str]],
    model: str = "gpt-4o-mini",
    temperature: float = 0.0,
    max_tokens: int = 2048,
    **kwargs: Any,
) -> str:
    """Send a chat completion request via LiteLLM and return the response text."""
    response = await litellm.acompletion(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs,
    )
    content = response.choices[0].message.content or ""
    logger.debug(
        "llm_completion", model=model, input_tokens=len(str(messages)), output_len=len(content)
    )
    return content


async def completion_with_metadata(
    messages: list[dict[str, str]],
    model: str = "gpt-4o-mini",
    temperature: float = 0.0,
    max_tokens: int = 2048,
    **kwargs: Any,
) -> dict[str, Any]:
    """Send a chat completion and return both the content and usage metadata."""
    response = await litellm.acompletion(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs,
    )
    content = response.choices[0].message.content or ""
    usage = response.usage
    return {
        "content": content,
        "model": response.model,
        "usage": {
            "prompt_tokens": usage.prompt_tokens if usage else 0,
            "completion_tokens": usage.completion_tokens if usage else 0,
            "total_tokens": usage.total_tokens if usage else 0,
        },
    }
