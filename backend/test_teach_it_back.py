import unittest
from unittest.mock import patch

from app.services.teach_it_back import (
    InsufficientSourceError,
    TeachItBackAIError,
    _evaluate_rubric,
    _generate_rubric,
)


class TeachItBackRubricTests(unittest.TestCase):
    def test_weighted_score_uses_concept_status_and_importance(self):
        rubric = [
            {
                "concept": "Sorted input",
                "description": "Input is sorted.",
                "importance": "high",
                "source_evidence": "The input must be sorted.",
                "weight": 3,
            },
            {
                "concept": "Middle element",
                "description": "Inspect the middle.",
                "importance": "medium",
                "source_evidence": "Find the middle element.",
                "weight": 2,
            },
            {
                "concept": "Logarithmic time",
                "description": "The search is logarithmic.",
                "importance": "low",
                "source_evidence": "The running time is logarithmic.",
                "weight": 1,
            },
        ]
        response = {
            "concept_evaluations": [
                {
                    "concept": "Sorted input",
                    "status": "fully_covered",
                    "student_evidence": "The list has to be sorted.",
                    "feedback": "Correct.",
                },
                {
                    "concept": "Middle element",
                    "status": "partially_covered",
                    "student_evidence": "Check the middle.",
                    "feedback": "Add how the interval changes.",
                },
                {
                    "concept": "Logarithmic time",
                    "status": "missed",
                    "student_evidence": "",
                    "feedback": "Not mentioned.",
                },
            ],
            "model_answer": "A concise answer.",
            "message": "Keep going.",
        }

        with patch("app.services.teach_it_back._invoke_json", return_value=response):
            result = _evaluate_rubric(
                "Binary search", rubric, "The list has to be sorted. Check the middle."
            )

        self.assertEqual(result["score"], 7)
        self.assertEqual(
            [item["status"] for item in result["concept_evaluations"]],
            ["fully_covered", "partially_covered", "missed"],
        )
        self.assertEqual(result["missing"], ["Logarithmic time: The search is logarithmic."])

    def test_does_not_award_coverage_without_student_evidence(self):
        rubric = [{
            "concept": "Sorted input",
            "description": "Input is sorted.",
            "importance": "high",
            "source_evidence": "The input must be sorted.",
            "weight": 3,
        }]
        response = {
            "concept_evaluations": [{
                "concept": "Sorted input",
                "status": "fully_covered",
                "student_evidence": "The middle element is checked.",
                "feedback": "Correct.",
            }],
            "model_answer": "A concise answer.",
            "message": "Keep going.",
        }

        with patch("app.services.teach_it_back._invoke_json", return_value=response):
            result = _evaluate_rubric("Binary search", rubric, "I split the list.")

        self.assertEqual(result["score"], 0)
        self.assertEqual(result["concept_evaluations"][0]["status"], "missed")
        self.assertEqual(result["concept_evaluations"][0]["student_evidence"], "")

    def test_rejects_rubric_without_verifiable_source_evidence(self):
        response = {
            "source_sufficient": True,
            "concepts": [{
                "concept": "Hash tables",
                "description": "Use key-value storage.",
                "importance": "high",
                "source_evidence": "Hash tables use keys.",
            }],
        }

        with patch("app.services.teach_it_back._invoke_json", return_value=response):
            with self.assertRaises(TeachItBackAIError):
                _generate_rubric("Binary search", "Binary search divides a sorted list.")

    def test_stops_when_source_is_insufficient(self):
        response = {
            "source_sufficient": False,
            "insufficiency_reason": "The excerpt does not explain the topic.",
            "concepts": [],
        }

        with patch("app.services.teach_it_back._invoke_json", return_value=response):
            with self.assertRaisesRegex(InsufficientSourceError, "does not explain"):
                _generate_rubric("Binary search", "A brief unrelated excerpt.")


if __name__ == "__main__":
    unittest.main()
