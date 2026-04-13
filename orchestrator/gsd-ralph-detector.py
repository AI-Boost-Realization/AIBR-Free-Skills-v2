#!/usr/bin/env python3
"""
GSD + Ralph Wiggum Auto-Detector

Automatically determines when to use GSD project management or Ralph loops
based on project context and user message content.

GSD (Get Stuff Done) is a structured project management framework with
.planning/ directories containing STATE.md, ROADMAP.md, and PROJECT.md.

Ralph Wiggum loops are iterative fix-until-done patterns: run a command,
check output, fix errors, repeat until a completion condition is satisfied.
The name refers to the Simpsons character who repeats the same action
regardless of outcome — Claude shouldn't do this blindly, but the controlled
version (with a max iteration cap and clear exit condition) is genuinely useful.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional

try:
    from activity_logger import log as log_activity
except ImportError:
    def log_activity(activity_type: str, description: str, **metadata) -> None:
        pass


class GSDRalphDetector:
    """Detects when to use GSD and/or Ralph Wiggum loops"""

    # Keywords that indicate a Ralph loop would be useful
    RALPH_KEYWORDS: List[str] = [
        'until', 'iterate', 'keep trying', 'all tests pass',
        'fix bugs', 'make it work', 'run tests', 'coverage',
        'keep going', 'repeatedly', 'loop'
    ]

    # Keywords that indicate GSD project management is relevant
    GSD_KEYWORDS: List[str] = [
        "what's next", 'status', 'progress', 'continue',
        'roadmap', 'milestone', 'phase', 'plan'
    ]

    def __init__(self):
        self.last_detection: Optional[str] = None

    def detect(self, cwd: Path, user_message: Optional[str] = None) -> Dict:
        """
        Detect if GSD and/or Ralph loops should be used.

        Returns:
            Dict with keys:
                use_gsd: bool
                use_ralph: bool
                gsd_ready: bool — True if .planning/ structure is complete
                gsd_needs_init: bool — True if .planning/ exists but is incomplete
                ralph_max_iterations: int
                confidence: float (0.0–1.0)
                suggestion: str | None — slash command to run
                reasoning: list[str] — human-readable reasons for detection
        """
        result: Dict = {
            'use_gsd': False,
            'use_ralph': False,
            'gsd_ready': False,
            'gsd_needs_init': False,
            'ralph_max_iterations': 20,
            'confidence': 0.0,
            'suggestion': None,
            'reasoning': []
        }

        gsd_score = self._check_gsd(cwd, user_message)
        if gsd_score['detected']:
            result['use_gsd'] = True
            result['gsd_ready'] = gsd_score['ready']
            result['gsd_needs_init'] = gsd_score['needs_init']
            result['reasoning'].extend(gsd_score['reasons'])
            result['confidence'] += gsd_score['confidence']

        ralph_score = self._check_ralph(cwd, user_message)
        if ralph_score['detected']:
            result['use_ralph'] = True
            result['ralph_max_iterations'] = ralph_score['max_iterations']
            result['reasoning'].extend(ralph_score['reasons'])
            result['confidence'] += ralph_score['confidence']

        if result['confidence'] > 0:
            result['confidence'] = min(result['confidence'], 1.0)

        result['suggestion'] = self._generate_suggestion(result)

        detection_key = f"gsd:{result['use_gsd']},ralph:{result['use_ralph']}"
        if detection_key != self.last_detection:
            self._log_detection(result)
            self.last_detection = detection_key

        return result

    def _check_gsd(self, cwd: Path, user_message: Optional[str]) -> Dict:
        """Check if GSD framework should be used"""
        score: Dict = {
            'detected': False,
            'ready': False,
            'needs_init': False,
            'confidence': 0.0,
            'reasons': []
        }

        planning_dir = cwd / '.planning'
        if planning_dir.exists():
            score['detected'] = True
            score['confidence'] += 0.5
            score['reasons'].append('Found .planning directory')

            required_files = [
                planning_dir / 'STATE.md',
                planning_dir / 'ROADMAP.md',
                planning_dir / 'PROJECT.md',
            ]
            if all(f.exists() for f in required_files):
                score['ready'] = True
                score['confidence'] += 0.3
                score['reasons'].append('GSD structure complete')
            else:
                score['needs_init'] = True
                score['reasons'].append('GSD structure incomplete — missing STATE/ROADMAP/PROJECT')

        if user_message:
            msg_lower = user_message.lower()
            matches = [kw for kw in self.GSD_KEYWORDS if kw in msg_lower]
            if matches:
                score['detected'] = True
                score['confidence'] += 0.2
                score['reasons'].append(f'User mentioned: {matches[0]}')

        return score

    def _check_ralph(self, cwd: Path, user_message: Optional[str]) -> Dict:
        """Check if a Ralph Wiggum loop would be beneficial"""
        score: Dict = {
            'detected': False,
            'max_iterations': 20,
            'confidence': 0.0,
            'reasons': []
        }

        if user_message:
            msg_lower = user_message.lower()
            matches = [kw for kw in self.RALPH_KEYWORDS if kw in msg_lower]
            if matches:
                score['detected'] = True
                score['confidence'] += 0.3
                score['reasons'].append(f'Iterative task keyword: "{matches[0]}"')

            if self._has_completion_criteria(user_message):
                score['confidence'] += 0.2
                score['reasons'].append('Clear completion criteria found')

        test_indicators = self._find_test_files(cwd)
        if test_indicators['has_tests']:
            score['confidence'] += 0.2
            score['reasons'].append(
                f'Found {test_indicators["count"]} test file(s)'
            )

            if user_message and 'test' in user_message.lower():
                score['detected'] = True
                score['confidence'] += 0.3

        if score['detected']:
            score['max_iterations'] = self._estimate_iterations(
                user_message, test_indicators
            )

        return score

    def _has_completion_criteria(self, message: str) -> bool:
        """Check if the message contains a clear done condition"""
        patterns = [
            r'when .+ pass',
            r'until .+ (works|succeeds|completes)',
            r'coverage >\s*\d+%',
            r'zero errors',
            r'build (passes|succeeds)',
            r'all .+ (pass|work|succeed)'
        ]
        return any(re.search(p, message.lower()) for p in patterns)

    def _find_test_files(self, cwd: Path) -> Dict:
        """Find test files in the project"""
        test_patterns = [
            '**/test*.py',
            '**/*test.py',
            '**/*.test.js',
            '**/*.test.ts',
            '**/*.spec.js',
            '**/*.spec.ts',
            '**/tests/**/*.py',
            '**/tests/**/*.js',
        ]

        test_files: List[Path] = []
        for pattern in test_patterns:
            test_files.extend(cwd.glob(pattern))

        return {
            'has_tests': len(test_files) > 0,
            'count': len(test_files),
            'files': [str(f.relative_to(cwd)) for f in test_files[:5]]
        }

    def _estimate_iterations(
        self, message: Optional[str], test_info: Dict
    ) -> int:
        """Estimate appropriate max iterations for a Ralph loop"""
        iterations = 20

        if message:
            msg_lower = message.lower()

            if any(word in msg_lower for word in ['fix', 'bug', 'typo']):
                iterations = 10

            if any(word in msg_lower for word in
                   ['system', 'integration', 'refactor', 'architecture']):
                iterations = 50

            if 'coverage' in msg_lower:
                iterations = 30

        if test_info['has_tests'] and test_info['count'] > 20:
            iterations = max(iterations, 30)

        return iterations

    def _generate_suggestion(self, result: Dict) -> Optional[str]:
        """Generate an actionable slash command suggestion"""
        if not (result['use_gsd'] or result['use_ralph']):
            return None

        suggestions: List[str] = []

        if result['use_gsd']:
            if result['gsd_ready']:
                suggestions.append('/gsd:progress')
            elif result['gsd_needs_init']:
                suggestions.append('/gsd:new-project')

        if result['use_ralph']:
            iterations = result['ralph_max_iterations']
            suggestions.append(
                f'/ralph-loop "[task description]" '
                f'--max-iterations {iterations} '
                '--completion-promise "[done condition]"'
            )

        if result['use_gsd'] and result['use_ralph']:
            suggestions = ['/gsd:progress (then use ralph-loop for individual plans)']

        return ' OR '.join(suggestions)

    def _log_detection(self, result: Dict) -> None:
        """Log detection to the activity feed"""
        if result['use_gsd'] and result['use_ralph']:
            log_activity(
                'workflow_detected',
                'Auto-detected GSD + Ralph loop workflow',
                suggestion=result['suggestion'],
                confidence=result['confidence']
            )
        elif result['use_gsd']:
            log_activity(
                'workflow_detected',
                'Auto-detected GSD project management',
                suggestion=result['suggestion'],
                confidence=result['confidence']
            )
        elif result['use_ralph']:
            log_activity(
                'workflow_detected',
                'Auto-detected Ralph loop opportunity',
                suggestion=result['suggestion'],
                iterations=result['ralph_max_iterations'],
                confidence=result['confidence']
            )


def detect_workflow(cwd: Optional[Path] = None, user_message: Optional[str] = None) -> Dict:
    """
    Convenience function: detect appropriate workflow for the current directory.

    Usage:
        from gsd_ralph_detector import detect_workflow
        result = detect_workflow(user_message="Fix all type errors until build passes")
        if result['use_ralph']:
            print(result['suggestion'])
    """
    if cwd is None:
        cwd = Path.cwd()
    return GSDRalphDetector().detect(cwd, user_message)


if __name__ == '__main__':
    detector = GSDRalphDetector()

    print("Test 1: GSD Project Detection")
    result = detector.detect(Path.cwd(), "What should I work on next?")
    print(f"  Use GSD: {result['use_gsd']}")
    print(f"  Suggestion: {result['suggestion']}")
    print(f"  Reasoning: {', '.join(result['reasoning'])}")
    print()

    print("Test 2: Ralph Loop Detection")
    result = detector.detect(Path.cwd(), "Fix all the type errors until the build passes")
    print(f"  Use Ralph: {result['use_ralph']}")
    print(f"  Max Iterations: {result['ralph_max_iterations']}")
    print(f"  Suggestion: {result['suggestion']}")
    print(f"  Reasoning: {', '.join(result['reasoning'])}")
    print()

    print("Test 3: Combined GSD + Ralph")
    result = detector.detect(
        Path.cwd(),
        "Execute the authentication plan and make all tests pass"
    )
    print(f"  Use GSD: {result['use_gsd']}")
    print(f"  Use Ralph: {result['use_ralph']}")
    print(f"  Confidence: {result['confidence']:.2f}")
    print(f"  Suggestion: {result['suggestion']}")
    print(f"  Reasoning: {', '.join(result['reasoning'])}")
