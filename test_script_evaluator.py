"""
Unit tests for core/script_evaluator.py
Kiểm thử các hàm tính điểm, phân loại, fingerprint, và mock API TypeSafe.
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock

from core.script_evaluator import (
    calculate_viral_score,
    classify_score,
    fingerprint_state,
    build_recommendations,
    sanitize_and_validate_state,
    evaluate_script,
    EvaluatorValidationError,
    EvaluatorConfigError,
    EvaluatorTimeoutError,
    EvaluatorUpstreamError,
    DIMENSIONS_SPEC,
    RUBRIC_VERSION
)


class ScriptEvaluatorTests(unittest.TestCase):

    def test_weights_distribution(self):
        total_weight = sum(dim["weight"] for dim in DIMENSIONS_SPEC.values())
        self.assertAlmostEqual(total_weight, 1.0, places=4)
        self.assertEqual(DIMENSIONS_SPEC["hook_strength"]["weight"], 0.30)
        self.assertEqual(DIMENSIONS_SPEC["curiosity_emotion"]["weight"], 0.25)
        self.assertEqual(DIMENSIONS_SPEC["retention_payoff"]["weight"], 0.25)
        self.assertEqual(DIMENSIONS_SPEC["share_comment"]["weight"], 0.20)

    def test_calculate_viral_score_boundaries(self):
        # All 0
        score_0 = calculate_viral_score({
            "hook_strength": 0.0,
            "curiosity_emotion": 0.0,
            "retention_payoff": 0.0,
            "share_comment": 0.0
        })
        self.assertEqual(score_0, 0)

        # All 4
        score_100 = calculate_viral_score({
            "hook_strength": 4.0,
            "curiosity_emotion": 4.0,
            "retention_payoff": 4.0,
            "share_comment": 4.0
        })
        self.assertEqual(score_100, 100)

        # Mixed scores
        # hook: 4 (0.30 * 1 = 0.30)
        # curiosity: 2 (0.25 * 0.5 = 0.125)
        # retention: 2 (0.25 * 0.5 = 0.125)
        # share: 3 (0.20 * 0.75 = 0.15)
        # total = 0.30 + 0.125 + 0.125 + 0.15 = 0.70 -> 70
        score_mixed = calculate_viral_score({
            "hook_strength": 4.0,
            "curiosity_emotion": 2.0,
            "retention_payoff": 2.0,
            "share_comment": 3.0
        })
        self.assertEqual(score_mixed, 70)

    def test_classify_score(self):
        self.assertEqual(classify_score(100), "recommended")
        self.assertEqual(classify_score(75), "recommended")
        self.assertEqual(classify_score(74), "revise")
        self.assertEqual(classify_score(60), "revise")
        self.assertEqual(classify_score(59), "major_revision")
        self.assertEqual(classify_score(0), "major_revision")

    def test_fingerprint_deterministic(self):
        state1 = {
            "platform": "tiktok",
            "title_sub": "Vụ án xì dầu",
            "dialogue": [{"speaker": "A", "text": "Chào bạn", "emotion": "normal"}]
        }
        state2 = {
            "dialogue": [{"text": "Chào bạn", "speaker": "A", "emotion": "normal"}],
            "title_sub": "Vụ án xì dầu",
            "platform": "tiktok"
        }
        fp1 = fingerprint_state(state1)
        fp2 = fingerprint_state(state2)
        self.assertEqual(fp1, fp2)
        self.assertTrue(fp1.startswith("sha256:"))

    def test_build_recommendations_and_limits(self):
        dimensions = {
            "hook_strength": {"score": 1.0, "confidence": 0.8}, # gap = 0.30 * 3 = 0.90
            "curiosity_emotion": {"score": 2.0, "confidence": 0.7}, # gap = 0.25 * 2 = 0.50
            "retention_payoff": {"score": 1.5, "confidence": 0.3, "uncertain": True}, # gap = 0.25 * 2.5 = 0.625 (uncertain)
            "share_comment": {"score": 4.0, "confidence": 0.9} # gap = 0
        }
        recs = build_recommendations(dimensions, {"content_profile": "irasutoya_short"})
        self.assertLessEqual(len(recs), 3)
        codes = [r["code"] for r in recs]
        self.assertIn("STRENGTHEN_HOOK", codes)
        self.assertNotIn("PROVOKE_DEBATE", codes)

        # Test asian_myth_3d special hook message
        recs_myth = build_recommendations(dimensions, {"content_profile": "asian_myth_3d"})
        hook_rec = next(r for r in recs_myth if r["dimension"] == "hook_strength")
        self.assertEqual(hook_rec["code"], "STRENGTHEN_HOOK_LONG_FORM")
        self.assertIn("mini-hook", hook_rec["message"])

    def test_sanitize_and_validate_state_limits(self):
        # Empty title_sub
        with self.assertRaises(EvaluatorValidationError):
            sanitize_and_validate_state({"title_sub": "", "dialogue": [{"speaker": "a", "text": "b"}]})

        # Empty dialogue
        with self.assertRaises(EvaluatorValidationError):
            sanitize_and_validate_state({"title_sub": "Test", "dialogue": []})

        # Over 100 lines
        huge_dialogue = [{"speaker": "a", "text": f"line {i}"} for i in range(101)]
        with self.assertRaises(EvaluatorValidationError):
            sanitize_and_validate_state({"title_sub": "Test", "dialogue": huge_dialogue})

        # Over 12,000 characters
        giant_text_dialogue = [{"speaker": "a", "text": "x" * 12500}]
        with self.assertRaises(EvaluatorValidationError):
            sanitize_and_validate_state({"title_sub": "Test", "dialogue": giant_text_dialogue})

    def test_evaluate_script_missing_key(self):
        script_data = {
            "title_sub": "Test",
            "dialogue": [{"speaker": "a", "text": "hello"}]
        }
        with self.assertRaises(EvaluatorConfigError):
            asyncio.run(evaluate_script(script_data, api_key=""))

    def test_mocked_evaluate_script_success(self):
        class FakeAnswer:
            def __init__(self, score, confidence, probabilities):
                self.score = score
                self.confidence = confidence
                self.probabilities = probabilities

        class FakeResponse:
            model = "jev-latest"
            answers = {
                "hook_strength": FakeAnswer(3.0, 0.85, {0: 0.01, 1: 0.05, 2: 0.20, 3: 0.60, 4: 0.14}),
                "curiosity_emotion": FakeAnswer(3.0, 0.75, {0: 0.02, 1: 0.08, 2: 0.20, 3: 0.55, 4: 0.15}),
                "retention_payoff": FakeAnswer(2.0, 0.80, {0: 0.05, 1: 0.15, 2: 0.60, 3: 0.15, 4: 0.05}),
                "share_comment": FakeAnswer(3.0, 0.70, {0: 0.02, 1: 0.08, 2: 0.25, 3: 0.50, 4: 0.15}),
            }

        fake_client = MagicMock()
        fake_client.system_one = AsyncMock(return_value=FakeResponse())

        script_data = {
            "title_sub": "Test Script",
            "dialogue": [
                {"speaker": "judge", "text": "Tòa tuyên án", "emotion": "normal"},
                {"speaker": "prisoner", "text": "Oan uổng quá", "emotion": "regret"}
            ]
        }

        result = asyncio.run(evaluate_script(script_data, client=fake_client))

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["model"], "jev-latest")
        self.assertEqual(result["rubric_version"], RUBRIC_VERSION)
        self.assertGreater(result["viral_score"], 0)
        self.assertIn("dimensions", result)
        self.assertIn("hook_strength", result["dimensions"])
        self.assertEqual(len(result["dimensions"]["hook_strength"]["probabilities"]), 5)
        self.assertEqual(result["weakest_dimension"], "retention_payoff")
        self.assertIn("input_fingerprint", result)


if __name__ == "__main__":
    unittest.main()
