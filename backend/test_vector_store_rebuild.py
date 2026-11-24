import threading
import unittest
from unittest.mock import patch

from app.services.vector_store import ensure_document_store


class FakeStore:
    def __init__(self, count=0):
        self._count = count

    def count(self):
        return self._count


class VectorStoreRebuildTests(unittest.TestCase):
    def test_missing_collection_rebuilds_from_extracted_text(self):
        fake_store = FakeStore(count=0)
        with (
            patch("app.services.vector_store._get_chroma_store", return_value=fake_store),
            patch("app.services.vector_store.chunk_text", return_value=["chunk one", "chunk two"]) as chunk,
            patch("app.services.vector_store.store_chunks", return_value=2) as store,
        ):
            rebuilt = ensure_document_store("document-1", "Extracted PDF text")

        self.assertTrue(rebuilt)
        chunk.assert_called_once_with("Extracted PDF text")
        store.assert_called_once_with("document-1", ["chunk one", "chunk two"])

    def test_existing_collection_is_not_reindexed(self):
        fake_store = FakeStore(count=3)
        with (
            patch("app.services.vector_store._get_chroma_store", return_value=fake_store),
            patch("app.services.vector_store.chunk_text") as chunk,
            patch("app.services.vector_store.store_chunks") as store,
        ):
            rebuilt = ensure_document_store("document-2", "Extracted PDF text")

        self.assertTrue(rebuilt)
        chunk.assert_not_called()
        store.assert_not_called()

    def test_empty_text_returns_false_without_rebuild(self):
        with patch("app.services.vector_store._get_chroma_store") as get_store:
            rebuilt = ensure_document_store("document-3", "")

        self.assertFalse(rebuilt)
        get_store.assert_not_called()

    def test_embedding_failure_is_handled_gracefully(self):
        fake_store = FakeStore(count=0)
        with (
            patch("app.services.vector_store._get_chroma_store", return_value=fake_store),
            patch("app.services.vector_store.chunk_text", return_value=["chunk"]),
            patch("app.services.vector_store.store_chunks", side_effect=RuntimeError("embedding unavailable")),
        ):
            rebuilt = ensure_document_store("document-4", "Extracted PDF text")

        self.assertFalse(rebuilt)

    def test_concurrent_calls_index_only_once(self):
        fake_store = FakeStore(count=0)
        store_calls = []

        def rebuild_store(document_id, chunks):
            store_calls.append((document_id, chunks))
            fake_store._count = len(chunks)
            return len(chunks)

        with (
            patch("app.services.vector_store._get_chroma_store", return_value=fake_store),
            patch("app.services.vector_store.chunk_text", return_value=["chunk"]),
            patch("app.services.vector_store.store_chunks", side_effect=rebuild_store),
        ):
            barrier = threading.Barrier(3)

            def worker():
                barrier.wait()
                ensure_document_store("document-5", "Extracted PDF text")

            threads = [threading.Thread(target=worker) for _ in range(2)]
            for thread in threads:
                thread.start()
            barrier.wait()
            for thread in threads:
                thread.join()

        self.assertEqual(len(store_calls), 1)


if __name__ == "__main__":
    unittest.main()
