"""Tests for the unstructured data brain (RAG pipeline)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ada.brains.unstructured.chunker import Chunk, chunk_text
from ada.brains.unstructured.rag import retrieve_and_answer

# --- Chunker tests ---


class TestChunker:
    def test_chunk_empty_text(self) -> None:
        assert chunk_text("") == []
        assert chunk_text("   ") == []

    def test_chunk_short_text(self) -> None:
        chunks = chunk_text("Hello world", chunk_size=100)
        assert len(chunks) == 1
        assert chunks[0].text == "Hello world"
        assert chunks[0].index == 0

    def test_chunk_with_metadata(self) -> None:
        chunks = chunk_text("Hello", metadata={"source": "test"})
        assert chunks[0].metadata == {"source": "test"}

    def test_chunk_long_text(self) -> None:
        text = "word " * 500  # ~2500 chars
        chunks = chunk_text(text, chunk_size=500, chunk_overlap=100)
        assert len(chunks) > 1
        # Verify indices are sequential
        for i, chunk in enumerate(chunks):
            assert chunk.index == i

    def test_chunk_overlap(self) -> None:
        # Create text with clear boundaries
        text = "A" * 100 + ". " + "B" * 100 + ". " + "C" * 100
        chunks = chunk_text(text, chunk_size=110, chunk_overlap=20)
        assert len(chunks) >= 2

    def test_chunk_model(self) -> None:
        chunk = Chunk(text="test", metadata={"key": "val"}, index=3)
        assert chunk.text == "test"
        assert chunk.metadata == {"key": "val"}
        assert chunk.index == 3


# --- RAG tests ---


class TestRAG:
    @pytest.fixture
    def mock_embed(self):
        with patch(
            "ada.brains.unstructured.rag.embed_text",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = [0.1] * 1536
            yield mock

    @pytest.fixture
    def mock_completion(self):
        with patch(
            "ada.brains.unstructured.rag.completion",
            new_callable=AsyncMock,
        ) as mock:
            yield mock

    @pytest.fixture
    def mock_store(self):
        store = MagicMock()
        return store

    async def test_no_results(
        self, mock_embed: AsyncMock, mock_store: MagicMock
    ) -> None:
        mock_store.search.return_value = []
        result = await retrieve_and_answer(
            question="What is X?",
            store=mock_store,
            tenant_id="t1",
        )
        assert "couldn't find" in result["answer"].lower()
        assert result["sources"] == []
        assert result["citations"] == []

    async def test_with_results_and_citations(
        self,
        mock_embed: AsyncMock,
        mock_completion: AsyncMock,
        mock_store: MagicMock,
    ) -> None:
        mock_store.search.return_value = [
            {
                "id": "doc-1",
                "score": 0.95,
                "payload": {
                    "title": "Refund Policy",
                    "text": "Refunds are processed within 5 days.",
                    "source": "confluence",
                },
            },
            {
                "id": "doc-2",
                "score": 0.8,
                "payload": {
                    "title": "FAQ",
                    "text": "Contact support for refunds.",
                    "source": "intercom",
                },
            },
        ]
        mock_completion.return_value = (
            "Refunds are processed within 5 days [Source 1]. "
            "You can also contact support [Source 2]."
        )

        result = await retrieve_and_answer(
            question="What is the refund policy?",
            store=mock_store,
            tenant_id="t1",
            roles=["support"],
        )

        assert "5 days" in result["answer"]
        assert len(result["sources"]) == 2
        assert len(result["citations"]) == 2
        assert result["citations"][0]["title"] == "Refund Policy"

    async def test_rbac_filtering_passed_to_store(
        self, mock_embed: AsyncMock, mock_store: MagicMock
    ) -> None:
        mock_store.search.return_value = []
        await retrieve_and_answer(
            question="Q?",
            store=mock_store,
            tenant_id="tenant-abc",
            roles=["admin", "finance"],
            source="confluence",
        )
        mock_store.search.assert_called_once_with(
            query_vector=mock_embed.return_value,
            tenant_id="tenant-abc",
            roles=["admin", "finance"],
            source="confluence",
            limit=5,
        )
