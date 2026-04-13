"""
Tests for gsd-ralph-detector.py — GSDRalphDetector class.

Covers:
- GSD detection via .planning/ directory presence and completeness
- GSD detection via user message keywords
- Ralph loop detection via iterative-task keywords
- _has_completion_criteria pattern matching
- _estimate_iterations logic
- Confidence capping at 1.0
- Suggestion generation
- Combined GSD + Ralph detection
"""

import importlib.util
from pathlib import Path
from typing import Dict

import pytest

# ---------------------------------------------------------------------------
# Import the hyphen-named module
# ---------------------------------------------------------------------------
_MODULE_PATH = Path(__file__).parent.parent / "gsd-ralph-detector.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("gsd_ralph_detector", _MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_mod = _load_module()
GSDRalphDetector = _mod.GSDRalphDetector
detect_workflow = _mod.detect_workflow


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def detector() -> GSDRalphDetector:
    """Fresh detector instance per test."""
    return GSDRalphDetector()


@pytest.fixture()
def empty_dir(tmp_path: Path) -> Path:
    """A temporary directory with no special structure."""
    return tmp_path


@pytest.fixture()
def gsd_complete_dir(tmp_path: Path) -> Path:
    """A directory with a fully-populated .planning/ structure."""
    planning = tmp_path / ".planning"
    planning.mkdir()
    (planning / "STATE.md").write_text("# State")
    (planning / "ROADMAP.md").write_text("# Roadmap")
    (planning / "PROJECT.md").write_text("# Project")
    return tmp_path


@pytest.fixture()
def gsd_incomplete_dir(tmp_path: Path) -> Path:
    """A directory with .planning/ present but missing required files."""
    planning = tmp_path / ".planning"
    planning.mkdir()
    (planning / "STATE.md").write_text("# State")
    # ROADMAP.md and PROJECT.md intentionally absent
    return tmp_path


# ---------------------------------------------------------------------------
# GSD detection — filesystem
# ---------------------------------------------------------------------------

class TestGSDFilesystemDetection:
    """GSD is detected from .planning/ directory presence and completeness."""

    def test_no_planning_dir_no_gsd(self, detector: GSDRalphDetector, empty_dir: Path):
        result = detector.detect(empty_dir)
        assert result["use_gsd"] is False
        assert result["gsd_ready"] is False
        assert result["gsd_needs_init"] is False

    def test_complete_planning_dir_detected_ready(
        self, detector: GSDRalphDetector, gsd_complete_dir: Path
    ):
        result = detector.detect(gsd_complete_dir)
        assert result["use_gsd"] is True
        assert result["gsd_ready"] is True
        assert result["gsd_needs_init"] is False

    def test_complete_planning_dir_confidence(
        self, detector: GSDRalphDetector, gsd_complete_dir: Path
    ):
        result = detector.detect(gsd_complete_dir)
        # .planning exists (+0.5) + all files present (+0.3) = 0.8 minimum
        assert result["confidence"] >= 0.8

    def test_incomplete_planning_dir_needs_init(
        self, detector: GSDRalphDetector, gsd_incomplete_dir: Path
    ):
        result = detector.detect(gsd_incomplete_dir)
        assert result["use_gsd"] is True
        assert result["gsd_ready"] is False
        assert result["gsd_needs_init"] is True

    def test_incomplete_dir_reasoning_mentions_missing_files(
        self, detector: GSDRalphDetector, gsd_incomplete_dir: Path
    ):
        result = detector.detect(gsd_incomplete_dir)
        combined = " ".join(result["reasoning"]).lower()
        assert "incomplete" in combined or "missing" in combined


# ---------------------------------------------------------------------------
# GSD detection — keyword signals
# ---------------------------------------------------------------------------

class TestGSDKeywordDetection:
    """GSD keywords in user messages also trigger detection."""

    @pytest.mark.parametrize("message", [
        "what's next on the roadmap",
        "show me the project status",
        "continue from where we left off",
        "what's the progress on phase two",
        "what milestone are we on",
        "what's the plan for this sprint",
    ])
    def test_gsd_keyword_triggers_gsd(
        self, detector: GSDRalphDetector, empty_dir: Path, message: str
    ):
        result = detector.detect(empty_dir, user_message=message)
        assert result["use_gsd"] is True, (
            f"Expected use_gsd=True for message {message!r}, got {result}"
        )

    def test_gsd_keyword_adds_confidence(
        self, detector: GSDRalphDetector, empty_dir: Path
    ):
        result = detector.detect(empty_dir, user_message="what's the current status")
        assert result["confidence"] >= 0.2

    def test_irrelevant_message_no_gsd(
        self, detector: GSDRalphDetector, empty_dir: Path
    ):
        result = detector.detect(empty_dir, user_message="fix the typo in auth.py")
        assert result["use_gsd"] is False


# ---------------------------------------------------------------------------
# Ralph detection — keyword signals
# ---------------------------------------------------------------------------

class TestRalphKeywordDetection:
    """Ralph loop is detected from iterative-task keywords in user messages."""

    @pytest.mark.parametrize("message", [
        "fix all the type errors until the build passes",
        "keep trying until all tests pass",
        "iterate on this until it works",
        "run tests and loop until coverage is satisfied",
        "keep going until all bugs are resolved",
        "run the build repeatedly until zero errors",
    ])
    def test_ralph_keyword_triggers_ralph(
        self, detector: GSDRalphDetector, empty_dir: Path, message: str
    ):
        result = detector.detect(empty_dir, user_message=message)
        assert result["use_ralph"] is True, (
            f"Expected use_ralph=True for {message!r}, got {result}"
        )

    def test_ralph_adds_confidence(
        self, detector: GSDRalphDetector, empty_dir: Path
    ):
        result = detector.detect(
            empty_dir, user_message="keep trying until all tests pass"
        )
        assert result["confidence"] >= 0.3

    def test_non_iterative_message_no_ralph(
        self, detector: GSDRalphDetector, empty_dir: Path
    ):
        result = detector.detect(
            empty_dir, user_message="create a new route in the API"
        )
        assert result["use_ralph"] is False


# ---------------------------------------------------------------------------
# _has_completion_criteria
# ---------------------------------------------------------------------------

class TestCompletionCriteria:
    """_has_completion_criteria detects clear done conditions."""

    @pytest.mark.parametrize("message", [
        "keep going when tests pass",
        "run until the build succeeds",
        "iterate until coverage > 80%",
        "fix until zero errors remain",
        "repeat until build passes",
        "continue until all tests pass",
    ])
    def test_detects_completion_criteria(
        self, detector: GSDRalphDetector, message: str
    ):
        assert detector._has_completion_criteria(message) is True, (
            f"Expected completion criteria detected in: {message!r}"
        )

    @pytest.mark.parametrize("message", [
        "fix the typo in auth.py",
        "add a new API endpoint",
        "refactor the payment module",
    ])
    def test_no_false_positives(self, detector: GSDRalphDetector, message: str):
        assert detector._has_completion_criteria(message) is False


# ---------------------------------------------------------------------------
# _estimate_iterations
# ---------------------------------------------------------------------------

class TestEstimateIterations:
    """_estimate_iterations returns context-appropriate iteration caps."""

    def _make_test_info(self, has_tests: bool = False, count: int = 0) -> Dict:
        return {"has_tests": has_tests, "count": count, "files": []}

    def test_default_iterations(self, detector: GSDRalphDetector):
        result = detector._estimate_iterations(None, self._make_test_info())
        assert result == 20

    def test_fix_bug_message_reduces_iterations(self, detector: GSDRalphDetector):
        result = detector._estimate_iterations("fix this bug", self._make_test_info())
        assert result == 10

    def test_typo_message_reduces_iterations(self, detector: GSDRalphDetector):
        result = detector._estimate_iterations(
            "correct the typo in the handler", self._make_test_info()
        )
        assert result == 10

    def test_system_message_increases_iterations(self, detector: GSDRalphDetector):
        result = detector._estimate_iterations(
            "refactor the entire system", self._make_test_info()
        )
        assert result == 50

    def test_architecture_message_increases_iterations(self, detector: GSDRalphDetector):
        result = detector._estimate_iterations(
            "redesign the integration architecture", self._make_test_info()
        )
        assert result == 50

    def test_coverage_message_sets_30(self, detector: GSDRalphDetector):
        result = detector._estimate_iterations(
            "improve test coverage to 90%", self._make_test_info()
        )
        assert result == 30

    def test_large_test_suite_raises_floor(self, detector: GSDRalphDetector):
        """More than 20 test files raises the floor to at least 30."""
        big_suite = self._make_test_info(has_tests=True, count=25)
        result = detector._estimate_iterations(None, big_suite)
        assert result >= 30

    def test_small_test_suite_keeps_default(self, detector: GSDRalphDetector):
        small_suite = self._make_test_info(has_tests=True, count=5)
        result = detector._estimate_iterations(None, small_suite)
        assert result == 20


# ---------------------------------------------------------------------------
# Confidence capping
# ---------------------------------------------------------------------------

class TestConfidenceCap:
    """Confidence is capped at 1.0 regardless of stacked signals."""

    def test_confidence_never_exceeds_1(
        self, detector: GSDRalphDetector, gsd_complete_dir: Path
    ):
        # Combine filesystem signals with keywords — confidence should stay <= 1.0
        result = detector.detect(
            gsd_complete_dir,
            user_message="what's the status and keep trying until all tests pass"
        )
        assert result["confidence"] <= 1.0

    def test_no_signals_confidence_is_zero(
        self, detector: GSDRalphDetector, empty_dir: Path
    ):
        result = detector.detect(empty_dir, user_message="refactor the auth module")
        assert result["confidence"] == 0.0


# ---------------------------------------------------------------------------
# Suggestion generation
# ---------------------------------------------------------------------------

class TestSuggestionGeneration:
    """_generate_suggestion returns appropriate slash commands."""

    def test_no_signals_no_suggestion(
        self, detector: GSDRalphDetector, empty_dir: Path
    ):
        result = detector.detect(empty_dir, user_message="create a new endpoint")
        assert result["suggestion"] is None

    def test_gsd_ready_suggests_progress(
        self, detector: GSDRalphDetector, gsd_complete_dir: Path
    ):
        result = detector.detect(gsd_complete_dir)
        assert result["suggestion"] is not None
        assert "/gsd:progress" in result["suggestion"]

    def test_gsd_needs_init_suggests_new_project(
        self, detector: GSDRalphDetector, gsd_incomplete_dir: Path
    ):
        result = detector.detect(gsd_incomplete_dir)
        assert result["suggestion"] is not None
        assert "/gsd:new-project" in result["suggestion"]

    def test_ralph_only_suggests_ralph_loop(
        self, detector: GSDRalphDetector, empty_dir: Path
    ):
        result = detector.detect(
            empty_dir,
            user_message="keep trying until all tests pass"
        )
        assert result["suggestion"] is not None
        assert "/ralph-loop" in result["suggestion"]

    def test_ralph_suggestion_includes_max_iterations(
        self, detector: GSDRalphDetector, empty_dir: Path
    ):
        result = detector.detect(
            empty_dir,
            user_message="iterate until all tests pass"
        )
        assert "--max-iterations" in result["suggestion"]

    def test_combined_gsd_ralph_suggestion_mentions_gsd_first(
        self, detector: GSDRalphDetector, gsd_complete_dir: Path
    ):
        result = detector.detect(
            gsd_complete_dir,
            user_message="continue progress and keep trying until all tests pass"
        )
        assert result["suggestion"] is not None
        assert "/gsd:progress" in result["suggestion"]


# ---------------------------------------------------------------------------
# Combined detection
# ---------------------------------------------------------------------------

class TestCombinedDetection:
    """GSD and Ralph can both fire at once."""

    def test_both_detected_when_signals_present(
        self, detector: GSDRalphDetector, gsd_complete_dir: Path
    ):
        result = detector.detect(
            gsd_complete_dir,
            user_message="run the plan and keep going until all tests pass"
        )
        assert result["use_gsd"] is True
        assert result["use_ralph"] is True

    def test_result_keys_always_present(
        self, detector: GSDRalphDetector, empty_dir: Path
    ):
        result = detector.detect(empty_dir)
        expected_keys = {
            "use_gsd", "use_ralph", "gsd_ready", "gsd_needs_init",
            "ralph_max_iterations", "confidence", "suggestion", "reasoning"
        }
        assert expected_keys.issubset(result.keys())

    def test_reasoning_is_a_list(
        self, detector: GSDRalphDetector, empty_dir: Path
    ):
        result = detector.detect(empty_dir)
        assert isinstance(result["reasoning"], list)


# ---------------------------------------------------------------------------
# detect_workflow convenience function
# ---------------------------------------------------------------------------

class TestDetectWorkflow:
    """Module-level detect_workflow() function works correctly."""

    def test_detect_workflow_with_none_cwd(self):
        """cwd=None defaults to Path.cwd() without raising."""
        result = detect_workflow(user_message="list the files")
        assert "use_gsd" in result
        assert "use_ralph" in result

    def test_detect_workflow_with_explicit_path(self, tmp_path: Path):
        result = detect_workflow(cwd=tmp_path, user_message="fix the bug")
        assert result["use_gsd"] is False
