import unittest

from app.services.upgrade_me import _current_progress_status, make_concept_id


class UpgradeMeProgressTests(unittest.TestCase):
    def test_empty_source_text_is_rejected(self):
        from app.services.upgrade_me import UpgradeMeSourceError
        from unittest.mock import patch
        with patch("app.services.upgrade_me.retrieve_relevant_chunks_with_ids", return_value=[]):
            from app.services.upgrade_me import _source_context
            with self.assertRaises(UpgradeMeSourceError):
                _source_context({"id": "document-1"}, "Deadlock")

    def test_concept_identifier_is_stable_for_equivalent_names(self):
        first = make_concept_id("document-1", "Binary Search", "Sorted Input")
        repeated = make_concept_id("document-1", " binary   search ", "sorted input")
        other_document = make_concept_id("document-2", "Binary Search", "Sorted Input")

        self.assertEqual(first, repeated)
        self.assertNotEqual(first, other_document)

    def test_full_latest_evaluation_marks_concept_improved(self):
        self.assertEqual(
            _current_progress_status("fully_covered", "2026-01-02T00:00:00Z", None),
            "improved",
        )

    def test_newer_full_oral_evaluation_improves_a_weak_concept(self):
        progress = {
            "last_evaluation_status": "fully_covered",
            "last_evaluated_at": "2026-01-03T00:00:00Z",
        }

        self.assertEqual(
            _current_progress_status(
                "partially_covered", "2026-01-02T00:00:00Z", progress
            ),
            "improved",
        )

    def test_newer_weak_teach_it_back_evaluation_reopens_concept(self):
        progress = {
            "improvement_status": "improved",
            "last_evaluation_status": "fully_covered",
            "last_evaluated_at": "2026-01-02T00:00:00Z",
            "last_practiced_at": "2026-01-02T00:00:00Z",
        }

        self.assertEqual(
            _current_progress_status(
                "incorrect", "2026-01-03T00:00:00Z", progress
            ),
            "needs_improvement",
        )


if __name__ == "__main__":
    unittest.main()
