#!/usr/bin/env python3
"""
Token Usage Tracker - Real-time token and cost monitoring
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict

CLAUDE_DIR = Path.home() / '.claude'
STATS_FILE = CLAUDE_DIR / '.token-stats.json'

# Current Claude pricing (per million tokens) — update as pricing changes
PRICING: Dict[str, Dict[str, float]] = {
    'haiku': {'input': 0.25, 'output': 1.25},
    'sonnet': {'input': 3.00, 'output': 15.00},
    'opus': {'input': 15.00, 'output': 75.00}
}


class TokenTracker:
    """Track token usage and costs across all Claude models"""

    def __init__(self):
        self.stats = self._load_stats()

    def _load_stats(self) -> Dict:
        """Load existing stats or initialize a fresh store"""
        if STATS_FILE.exists():
            try:
                with open(STATS_FILE, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        return {
            'total_tokens': 0,
            'total_cost': 0.0,
            'by_model': {
                'haiku': {'requests': 0, 'tokens': 0, 'cost': 0.0},
                'sonnet': {'requests': 0, 'tokens': 0, 'cost': 0.0},
                'opus': {'requests': 0, 'tokens': 0, 'cost': 0.0}
            },
            'sessions': [],
            'last_updated': None
        }

    def record_usage(self, model: str, input_tokens: int, output_tokens: int) -> Dict:
        """
        Record token usage for a single request.

        Args:
            model: 'haiku', 'sonnet', or 'opus'
            input_tokens: Tokens in the prompt
            output_tokens: Tokens in the completion

        Returns:
            Dict with model, tokens, and cost for this request
        """
        pricing = PRICING.get(model, PRICING['sonnet'])
        cost = (
            (input_tokens / 1_000_000) * pricing['input'] +
            (output_tokens / 1_000_000) * pricing['output']
        )
        total_tokens = input_tokens + output_tokens

        self.stats['total_tokens'] += total_tokens
        self.stats['total_cost'] += cost

        model_stats = self.stats['by_model'].setdefault(model, {
            'requests': 0, 'tokens': 0, 'cost': 0.0
        })
        model_stats['requests'] += 1
        model_stats['tokens'] += total_tokens
        model_stats['cost'] += cost

        self.stats['last_updated'] = datetime.now().isoformat()

        self._save_stats()

        return {'model': model, 'tokens': total_tokens, 'cost': cost}

    def _save_stats(self) -> None:
        """Persist stats to disk"""
        STATS_FILE.parent.mkdir(exist_ok=True)
        with open(STATS_FILE, 'w') as f:
            json.dump(self.stats, f, indent=2)

    def get_current_stats(self) -> Dict:
        """Get current statistics including per-model percentage breakdown"""
        total_requests = sum(
            m['requests'] for m in self.stats['by_model'].values()
        )

        breakdown: Dict[str, int] = {}
        for model, stats in self.stats['by_model'].items():
            if total_requests > 0:
                breakdown[model] = int((stats['requests'] / total_requests) * 100)
            else:
                breakdown[model] = 0

        # Most-used model is the "current" model for display purposes
        current_model = 'sonnet'
        if total_requests > 0:
            current_model = max(
                self.stats['by_model'].items(),
                key=lambda x: x[1]['requests']
            )[0]

        return {
            'currentModel': current_model,
            'tokensUsed': self.stats['total_tokens'],
            'estimatedCost': round(self.stats['total_cost'], 2),
            'breakdown': breakdown
        }

    def reset_stats(self) -> None:
        """Reset all statistics"""
        self.stats = {
            'total_tokens': 0,
            'total_cost': 0.0,
            'by_model': {
                'haiku': {'requests': 0, 'tokens': 0, 'cost': 0.0},
                'sonnet': {'requests': 0, 'tokens': 0, 'cost': 0.0},
                'opus': {'requests': 0, 'tokens': 0, 'cost': 0.0}
            },
            'sessions': [],
            'last_updated': None
        }
        self._save_stats()


def get_stats() -> Dict:
    """Module-level convenience function to get current stats"""
    return TokenTracker().get_current_stats()


if __name__ == '__main__':
    tracker = TokenTracker()

    # Simulate some usage
    tracker.record_usage('haiku', 500, 200)
    tracker.record_usage('sonnet', 2000, 800)
    tracker.record_usage('opus', 5000, 3000)

    print("Current Stats:")
    print(json.dumps(tracker.get_current_stats(), indent=2))
