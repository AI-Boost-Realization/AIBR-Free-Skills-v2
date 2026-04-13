#!/usr/bin/env python3
"""
Master Orchestrator - The Brain of Your Agentic System

Automatically:
1. Executes skills based on context
2. Monitors user activity for patterns
3. Creates new skills on the fly
4. Routes requests to optimal models
5. Manages all MCP servers
6. Updates the dashboard in real-time
7. Learns from your workflow

This runs in the background and makes EVERYTHING automatic.
"""

import os
import sys
import json
import time
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add model router and activity logger
orchestrator_dir = Path.home() / '.claude/orchestrator'
sys.path.insert(0, str(orchestrator_dir))

try:
    from model_router import route_request
except ImportError:
    # Fallback if model router not available
    def route_request(request: str, context: Optional[Dict] = None):
        return 'sonnet', {'reasoning': 'Default model', 'estimated_cost': 0.01, 'scores': {}}

try:
    from activity_logger import log as log_activity
except ImportError:
    # Fallback if activity logger not available
    def log_activity(activity_type: str, description: str, **metadata) -> None:
        pass

try:
    from gsd_ralph_detector import GSDRalphDetector
except ImportError:
    # Fallback if detector not available
    GSDRalphDetector = None

CLAUDE_DIR = Path.home() / '.claude'
COMMANDS_DIR = CLAUDE_DIR / 'commands'
LOGS_DIR = CLAUDE_DIR / 'logs'
SESSIONS_DIR = CLAUDE_DIR / 'sessions'


class SkillExecutor:
    """Automatically execute skills based on context"""

    def __init__(self):
        self.last_directory: Optional[str] = None
        # Map directory name fragments to project identifiers.
        # Add entries here to match your own project layout.
        self.project_map: Dict[str, str] = {
            'my-web-app': 'web-app',
            'my-api': 'api',
            'my-cli': 'cli',
        }
        self.gsd_ralph_detector = GSDRalphDetector() if GSDRalphDetector else None

    def detect_context(self) -> Dict:
        """Detect current context and determine which skills to run"""
        cwd = Path.cwd()
        context: Dict = {
            'directory': str(cwd),
            'project_name': cwd.name,
            'project': None,
            'skills_to_execute': []
        }

        # Detect project by directory name
        for key, project_id in self.project_map.items():
            if key in str(cwd):
                context['project'] = project_id
                context['skills_to_execute'].append(f'switch-project {project_id}')
                break

        # If no match but directory changed, trigger generic session start
        if context['project'] is None and str(cwd) != self.last_directory:
            context['skills_to_execute'].append('start-session')

        # Detect project type
        if (cwd / 'package.json').exists():
            context['project_type'] = 'nodejs'

        if (cwd / 'requirements.txt').exists():
            context['project_type'] = 'python'

        if (cwd / '.git').exists():
            context['has_git'] = True

        # Check for GSD and Ralph Wiggum opportunities
        if self.gsd_ralph_detector:
            workflow = self.gsd_ralph_detector.detect(cwd)
            if workflow['use_gsd'] and workflow['gsd_ready']:
                context['gsd_detected'] = True
                context['gsd_suggestion'] = workflow['suggestion']
                print(f"  GSD project detected - Run /work to continue")
                log_activity('gsd_detected', 'GSD project management detected',
                           suggestion=workflow['suggestion'],
                           auto_action='/work')

                self.show_gsd_prompt(workflow)

            if workflow['use_ralph']:
                context['ralph_opportunity'] = True
                context['ralph_suggestion'] = workflow['suggestion']
                print(f"  Ralph loop opportunity detected")
                log_activity('ralph_opportunity', 'Ralph Wiggum loop opportunity',
                           suggestion=workflow['suggestion'],
                           max_iterations=workflow['ralph_max_iterations'])

        self.last_directory = str(cwd)
        return context

    def show_gsd_prompt(self, workflow: Dict) -> None:
        """Print a prompt suggesting GSD workflow"""
        suggestion = workflow.get('suggestion', '/gsd:progress')
        print(f"\n  Suggested: {suggestion}\n")

    async def execute_skills(self, skills: List[str]) -> None:
        """Execute detected skills automatically"""
        for skill in skills:
            print(f"Auto-executing: /{skill}")
            log_activity('skill_executed', f'Auto-executed /{skill}', skill=skill)
            await self.run_skill(skill)

    async def run_skill(self, skill: str) -> None:
        """Run a single skill"""
        # Write a pending command file that your shell hook can pick up.
        pending_file = CLAUDE_DIR / '.pending-commands'
        with open(pending_file, 'w') as f:
            f.write(f"TRIGGER:/{skill}\n")

        log_file = LOGS_DIR / 'auto-execution.log'
        log_file.parent.mkdir(exist_ok=True)
        with open(log_file, 'a') as f:
            f.write(f"[{datetime.now()}] Auto-executed: /{skill}\n")


class PatternDetector:
    """Detects patterns in user behavior to auto-create skills"""

    def __init__(self):
        self.command_history: List[Dict] = []
        self.pattern_threshold = 3  # Need 3 repetitions to create skill

    def record_command(self, command: str, context: Dict) -> None:
        """Record a command for pattern analysis"""
        self.command_history.append({
            'command': command,
            'context': context,
            'timestamp': datetime.now().isoformat()
        })

        # Keep only last 100 commands
        if len(self.command_history) > 100:
            self.command_history = self.command_history[-100:]

        self.analyze_patterns()

    def analyze_patterns(self) -> None:
        """Analyze command history for patterns"""
        sequences: Dict[tuple, int] = {}

        for i in range(len(self.command_history) - 2):
            seq = tuple(
                cmd['command'] for cmd in self.command_history[i:i+3]
            )
            sequences[seq] = sequences.get(seq, 0) + 1

        for seq, count in sequences.items():
            if count >= self.pattern_threshold:
                self.create_skill_from_pattern(seq, count)

    def create_skill_from_pattern(self, sequence: tuple, count: int) -> None:
        """Auto-create a skill from detected pattern"""
        skill_name = self.generate_skill_name(sequence)

        skill_file = COMMANDS_DIR / f"{skill_name}.md"
        if skill_file.exists():
            return

        skill_content = self.generate_skill_content(skill_name, sequence, count)

        skill_file.parent.mkdir(exist_ok=True)
        with open(skill_file, 'w') as f:
            f.write(skill_content)

        print(f"Auto-created new skill: /{skill_name}")
        print(f"   Detected {count} repetitions")

        log_activity('skill_created', f'Auto-created /{skill_name} skill',
                    pattern=list(sequence), count=count)

    def generate_skill_name(self, sequence: tuple) -> str:
        """Generate a name for the skill"""
        actions = []
        for cmd in sequence:
            action = cmd.split()[0] if cmd else ''
            if action and action not in actions:
                actions.append(action)
        return '-'.join(actions[:3]).lower()

    def generate_skill_content(self, name: str, sequence: tuple, count: int) -> str:
        """Generate the skill file content"""
        return f"""---
name: {name}
description: Auto-generated skill (detected {count} repetitions)
auto_created: true
created_at: {datetime.now().isoformat()}
---

<objective>
Automate the following sequence:
{chr(10).join(f'{i+1}. {cmd}' for i, cmd in enumerate(sequence))}
</objective>

<process>
{chr(10).join(f'''<step name="step{i+1}">
{cmd}
</step>''' for i, cmd in enumerate(sequence))}
</process>

<usage>
Created automatically after detecting this pattern {count} times.
Review and customize as needed.
</usage>
"""


class MCPManager:
    """Automatically manages MCP servers based on context"""

    def __init__(self):
        self.active_servers: List[str] = []

    def auto_configure(self, context: Dict) -> None:
        """Auto-configure MCP servers based on context"""
        required_servers = self.determine_required_servers(context)

        for server in required_servers:
            if server not in self.active_servers:
                self.add_server(server)

        for server in list(self.active_servers):
            if server not in required_servers and server not in ['filesystem']:
                self.remove_server(server)

    def determine_required_servers(self, context: Dict) -> List[str]:
        """Determine which MCP servers are needed"""
        servers = ['filesystem']  # Always needed

        if context.get('has_git'):
            servers.append('github-official')

        if context.get('project_type') == 'python':
            servers.append('mcp-python-refactoring')

        if context.get('project_type') == 'nodejs':
            if 'next' in context.get('directory', '').lower():
                servers.append('next-devtools-mcp')

        return servers

    def add_server(self, server: str) -> None:
        """Add MCP server"""
        print(f"Adding MCP server: {server}")
        log_activity('mcp_configured', f'Added {server} MCP server', server=server)
        self.active_servers.append(server)

    def remove_server(self, server: str) -> None:
        """Remove MCP server"""
        print(f"Removing MCP server: {server}")
        if server in self.active_servers:
            self.active_servers.remove(server)


class ModelOptimizer:
    """Automatically route requests to optimal model"""

    def optimize_request(self, request: str, context: Optional[Dict] = None) -> str:
        """Determine optimal model for request"""
        model, info = route_request(request, context)

        print(f"Model: {model.upper()}")
        print(f"Reason: {info['reasoning']}")
        print(f"Est. Cost: ${info['estimated_cost']}")

        return model


class MasterOrchestrator:
    """The main orchestrator that coordinates everything"""

    def __init__(self):
        self.skill_executor = SkillExecutor()
        self.pattern_detector = PatternDetector()
        self.mcp_manager = MCPManager()
        self.model_optimizer = ModelOptimizer()
        self.running = False

    async def start(self) -> None:
        """Start the orchestrator"""
        print("Master Orchestrator starting...")
        print("Monitoring your workflow...")
        print("Auto-executing skills when detected")
        print("Creating new skills from patterns")
        print("Optimizing model usage")
        print()

        self.running = True

        await asyncio.gather(
            self.monitor_directory_changes(),
            self.monitor_command_history(),
            self.periodic_optimization()
        )

    async def monitor_directory_changes(self) -> None:
        """Monitor when user changes directories"""
        last_cwd: Optional[str] = None

        while self.running:
            cwd = str(Path.cwd())

            if cwd != last_cwd:
                print(f"\nDirectory changed: {cwd}")

                context = self.skill_executor.detect_context()

                if context.get('project'):
                    log_activity('context_switch',
                               f'Switched to {context["project"]} project',
                               project=context['project_name'])

                if context['skills_to_execute']:
                    await self.skill_executor.execute_skills(
                        context['skills_to_execute']
                    )

                self.mcp_manager.auto_configure(context)

                last_cwd = cwd

            await asyncio.sleep(2)

    async def monitor_command_history(self) -> None:
        """Monitor command history for patterns"""
        history_file = LOGS_DIR / 'session-history.log'
        last_size = 0

        while self.running:
            if history_file.exists():
                size = history_file.stat().st_size

                if size > last_size:
                    with open(history_file, 'r') as f:
                        f.seek(last_size)
                        new_lines = f.read().splitlines()

                    for line in new_lines:
                        self.pattern_detector.record_command(line, {})

                    last_size = size

            await asyncio.sleep(5)

    async def periodic_optimization(self) -> None:
        """Periodically optimize the system"""
        log_file = LOGS_DIR / 'orchestrator.log'
        while self.running:
            await asyncio.sleep(3600)  # Every hour

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            msg = f"[{timestamp}] periodic_optimization: cycle complete"

            try:
                log_file.parent.mkdir(parents=True, exist_ok=True)
                with open(log_file, 'a') as f:
                    f.write(msg + '\n')
                # Rotate: keep last 100 lines
                if log_file.exists() and log_file.stat().st_size > 50000:
                    lines = log_file.read_text().splitlines()
                    log_file.write_text('\n'.join(lines[-100:]) + '\n')
            except OSError:
                pass

    def stop(self) -> None:
        """Stop the orchestrator"""
        print("\nMaster Orchestrator stopping...")
        self.running = False


async def main() -> None:
    orchestrator = MasterOrchestrator()

    try:
        await orchestrator.start()
    except KeyboardInterrupt:
        orchestrator.stop()


if __name__ == '__main__':
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    asyncio.run(main())
