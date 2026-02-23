"""RAG retrieval and answer generation with citations."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import structlog

from ada.brains.unstructured.embeddings import embed_text
from ada.llm.client import completion

if TYPE_CHECKING:
    from ada.brains.unstructured.qdrant import QdrantStore

logger = structlog.get_logger()

RAG_SYSTEM_PROMPT = """\
You are a helpful assistant that answers questions based on provided context documents.

Rules:
1. Only answer based on the provided context. If the context doesn't contain \
enough information, say so.
2. Cite your sources using [Source N] notation, where N corresponds to the \
document number in the context.
3. Be concise and direct.
4. If multiple sources agree, mention the most relevant one.
"""


async def retrieve_and_answer(
    question: str,
    store: QdrantStore,
    tenant_id: str,
    roles: list[str] | None = None,
    source: str | None = None,
    model: str = "gpt-4o-mini",
    top_k: int = 5,
) -> dict[str, Any]:
    """Retrieve relevant documents and generate an answer with citations.

    Returns:
        Dict with 'answer', 'sources', and 'citations' keys.
    """
    # Embed the question
    query_vector = await embed_text(question)

    # Retrieve relevant documents
    results = store.search(
        query_vector=query_vector,
        tenant_id=tenant_id,
        roles=roles,
        source=source,
        limit=top_k,
    )

    if not results:
        return {
            "answer": "I couldn't find any relevant documents to answer your question.",
            "sources": [],
            "citations": [],
        }

    # Build context from retrieved documents
    context_parts: list[str] = []
    sources: list[dict[str, Any]] = []
    for i, result in enumerate(results, 1):
        payload = result.get("payload", {})
        title = payload.get("title", "Untitled")
        text = payload.get("text", "")
        src = payload.get("source", "unknown")

        context_parts.append(f"[Source {i}] ({src}: {title})\n{text}")
        sources.append({
            "index": i,
            "id": result["id"],
            "title": title,
            "source": src,
            "score": result["score"],
        })

    context = "\n\n---\n\n".join(context_parts)

    messages = [
        {"role": "system", "content": RAG_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}",
        },
    ]

    answer = await completion(messages=messages, model=model, temperature=0.1)

    # Extract citation references from the answer
    citation_refs = re.findall(r"\[Source (\d+)\]", answer)
    citations = [
        s for s in sources if str(s["index"]) in citation_refs
    ]

    logger.info(
        "rag_answer_generated",
        question=question,
        num_sources=len(sources),
        num_citations=len(citations),
    )

    return {
        "answer": answer,
        "sources": sources,
        "citations": citations,
    }
