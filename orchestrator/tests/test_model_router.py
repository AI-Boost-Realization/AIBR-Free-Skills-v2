"""
Tests for model-router.py — ModelRouter class and route_request function.

The file uses a hyphenated name so we load it via importlib.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Dict

import pytest

# ---------------------------------------------------------------------------
# Import the hyphen-named module
# ---------------------------------------------------------------------------
_MODULE_PATH = Path(__file__).parent.parent / "model-router.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("model_router", _MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_mod = _load_module()
ModelRouter = _mod.ModelRouter
route_request = _mod.route_request


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def router() -> ModelRouter:
    """Fresh ModelRouter instance for each test."""
    return ModelRouter()


# ---------------------------------------------------------------------------
# Opus keyword detection
# ---------------------------------------------------------------------------

class TestOpusKeywords:
    """Opus-level complexity keywords and patterns."""

    @pytest.mark.parametrize("task", [
        "design a complex system architecture",
        "plan the strategy for our enterprise solution",
        "optimize the production performance at scale",
        "comprehensive security review and integration design",
        "architect the multi-tenant system",
    ])
    def test_opus_keywords_route_to_opus(self, router: ModelRouter, task: str):
        model, info = router.route(task)
        assert model == "opus", (
            f"Expected opus for {task!r}, got {model}. Scores: {info['scores']}"
        )

    def test_critical_context_forces_opus(self, router: ModelRouter):
        """critical=True in context adds 5 points to opus — should dominate."""
        model, info = router.route("update the readme", context={"critical": True})
        assert model == "opus", f"Expected opus with critical=True, scores: {info['scores']}"

    def test_opus_pattern_design_system(self, router: ModelRouter):
        model, _ = router.route("design system architecture for the new service")
        assert model == "opus"

    def test_opus_pattern_complex_workflow(self, router: ModelRouter):
        model, _ = router.route("complex workflow for the deployment system")
        assert model == "opus"


# ---------------------------------------------------------------------------
# Haiku keyword detection
# ---------------------------------------------------------------------------

class TestHaikuKeywords:
    """Haiku-level simplicity keywords and patterns."""

    @pytest.mark.parametrize("task", [
        "list all files",
        "show the current status",
        "get the config value",
        "what is the version",
        "check the health endpoint",
    ])
    def test_haiku_keywords_route_to_haiku(self, router: ModelRouter, task: str):
        model, info = router.route(task)
        assert model == "haiku", (
            f"Expected haiku for {task!r}, got {model}. Scores: {info['scores']}"
        )

    def test_short_request_boosts_haiku(self, router: ModelRouter):
        """Fewer than 10 words adds 2 points to haiku score."""
        model, info = router.route("list files")
        # The word-count heuristic + keyword should produce haiku
        assert info["scores"]["haiku"] >= info["scores"]["sonnet"], (
            f"Expected haiku score >= sonnet for short request. Scores: {info['scores']}"
        )

    def test_haiku_pattern_list_prefix(self, router: ModelRouter):
        model, _ = router.route("list all environment variables in the config")
        assert model == "haiku"

    def test_haiku_pattern_what_is(self, router: ModelRouter):
        model, _ = router.route("what is the current python version")
        assert model == "haiku"


# ---------------------------------------------------------------------------
# Sonnet as default / balanced tasks
# ---------------------------------------------------------------------------

class TestSonnetDefault:
    """Sonnet is the tie-breaker default and handles mid-complexity tasks."""

    def test_all_zeros_defaults_to_sonnet(self, router: ModelRouter):
        """When no keywords or patterns match, tie-breaking gives sonnet +1."""
        # Use a medium-length, neutral request that doesn't match any keywords
        model, info = router.route(
            "process the thing and make it work with the other thing over there"
        )
        # Sonnet must win — it gets +1 tie-break, plus possibly word count boost
        assert model == "sonnet", f"Scores: {info['scores']}"

    def test_sonnet_keywords_route_to_sonnet(self, router: ModelRouter):
        model, info = router.route("implement the user authentication feature")
        assert model == "sonnet", f"Scores: {info['scores']}"

    def test_sonnet_pattern_create(self, router: ModelRouter):
        model, _ = router.route("create a new database migration script")
        assert model == "sonnet"

    def test_sonnet_pattern_fix(self, router: ModelRouter):
        model, _ = router.route("fix the broken import in the auth module")
        assert model == "sonnet"

    def test_sonnet_pattern_refactor(self, router: ModelRouter):
        model, _ = router.route("refactor the payment service into smaller modules")
        assert model == "sonnet"

    def test_sonnet_scores_returned(self, router: ModelRouter):
        """route() always returns a scores dict with all three model keys."""
        _, info = router.route("build a simple API endpoint")
        assert set(info["scores"].keys()) == {"haiku", "sonnet", "opus"}


# ---------------------------------------------------------------------------
# File count context signals
# ---------------------------------------------------------------------------

class TestFileCountContext:
    """Context dict file_count drives sonnet/opus score bumps."""

    def test_file_count_over_10_boosts_sonnet(self, router: ModelRouter):
        """file_count > 10 adds +2 to sonnet."""
        _, info = router.route("update the codebase", context={"file_count": 15})
        assert info["scores"]["sonnet"] >= 2, (
            f"Expected sonnet bonus for file_count=15. Scores: {info['scores']}"
        )

    def test_file_count_over_50_boosts_opus(self, router: ModelRouter):
        """file_count > 50 adds +3 to opus (and still +2 to sonnet)."""
        _, info = router.route("update everything", context={"file_count": 60})
        assert info["scores"]["opus"] >= 3, (
            f"Expected opus bonus for file_count=60. Scores: {info['scores']}"
        )
        assert info["scores"]["sonnet"] >= 2, (
            f"Expected sonnet bonus too for file_count=60. Scores: {info['scores']}"
        )

    def test_file_count_over_50_often_routes_opus(self, router: ModelRouter):
        """Large file counts combined with a neutral request should route to opus."""
        model, info = router.route(
            "process all the files in the repository",
            context={"file_count": 55}
        )
        assert model == "opus", f"Scores: {info['scores']}"

    def test_small_file_count_no_bonus(self, router: ModelRouter):
        """file_count <= 10 adds no bonus to any model."""
        _, info_no_ctx = router.route("build a module")
        _, info_ctx = router.route("build a module", context={"file_count": 5})
        # Scores should be identical — small file count adds nothing
        assert info_no_ctx["scores"] == info_ctx["scores"]

    def test_lines_of_code_over_1000_boosts_sonnet(self, router: ModelRouter):
        _, info = router.route("review the code", context={"lines_of_code": 1500})
        assert info["scores"]["sonnet"] >= 2

    def test_lines_of_code_over_5000_boosts_opus(self, router: ModelRouter):
        _, info = router.route("review the code", context={"lines_of_code": 6000})
        assert info["scores"]["opus"] >= 2

    def test_steps_over_5_boosts_sonnet(self, router: ModelRouter):
        _, info = router.route("complete the task", context={"steps": 7})
        assert info["scores"]["sonnet"] >= 2

    def test_steps_over_10_boosts_opus(self, router: ModelRouter):
        _, info = router.route("complete the task", context={"steps": 12})
        assert info["scores"]["opus"] >= 3


# ---------------------------------------------------------------------------
# Word count heuristic
# ---------------------------------------------------------------------------

class TestWordCountHeuristic:
    """Word count affects scores independently of keywords."""

    def test_long_request_boosts_sonnet(self, router: ModelRouter):
        """Requests with >50 words add +2 to sonnet."""
        long_request = " ".join(["word"] * 55)
        _, info = router.route(long_request)
        assert info["scores"]["sonnet"] >= 2

    def test_very_long_request_also_boosts_opus(self, router: ModelRouter):
        """Requests with >100 words add +1 to opus on top of sonnet boost."""
        very_long = " ".join(["word"] * 110)
        _, info = router.route(very_long)
        assert info["scores"]["opus"] >= 1
        assert info["scores"]["sonnet"] >= 2


# ---------------------------------------------------------------------------
# Routing info structure
# ---------------------------------------------------------------------------

class TestRoutingInfoStructure:
    """route() should always return a well-formed info dict."""

    def test_info_keys_present(self, router: ModelRouter):
        _, info = router.route("list files")
        required_keys = {"model", "scores", "reasoning", "estimated_cost", "timestamp"}
        assert required_keys.issubset(info.keys())

    def test_estimated_cost_is_nonnegative(self, router: ModelRouter):
        for request in ["list files", "implement auth", "design architecture"]:
            _, info = router.route(request)
            assert info["estimated_cost"] >= 0.0

    def test_model_in_info_matches_returned_model(self, router: ModelRouter):
        model, info = router.route("build a feature")
        assert info["model"] == model

    def test_stats_increment_on_route(self, router: ModelRouter):
        router.route("list files")
        router.route("implement feature")
        stats = router.get_stats()
        assert stats["total_requests"] == 2

    def test_route_request_module_function(self):
        """Top-level route_request() convenience function works."""
        model, info = route_request("list all users")
        assert model in ("haiku", "sonnet", "opus")
        assert "scores" in info
