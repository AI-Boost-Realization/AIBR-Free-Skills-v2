#!/usr/bin/env python3
"""
Intelligent Model Router
Automatically selects optimal Claude model based on request complexity

Models:
- Haiku: Fast, cheap, simple tasks ($0.25/1M input, $1.25/1M output)
- Sonnet: Balanced, most tasks ($3/1M input, $15/1M output)
- Opus: Complex reasoning ($15/1M input, $75/1M output)
"""

import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

CLAUDE_DIR = Path.home() / '.claude'
ROUTING_LOG = CLAUDE_DIR / 'logs' / 'model-routing.jsonl'


class ModelRouter:
    """Intelligently route requests to optimal Claude model"""

    # Model costs (per 1M tokens)
    COSTS: Dict[str, Dict[str, float]] = {
        'haiku': {'input': 0.25, 'output': 1.25},
        'sonnet': {'input': 3.00, 'output': 15.00},
        'opus': {'input': 15.00, 'output': 75.00}
    }

    # Complexity indicators
    COMPLEXITY_KEYWORDS: Dict[str, List[str]] = {
        'haiku': [
            'simple', 'quick', 'list', 'check', 'status', 'show',
            'what is', 'basic', 'read', 'get', 'fetch'
        ],
        'sonnet': [
            'create', 'build', 'implement', 'write', 'modify',
            'refactor', 'update', 'add', 'fix', 'debug',
            'analyze', 'review', 'test'
        ],
        'opus': [
            'complex', 'architec', 'design', 'plan', 'strategy',
            'multiple', 'system', 'integration', 'optimize',
            'critical', 'production', 'performance', 'security',
            'scale', 'enterprise', 'comprehensive'
        ]
    }

    # Task type patterns
    TASK_PATTERNS: Dict[str, List[str]] = {
        'haiku': [
            r'^list\s+',
            r'^show\s+',
            r'^get\s+',
            r'^what\s+(is|are)',
            r'^check\s+',
            r'^status\s+of',
            r'simple.*?query',
        ],
        'sonnet': [
            r'^create\s+',
            r'^build\s+',
            r'^implement\s+',
            r'^write\s+',
            r'^fix\s+',
            r'^debug\s+',
            r'^add\s+feature',
            r'^refactor\s+',
        ],
        'opus': [
            r'^design\s+(system|architecture)',
            r'^plan\s+.*?(strategy|approach)',
            r'complex.*?(workflow|system)',
            r'multi-.*?agent',
            r'enterprise.*?solution',
            r'^architect\s+',
            r'optimize.*?(performance|system)',
        ]
    }

    def __init__(self):
        self.usage_log: List[Dict] = []
        self.model_stats: Dict[str, Dict] = {
            'haiku': {'uses': 0, 'tokens': 0, 'cost': 0.0},
            'sonnet': {'uses': 0, 'tokens': 0, 'cost': 0.0},
            'opus': {'uses': 0, 'tokens': 0, 'cost': 0.0}
        }

    def route(self, request: str, context: Optional[Dict] = None) -> Tuple[str, Dict]:
        """
        Route request to optimal model.

        Args:
            request: User's request text
            context: Additional context (file_count, lines_of_code, steps, critical)

        Returns:
            (model_name, routing_info)
        """
        request_lower = request.lower()
        scores: Dict[str, float] = {'haiku': 0.0, 'sonnet': 0.0, 'opus': 0.0}

        # 1. Keyword analysis
        for model, keywords in self.COMPLEXITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in request_lower:
                    scores[model] += 1

        # 2. Pattern matching (patterns weigh more than keywords)
        for model, patterns in self.TASK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, request_lower):
                    scores[model] += 3

        # 3. Context analysis
        if context:
            if context.get('file_count', 0) > 10:
                scores['sonnet'] += 2
            if context.get('file_count', 0) > 50:
                scores['opus'] += 3

            if context.get('lines_of_code', 0) > 1000:
                scores['sonnet'] += 2
            if context.get('lines_of_code', 0) > 5000:
                scores['opus'] += 2

            if context.get('steps', 0) > 5:
                scores['sonnet'] += 2
            if context.get('steps', 0) > 10:
                scores['opus'] += 3

            if context.get('critical', False):
                scores['opus'] += 5

        # 4. Request length analysis
        word_count = len(request.split())
        if word_count < 10:
            scores['haiku'] += 2
        elif word_count > 50:
            scores['sonnet'] += 2
        if word_count > 100:
            scores['opus'] += 1

        # 5. Default to Sonnet on a tie
        if scores['haiku'] == scores['sonnet'] == scores['opus']:
            scores['sonnet'] += 1

        selected_model = max(scores.items(), key=lambda x: x[1])[0]

        routing_info = {
            'model': selected_model,
            'scores': scores,
            'reasoning': self._explain_routing(selected_model, scores, request),
            'estimated_cost': self._estimate_cost(selected_model, request),
            'timestamp': datetime.now().isoformat()
        }

        self._log_routing(request, selected_model, routing_info)

        return selected_model, routing_info

    def _explain_routing(self, model: str, scores: Dict[str, float], request: str) -> str:
        """Generate human-readable explanation for routing decision"""
        reasons: List[str] = []

        if model == 'haiku':
            reasons.append("Simple query detected")
            reasons.append("Optimized for speed and cost")
        elif model == 'sonnet':
            reasons.append("Balanced complexity")
            reasons.append("Best general-purpose model")
        elif model == 'opus':
            reasons.append("Complex reasoning required")
            reasons.append("High-quality output prioritized")

        request_lower = request.lower()
        trigger_map = {
            'architecture': 'opus',
            'quick': 'haiku',
            'implement': 'sonnet',
        }
        for keyword, target_model in trigger_map.items():
            if keyword in request_lower and model == target_model:
                reasons.append(f"'{keyword}' keyword detected")

        return " | ".join(reasons)

    def _estimate_cost(self, model: str, request: str) -> float:
        """Estimate cost for this request"""
        # Rough estimation: 1 word ~= 1.3 tokens
        estimated_tokens = len(request.split()) * 1.3
        input_tokens = estimated_tokens
        output_tokens = estimated_tokens * 2  # assume response is ~2x request

        pricing = self.COSTS[model]
        cost = (
            (input_tokens / 1_000_000) * pricing['input'] +
            (output_tokens / 1_000_000) * pricing['output']
        )
        return round(cost, 6)

    def _log_routing(self, request: str, model: str, info: Dict) -> None:
        """Log routing decision for analysis"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'request_preview': request[:100],
            'model': model,
            'scores': info['scores'],
            'estimated_cost': info['estimated_cost']
        }

        self.usage_log.append(log_entry)
        self.model_stats[model]['uses'] += 1

        try:
            ROUTING_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(ROUTING_LOG, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except OSError:
            pass

    def get_stats(self) -> Dict:
        """Get usage statistics"""
        total_cost = sum(stats['cost'] for stats in self.model_stats.values())
        total_uses = sum(stats['uses'] for stats in self.model_stats.values())

        return {
            'total_requests': total_uses,
            'total_cost': round(total_cost, 2),
            'by_model': self.model_stats,
            'cost_breakdown': {
                model: round((stats['cost'] / total_cost * 100) if total_cost > 0 else 0.0, 1)
                for model, stats in self.model_stats.items()
            }
        }

    def optimize_recommendation(self) -> Dict:
        """Analyze usage and recommend optimizations"""
        stats = self.get_stats()
        recommendations: List[Dict] = []

        opus_percentage = stats['cost_breakdown'].get('opus', 0)
        if opus_percentage > 50:
            recommendations.append({
                'type': 'cost_optimization',
                'message': (
                    f'Opus usage is {opus_percentage}% of costs. '
                    'Consider if all Opus requests need that level of reasoning.'
                ),
                'potential_savings': 'Varies by workload'
            })

        haiku_percentage = stats['cost_breakdown'].get('haiku', 0)
        if haiku_percentage < 10:
            recommendations.append({
                'type': 'efficiency',
                'message': (
                    f'Only {haiku_percentage}% Haiku usage. '
                    'More simple tasks could use the faster, cheaper model.'
                ),
                'potential_savings': 'Up to 10x faster responses on simple tasks'
            })

        return {
            'stats': stats,
            'recommendations': recommendations
        }


# Global router instance
router = ModelRouter()


def route_request(request: str, context: Optional[Dict] = None) -> Tuple[str, Dict]:
    """
    Main routing function.

    Usage:
        model, info = route_request("Create a complex system architecture")
    """
    return router.route(request, context)


def get_routing_stats() -> Dict:
    """Get current routing statistics"""
    return router.get_stats()


def get_recommendations() -> Dict:
    """Get optimization recommendations"""
    return router.optimize_recommendation()


# CLI Interface
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python model-router.py '<request>'")
        print("       python model-router.py stats")
        print("       python model-router.py recommend")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'stats':
        stats = get_routing_stats()
        print(json.dumps(stats, indent=2))

    elif command == 'recommend':
        recs = get_recommendations()
        print(json.dumps(recs, indent=2))

    else:
        request = ' '.join(sys.argv[1:])
        model, info = route_request(request)

        print(f"Selected Model: {model.upper()}")
        print(f"Reasoning: {info['reasoning']}")
        print(f"Estimated Cost: ${info['estimated_cost']}")
        print(f"Scores: {info['scores']}")
