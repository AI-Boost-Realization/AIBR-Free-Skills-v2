#!/usr/bin/env python3
"""
Progress Tracker - Visual progress indicators for terminal
Shows real-time progress during long-running tasks
"""
import sys
import time
from typing import Optional


class ProgressTracker:
    """Terminal progress indicators for generic multi-step tasks"""

    def __init__(self, total_steps: int, task_name: str = "Progress"):
        self.total_steps = total_steps
        self.current_step = 0
        self.task_name = task_name
        self.start_time = time.time()
        self.step_times: list[float] = []

    def update(self, step: int, status: str = "") -> None:
        """Update progress to a specific step"""
        self.current_step = step
        self.step_times.append(time.time())
        self._render(status)

    def increment(self, status: str = "") -> None:
        """Increment progress by one step"""
        self.current_step += 1
        self.step_times.append(time.time())
        self._render(status)

    def complete(self, final_message: str = "Complete!") -> None:
        """Mark as complete"""
        self.current_step = self.total_steps
        self._render(final_message)
        print()

    def _render(self, status: str = "") -> None:
        """Render progress bar to terminal"""
        percent = (self.current_step / self.total_steps) * 100
        bar_length = 30
        filled = int((self.current_step / self.total_steps) * bar_length)
        bar = "=" * filled + ">" + " " * (bar_length - filled - 1)
        eta_str = self._calculate_eta()

        sys.stdout.write('\r')
        sys.stdout.write(f"{self.task_name}: [{bar}] {percent:.0f}% {status} {eta_str}")
        sys.stdout.flush()

    def _calculate_eta(self) -> str:
        """Calculate estimated time remaining"""
        if self.current_step == 0:
            return ""

        elapsed = time.time() - self.start_time
        avg_time_per_step = elapsed / self.current_step
        remaining_steps = self.total_steps - self.current_step

        if remaining_steps <= 0:
            return ""

        eta_seconds = avg_time_per_step * remaining_steps

        if eta_seconds < 60:
            return f"(~{eta_seconds:.0f}s)"
        elif eta_seconds < 3600:
            return f"(~{eta_seconds/60:.0f}m)"
        else:
            return f"(~{eta_seconds/3600:.1f}h)"


class RalphProgressTracker:
    """
    Progress tracker for iterative fix-until-done loops.

    Named after the Ralph Wiggum pattern — where Claude keeps iterating
    on a task (e.g., fixing type errors, reducing lint violations) until
    a completion condition is satisfied. This tracker visualizes how many
    iterations have run and how many error indicators remain.
    """

    def __init__(self, max_iterations: int, task_description: str):
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.task_description = task_description
        self.start_time = time.time()
        self.errors_remaining: Optional[int] = None
        self.last_status = ""

    def update(self, iteration: int, status: str = "", errors: Optional[int] = None) -> None:
        """Update iteration progress"""
        self.current_iteration = iteration
        self.last_status = status
        if errors is not None:
            self.errors_remaining = errors
        self._render()

    def _render(self) -> None:
        """Render Ralph loop progress"""
        percent = (self.current_iteration / self.max_iterations) * 100
        bar_length = 20
        filled = int((self.current_iteration / self.max_iterations) * bar_length)
        bar = "=" * filled + ">" + " " * (bar_length - filled - 1)

        if self.current_iteration > 0:
            elapsed = time.time() - self.start_time
            avg_time = elapsed / self.current_iteration
            remaining = (self.max_iterations - self.current_iteration) * avg_time
            eta = f"ETA: ~{remaining/60:.0f}m" if remaining > 60 else f"ETA: ~{remaining:.0f}s"
        else:
            eta = ""

        error_str = f"| {self.errors_remaining} errors remaining" if self.errors_remaining is not None else ""

        sys.stdout.write('\r\033[K')
        print(f"\n{'=' * 60}")
        print(f"Iterating: {self.task_description}")
        print(f"{'=' * 60}")
        print(f"[Iteration {self.current_iteration}/{self.max_iterations}] [{bar}] {percent:.0f}%")
        print(f"Status: {self.last_status} {error_str}")
        print(f"{eta}")
        print(f"{'=' * 60}")
        sys.stdout.write('\033[5A')
        sys.stdout.flush()

    def complete(self, success: bool = True) -> None:
        """Mark loop as complete"""
        sys.stdout.write('\r\033[K')
        print(f"\n{'=' * 60}")
        if success:
            print(f"Loop Complete: {self.task_description}")
            print(f"  Total iterations: {self.current_iteration}")
            elapsed = time.time() - self.start_time
            print(f"  Time elapsed: {elapsed/60:.1f}m")
        else:
            print(f"Loop Stopped: {self.task_description}")
            print(f"  Completed: {self.current_iteration}/{self.max_iterations} iterations")
        print(f"{'=' * 60}\n")


class PlanProgress:
    """Progress tracker for multi-step plan execution"""

    def __init__(self, plan_name: str, total_steps: int):
        self.plan_name = plan_name
        self.total_steps = total_steps
        self.steps: list[dict] = []
        self.current_step_index = 0

    def add_step(self, name: str, status: str = "pending") -> None:
        """Add a step to the plan"""
        self.steps.append({
            'name': name,
            'status': status,  # pending, in_progress, complete, failed
            'start_time': None,
            'end_time': None
        })

    def start_step(self, index: int) -> None:
        """Mark step as in progress"""
        if index < len(self.steps):
            self.steps[index]['status'] = 'in_progress'
            self.steps[index]['start_time'] = time.time()
            self.current_step_index = index
            self._render()

    def complete_step(self, index: int, success: bool = True) -> None:
        """Mark step as complete or failed"""
        if index < len(self.steps):
            self.steps[index]['status'] = 'complete' if success else 'failed'
            self.steps[index]['end_time'] = time.time()
            self._render()

    def _render(self) -> None:
        """Render plan progress"""
        print(f"\n{'=' * 60}")
        print(f"Executing: {self.plan_name}")
        print(f"{'=' * 60}")

        for i, step in enumerate(self.steps):
            if step['status'] == 'complete':
                icon = '[done]'
                color = '\033[92m'
            elif step['status'] == 'failed':
                icon = '[fail]'
                color = '\033[91m'
            elif step['status'] == 'in_progress':
                icon = '[runs]'
                color = '\033[93m'
            else:
                icon = '[wait]'
                color = '\033[90m'

            duration = ""
            if step['end_time'] and step['start_time']:
                elapsed = step['end_time'] - step['start_time']
                duration = f" ({elapsed:.1f}s)"

            reset = '\033[0m'
            print(f"  Step {i+1}/{self.total_steps} {color}{icon}{reset} {step['name']}{duration}")

        print(f"{'=' * 60}\n")


def demo_progress() -> None:
    """Demo the progress trackers"""
    print("Demo 1: Basic Progress")
    print("=" * 60)
    tracker = ProgressTracker(10, "Processing files")
    for i in range(1, 11):
        tracker.update(i, f"file_{i}.txt")
        time.sleep(0.2)
    tracker.complete("All files processed!")
    print("\n")

    print("Demo 2: Ralph Iteration Loop")
    print("=" * 60)
    ralph = RalphProgressTracker(15, "Fix linting errors")
    for i in range(1, 16):
        errors_left = max(0, 12 - i)
        ralph.update(i, "Running lint...", errors=errors_left)
        time.sleep(0.3)
    ralph.complete(success=True)

    print("Demo 3: Plan Execution")
    print("=" * 60)
    plan = PlanProgress("Phase 3.2 - Authentication", 5)
    plan.add_step("Create auth endpoints")
    plan.add_step("Implement JWT logic")
    plan.add_step("Add password reset")
    plan.add_step("Write tests")
    plan.add_step("Update documentation")

    for i in range(5):
        plan.start_step(i)
        time.sleep(0.5)
        plan.complete_step(i, success=True)

    print("All demos complete!")


if __name__ == '__main__':
    demo_progress()
