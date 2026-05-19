import unittest

from fastapi import HTTPException

from app.domain.compatibility_engine import is_valid, validate_build
from app.domain.recommender import recommend_builds
from app.domain.sample_data import PARTS
from app.domain.schemas import QuoteRequestPayload


class RecommenderTestCase(unittest.TestCase):
    def test_recommendation_returns_primary_and_alternatives(self) -> None:
        payload = QuoteRequestPayload(budget=1_700_000, purpose="gaming", preferred_brands=["AMD", "NVIDIA"])
        bundle = recommend_builds(payload)

        self.assertTrue(bundle["primary"].quote_id.startswith("qt_"))
        self.assertGreaterEqual(len(bundle["alternatives"]), 2)
        self.assertLessEqual(bundle["primary"].total_price, payload.budget)

    def test_low_budget_raises_no_compatible_build(self) -> None:
        payload = QuoteRequestPayload(budget=300_000, purpose="3d", preferred_brands=["NVIDIA"])
        with self.assertRaises(HTTPException) as context:
            recommend_builds(payload)

        self.assertEqual(context.exception.status_code, 422)

    def test_validation_marks_known_good_build_as_valid(self) -> None:
        bundle = recommend_builds(QuoteRequestPayload(budget=1_500_000, purpose="gaming", preferred_brands=[]))
        models = {item.model for item in bundle["primary"].items}
        build = {part["category"]: part for part in PARTS if part["model"] in models}
        checks = validate_build(build)
        self.assertTrue(is_valid(checks))

    def test_each_budget_tier_has_five_options(self) -> None:
        cases = [
            ("office", 900_000),
            ("office", 1_300_000),
            ("gaming", 900_000),
            ("gaming", 1_500_000),
            ("video_edit", 1_500_000),
            ("video_edit", 2_500_000),
            ("3d", 2_500_000),
            ("3d", 5_000_000),
            ("deep_learning", 5_000_000),
            ("deep_learning", 10_000_000),
        ]

        for purpose, budget in cases:
            with self.subTest(purpose=purpose, budget=budget):
                payload = QuoteRequestPayload(budget=budget, purpose=purpose, preferred_brands=[])
                bundle = recommend_builds(payload)
                self.assertGreaterEqual(len(bundle["alternatives"]) + 1, 5)
                self.assertLessEqual(bundle["primary"].total_price, payload.budget)


if __name__ == "__main__":
    unittest.main()
