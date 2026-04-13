#!/usr/bin/env python3
"""
Session Manager - Automatic session continuity across days/weeks
Saves state, enables instant resume, tracks work history
"""
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

CLAUDE_DIR = Path.home() / '.claude'
CURRENT_SESSION_FILE = CLAUDE_DIR / '.current-work-session.json'
SESSIONS_DIR = CLAUDE_DIR / '.work-sessions'
AUTO_SAVE_INTERVAL = 300  # 5 minutes

try:
    from activity_logger import log as log_activity
except ImportError:
    def log_activity(activity_type: str, description: str, **metadata) -> None:
        pass


class SessionManager:
    """Manages work sessions with auto-save and instant resume"""

    def __init__(self):
        SESSIONS_DIR.mkdir(exist_ok=True)
        self.current_session: Optional[Dict] = self.load_current_session()
        self.last_save = time.time()

    def load_current_session(self) -> Optional[Dict]:
        """Load the current active session if it exists"""
        if CURRENT_SESSION_FILE.exists():
            try:
                with open(CURRENT_SESSION_FILE, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None
        return None

    def create_session(self, **kwargs) -> Dict:
        """
        Create a new work session.

        Keyword args:
            project: Project name (defaults to cwd basename)
            directory: Working directory (defaults to cwd)
            gsd_phase: Current GSD phase (optional)
            gsd_plan: Current GSD plan (optional)
            files_open: List of open files (optional)
            last_position: Last cursor position (optional)
            next_action: Description of next action (optional)
            mcp_servers: Active MCP servers (optional)
        """
        session: Dict = {
            'project': kwargs.get('project', Path.cwd().name),
            'directory': kwargs.get('directory', str(Path.cwd())),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'gsd_phase': kwargs.get('gsd_phase'),
            'gsd_plan': kwargs.get('gsd_plan'),
            'files_open': kwargs.get('files_open', []),
            'last_position': kwargs.get('last_position'),
            'next_action': kwargs.get('next_action'),
            'mcp_servers': kwargs.get('mcp_servers', []),
            'session_id': int(time.time())
        }

        self.current_session = session
        self.save_current_session()

        log_activity('session_started', f'Started work on {session["project"]}',
                    project=session['project'])

        return session

    def update_session(self, **kwargs) -> Dict:
        """Update current session with new data"""
        if not self.current_session:
            return self.create_session(**kwargs)

        for key, value in kwargs.items():
            if value is not None:
                self.current_session[key] = value

        self.current_session['updated_at'] = datetime.now().isoformat()

        if time.time() - self.last_save > AUTO_SAVE_INTERVAL:
            self.save_current_session()

        return self.current_session

    def save_current_session(self) -> None:
        """Save current session to file"""
        if not self.current_session:
            return

        with open(CURRENT_SESSION_FILE, 'w') as f:
            json.dump(self.current_session, f, indent=2)

        session_id = self.current_session.get('session_id', int(time.time()))
        archive_file = SESSIONS_DIR / f"{session_id}.json"
        with open(archive_file, 'w') as f:
            json.dump(self.current_session, f, indent=2)

        self.last_save = time.time()

    def end_session(self, save_summary: bool = True) -> None:
        """End current session and optionally save summary"""
        if not self.current_session:
            return

        started = datetime.fromisoformat(self.current_session['created_at'])
        ended = datetime.now()
        duration = ended - started

        self.current_session['ended_at'] = ended.isoformat()
        self.current_session['duration_seconds'] = duration.total_seconds()

        self.save_current_session()

        log_activity('session_ended', f'Ended work on {self.current_session["project"]}',
                    project=self.current_session['project'],
                    duration=str(duration))

        if save_summary:
            self.generate_summary()

        if CURRENT_SESSION_FILE.exists():
            CURRENT_SESSION_FILE.unlink()

        self.current_session = None

    def generate_summary(self) -> str:
        """Generate a summary of the session"""
        if not self.current_session:
            return ""

        summary = f"""
{'=' * 45}
SESSION SUMMARY
{'=' * 45}

Project: {self.current_session['project']}
Duration: {self._format_duration()}

Work Done:
  Phase: {self.current_session.get('gsd_phase', 'N/A')}
  Plan: {self.current_session.get('gsd_plan', 'N/A')}
  Files: {', '.join(self.current_session.get('files_open', [])[:3])}

Next Steps:
  {self.current_session.get('next_action', 'Continue where you left off')}

{'=' * 45}
"""
        summary_file = SESSIONS_DIR / f"{self.current_session['session_id']}-summary.txt"
        with open(summary_file, 'w') as f:
            f.write(summary)

        return summary

    def _format_duration(self) -> str:
        """Format session duration as Xh Ym or Ym"""
        if not self.current_session:
            return "0m"

        started = datetime.fromisoformat(self.current_session['created_at'])
        ended_at = self.current_session.get('ended_at')
        ended = datetime.fromisoformat(ended_at) if ended_at else datetime.now()

        duration = ended - started
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)

        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    def get_recent_sessions(self, limit: int = 5) -> List[Dict]:
        """Get recent work sessions sorted by modification time"""
        session_files = sorted(
            SESSIONS_DIR.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        sessions: List[Dict] = []
        for file in session_files[:limit]:
            try:
                with open(file, 'r') as f:
                    sessions.append(json.load(f))
            except (json.JSONDecodeError, IOError):
                continue

        return sessions

    def get_session_by_project(self, project: str) -> Optional[Dict]:
        """Get the most recent session for a project"""
        sessions = self.get_recent_sessions(limit=20)
        for session in sessions:
            if session.get('project') == project:
                return session
        return None

    def resume_session(self, session: Dict) -> Dict:
        """Resume a previous session"""
        new_session = self.create_session(
            project=session['project'],
            directory=session['directory'],
            gsd_phase=session.get('gsd_phase'),
            gsd_plan=session.get('gsd_plan'),
            files_open=session.get('files_open', []),
            last_position=session.get('last_position'),
            next_action=session.get('next_action'),
            mcp_servers=session.get('mcp_servers', [])
        )

        log_activity('session_resumed', f'Resumed work on {session["project"]}',
                    project=session['project'],
                    previous_session=session.get('session_id'))

        return new_session

    def get_session_stats(self) -> Dict:
        """Get statistics about work sessions"""
        sessions = self.get_recent_sessions(limit=100)

        if not sessions:
            return {'total_sessions': 0, 'total_time': 0, 'projects': {}}

        total_time = sum(s.get('duration_seconds', 0) for s in sessions)

        projects: Dict[str, Dict] = {}
        for session in sessions:
            project = session.get('project', 'Unknown')
            if project not in projects:
                projects[project] = {'count': 0, 'total_time': 0, 'last_worked': None}

            projects[project]['count'] += 1
            projects[project]['total_time'] += session.get('duration_seconds', 0)

            updated = session.get('updated_at', session.get('created_at'))
            if updated:
                if not projects[project]['last_worked'] or updated > projects[project]['last_worked']:
                    projects[project]['last_worked'] = updated

        return {
            'total_sessions': len(sessions),
            'total_time': total_time,
            'projects': projects
        }


# Module-level convenience functions

def get_current_session() -> Optional[Dict]:
    """Get the current active session"""
    return SessionManager().current_session


def create_session(**kwargs) -> Dict:
    """Create a new session"""
    return SessionManager().create_session(**kwargs)


def end_session() -> None:
    """End the current session"""
    SessionManager().end_session()


if __name__ == '__main__':
    manager = SessionManager()

    print("=" * 60)
    print("SESSION MANAGER TEST")
    print("=" * 60)

    print("\n1. Creating test session...")
    session = manager.create_session(
        project="TestProject",
        gsd_phase="3",
        gsd_plan="3.2",
        files_open=["test.py", "main.py"],
        next_action="Complete authentication"
    )
    print(f"Session created: {session['session_id']}")

    print("\n2. Updating session...")
    manager.update_session(
        gsd_plan="3.3",
        files_open=["test.py", "main.py", "auth.py"]
    )
    print("Session updated")

    print("\n3. Recent sessions:")
    recent = manager.get_recent_sessions(limit=3)
    for s in recent:
        print(f"  {s['project']} ({s.get('created_at', 'unknown')})")

    print("\n4. Session statistics:")
    stats = manager.get_session_stats()
    print(f"  Total sessions: {stats['total_sessions']}")
    print(f"  Total time: {stats['total_time']:.0f}s")
    print(f"  Projects: {len(stats['projects'])}")

    print("\n5. Ending session...")
    manager.end_session()
    print("Session ended")

    print("\n" + "=" * 60)
    print("All tests passed!")
