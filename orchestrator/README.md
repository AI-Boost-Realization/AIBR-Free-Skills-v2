# Orchestrator System

A Python-based orchestration layer that runs as a background daemon alongside Claude Code. It monitors your environment, routes requests to the right Claude model, tracks token costs, detects repetitive loops, and can auto-generate skills from repeated command patterns.

All of this is real running Python code. None of it is a prompt file.

## Components

### master-orchestrator.py

The main daemon. Start it with `python master-orchestrator.py` and leave it running in a background terminal.

It runs three async loops:

**Directory monitor** — polls `cwd` every 2 seconds. When you switch directories it calls `SkillExecutor.detect_context()` to determine project type and auto-executes relevant skills. It also runs `MCPManager.auto_configure()` to add or remove MCP servers based on what the project needs (e.g., `github-official` when a `.git` dir is present).

**Command history monitor** — watches `~/.claude/logs/session-history.log` for new lines. Each new command is passed to `PatternDetector`. When it sees the same 3-command sequence repeat 3+ times it auto-generates a skill file in `~/.claude/commands/`.

**Periodic optimization** — runs hourly, logs a heartbeat, rotates the log file if it exceeds 50KB.

The `SkillExecutor.project_map` dict maps directory name fragments to project identifiers. Customize it to match your own project layout.

### model-router.py

Keyword and pattern matching that selects haiku / sonnet / opus for a given request string.

Scoring works in layers:
1. Keyword match (+1 per keyword hit, three separate keyword lists)
2. Regex pattern match (+3 per match, weighted higher than keywords)
3. Context analysis — file count, lines of code, step count, and a `critical` flag each add points
4. Request word count — short requests lean haiku, long ones lean sonnet/opus
5. Tie-break defaults to sonnet

Each routing decision is appended to `~/.claude/logs/model-routing.jsonl` for later analysis.

CLI usage:
```bash
python model-router.py "create a new authentication system"
python model-router.py stats
python model-router.py recommend
```

Import usage:
```python
from model_router import route_request
model, info = route_request("fix the type error in auth.ts")
# model: 'sonnet'
# info: {reasoning, estimated_cost, scores, timestamp}
```

### session_manager.py

Session lifecycle management with auto-save and resume.

Creates JSON files under `~/.claude/.work-sessions/` — one per session. The current session is also written to `~/.claude/.current-work-session.json` for quick reads.

Sessions can carry: project name, directory, GSD phase/plan, open files, last cursor position, next action, and active MCP servers. When you resume a prior session it creates a new session pre-populated with the previous session's state.

```python
from session_manager import SessionManager

manager = SessionManager()
session = manager.create_session(
    project="my-api",
    next_action="Implement rate limiting middleware"
)
manager.update_session(files_open=["src/middleware/rate-limit.ts"])
manager.end_session()  # saves summary to .work-sessions/{id}-summary.txt
```

### token-tracker.py

Tracks token counts and estimated cost per model. Persists to `~/.claude/.token-stats.json`.

```python
from token_tracker import TokenTracker

tracker = TokenTracker()
tracker.record_usage('sonnet', input_tokens=2000, output_tokens=800)
stats = tracker.get_current_stats()
# {'currentModel': 'sonnet', 'tokensUsed': 2800, 'estimatedCost': 0.018, 'breakdown': {...}}
```

Pricing is defined in the `PRICING` dict at the top of the file. Update it when Anthropic changes pricing.

### activity-logger.py

Rolling activity log — keeps the last 50 entries in `~/.claude/.recent-activity.json`. Used by the orchestrator to feed an activity feed to the dashboard.

```python
from activity_logger import log as log_activity

log_activity('skill_executed', 'Auto-ran /deploy', skill='deploy', project='my-api')
```

The `log()` convenience function instantiates `ActivityLogger`, appends the entry, trims to 50 items, and saves — all in one call.

### gsd-ralph-detector.py

Detects two patterns from project context and user message text:

**GSD detection** — checks whether `cwd/.planning/` exists and contains `STATE.md`, `ROADMAP.md`, and `PROJECT.md`. Also checks user message text for keywords like "what's next", "progress", "roadmap".

**Ralph loop detection** — checks user message for iterative keywords ("until", "all tests pass", "fix bugs", etc.) and looks for test files in the project. When detected it estimates an appropriate `max_iterations` based on task complexity indicators in the message.

The "Ralph Wiggum" name refers to the Simpsons character who repeats the same action without checking the result. The detector flags when Claude is about to enter a potentially uncontrolled loop and suggests a bounded alternative (`/ralph-loop ... --max-iterations N --completion-promise "..."`) so the loop has an explicit exit condition.

```python
from gsd_ralph_detector import detect_workflow

result = detect_workflow(user_message="Fix all lint errors until the build passes")
if result['use_ralph']:
    print(result['suggestion'])
    # /ralph-loop "[task]" --max-iterations 10 --completion-promise "[done condition]"
```

### progress-tracker.py

Terminal progress indicators. Three tracker classes:

- `ProgressTracker` — generic `[=====>    ] 60%` bar with ETA
- `RalphProgressTracker` — multi-line display showing current iteration, errors remaining, and ETA, designed for the bounded loop pattern
- `PlanProgress` — step-by-step plan display with color-coded status icons (pending / in_progress / complete / failed) and per-step timing

Run `python progress-tracker.py` to see all three demos.

## Installation

```bash
pip install watchdog
```

The watchdog package is required for filesystem monitoring. Everything else is stdlib.

## Running as a background process

```bash
# Start in background, log to file
nohup python ~/.claude/orchestrator/master-orchestrator.py \
  >> ~/.claude/logs/orchestrator.log 2>&1 &

# Or via a launchd plist on macOS (add to ~/Library/LaunchAgents/)
# See your OS service manager docs for systemd on Linux
```

The orchestrator writes its own logs to `~/.claude/logs/orchestrator.log` and rotates them at 50KB.

## Customizing project detection

In `master-orchestrator.py`, edit `SkillExecutor.project_map`:

```python
self.project_map: Dict[str, str] = {
    'my-web-app': 'web-app',
    'my-api': 'api',
    'my-ml-pipeline': 'ml',
}
```

The key is a substring matched against the full path of the current directory. The value is the project identifier used in activity logs and skill triggers.

## File layout

```
~/.claude/
  orchestrator/
    master-orchestrator.py
    model-router.py
    session_manager.py
    token-tracker.py
    activity-logger.py
    gsd-ralph-detector.py
    progress-tracker.py
  logs/
    orchestrator.log
    model-routing.jsonl
    auto-execution.log
    session-history.log
  .recent-activity.json
  .token-stats.json
  .current-work-session.json
  .work-sessions/
    {timestamp}.json
    {timestamp}-summary.txt
```
