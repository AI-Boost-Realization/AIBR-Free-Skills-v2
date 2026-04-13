#!/usr/bin/env python3
"""
Activity Logger - Track orchestrator activity for the dashboard
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

CLAUDE_DIR = Path.home() / '.claude'
ACTIVITY_FILE = CLAUDE_DIR / '.recent-activity.json'
MAX_ACTIVITIES = 50


class ActivityLogger:
    """Log orchestrator activities to a rolling JSON file"""

    def __init__(self):
        self.activities: List[Dict] = self._load_activities()

    def _load_activities(self) -> List[Dict]:
        """Load recent activities from disk"""
        if ACTIVITY_FILE.exists():
            try:
                with open(ACTIVITY_FILE, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return []

    def log_activity(
        self,
        activity_type: str,
        description: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Log a single activity.

        Args:
            activity_type: Category string, e.g. 'skill_created', 'context_switch'
            description: Human-readable description
            metadata: Arbitrary additional data

        Returns:
            The activity dict that was saved
        """
        activity: Dict = {
            'type': activity_type,
            'description': description,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }

        self.activities.insert(0, activity)

        if len(self.activities) > MAX_ACTIVITIES:
            self.activities = self.activities[:MAX_ACTIVITIES]

        self._save_activities()

        return activity

    def _save_activities(self) -> None:
        """Persist activities to disk"""
        ACTIVITY_FILE.parent.mkdir(exist_ok=True)
        with open(ACTIVITY_FILE, 'w') as f:
            json.dump(self.activities, f, indent=2)

    def get_recent(self, limit: int = 10) -> List[Dict]:
        """Get the N most recent activities"""
        return self.activities[:limit]

    def clear_old(self, days: int = 7) -> None:
        """Remove activities older than N days"""
        cutoff = datetime.now() - timedelta(days=days)
        self.activities = [
            a for a in self.activities
            if datetime.fromisoformat(a['timestamp']) > cutoff
        ]
        self._save_activities()


def log(activity_type: str, description: str, **metadata) -> Dict:
    """
    Module-level convenience function for one-line logging.

    Usage:
        from activity_logger import log as log_activity
        log_activity('skill_executed', 'Auto-ran /deploy', skill='deploy')
    """
    logger = ActivityLogger()
    return logger.log_activity(activity_type, description, metadata if metadata else None)


if __name__ == '__main__':
    logger = ActivityLogger()

    logger.log_activity('skill_created', 'Auto-created deploy-test skill', {
        'pattern': ['git', 'add', 'commit'],
        'count': 3
    })

    logger.log_activity('context_switch', 'Switched to web-app project', {
        'from': 'api',
        'to': 'web-app'
    })

    logger.log_activity('mcp_configured', 'Added github-official MCP server', {
        'reason': 'Detected .git directory'
    })

    print("Recent Activities:")
    for activity in logger.get_recent(5):
        print(f"- {activity['type']}: {activity['description']}")
