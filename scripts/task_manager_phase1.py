#!/usr/bin/env python3
"""
Enhanced Proactive Task Manager - Phase 1 Features
Adds: Progress tracking, recurring tasks, actual time tracking, blocked reasons
"""

import json
import argparse
import sys
import shutil
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any
import uuid

# Data file location
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
DATA_FILE = DATA_DIR / "tasks.json"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

def load_data() -> Dict[str, Any]:
    """Load tasks data from JSON file."""
    try:
        if not DATA_FILE.exists():
            return {"goals": [], "tasks": []}
        
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            # Validate schema
            if not isinstance(data, dict) or "tasks" not in data:
                print("⚠️ tasks.json schema invalid, recovering to empty state", file=sys.stderr)
                return {"goals": [], "tasks": []}
            return data
    except json.JSONDecodeError as e:
        print(f"⚠️ tasks.json corrupted: {e}. Using empty state. Backup at tasks.json.bak", file=sys.stderr)
        # Try to create backup
        if DATA_FILE.exists():
            import shutil
            try:
                shutil.copy(DATA_FILE, DATA_FILE.parent / "tasks.json.bak")
            except Exception:
                pass
        return {"goals": [], "tasks": []}
    except IOError as e:
        print(f"⚠️ Error reading tasks.json: {e}", file=sys.stderr)
        return {"goals": [], "tasks": []}

def save_data(data: Dict[str, Any]) -> None:
    """Save tasks data to JSON file."""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def generate_id(prefix: str) -> str:
    """Generate a unique ID."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

def find_task_by_id(data: Dict[str, Any], task_id: str) -> Optional[Dict]:
    """Find a task by ID."""
    for task in data["tasks"]:
        if task["id"] == task_id:
            return task
    return None

def mark_progress(args) -> None:
    """Update task progress (0-100%)."""
    data = load_data()
    
    task = find_task_by_id(data, args.task_id)
    if not task:
        print(json.dumps({"success": False, "error": f"Task not found: {args.task_id}"}), file=sys.stderr)
        sys.exit(1)
    
    progress = int(args.progress)
    if not 0 <= progress <= 100:
        print(json.dumps({"success": False, "error": "Progress must be 0-100"}), file=sys.stderr)
        sys.exit(1)
    
    task["progress"] = progress
    task["updated_at"] = datetime.now(timezone.utc).isoformat() + "Z"
    
    if progress == 100 and task["status"] == "in_progress":
        task["status"] = "completed"
        task["completed_at"] = datetime.now(timezone.utc).isoformat() + "Z"
    elif progress > 0 and task["status"] == "pending":
        task["status"] = "in_progress"
    
    save_data(data)
    
    print(json.dumps({"success": True, "task": task}, indent=2))

def mark_blocked(args) -> None:
    """Mark a task as blocked with a reason."""
    data = load_data()
    
    task = find_task_by_id(data, args.task_id)
    if not task:
        print(json.dumps({"success": False, "error": f"Task not found: {args.task_id}"}), file=sys.stderr)
        sys.exit(1)
    
    task["status"] = "blocked"
    task["blocked_reason"] = args.reason
    task["updated_at"] = datetime.now(timezone.utc).isoformat() + "Z"
    
    save_data(data)
    
    print(json.dumps({"success": True, "task": task}, indent=2))

def unblock_task(args) -> None:
    """Unblock a task and set it back to pending."""
    data = load_data()
    
    task = find_task_by_id(data, args.task_id)
    if not task:
        print(json.dumps({"success": False, "error": f"Task not found: {args.task_id}"}), file=sys.stderr)
        sys.exit(1)
    
    task["status"] = "pending"
    task["blocked_reason"] = None
    task["updated_at"] = datetime.now(timezone.utc).isoformat() + "Z"
    
    save_data(data)
    
    print(json.dumps({"success": True, "task": task}, indent=2))

def log_time(args) -> None:
    """Log actual time spent on a task."""
    data = load_data()
    
    task = find_task_by_id(data, args.task_id)
    if not task:
        print(json.dumps({"success": False, "error": f"Task not found: {args.task_id}"}), file=sys.stderr)
        sys.exit(1)
    
    minutes = int(args.minutes)
    if "actual_minutes" not in task:
        task["actual_minutes"] = 0
    
    task["actual_minutes"] += minutes
    task["updated_at"] = datetime.now(timezone.utc).isoformat() + "Z"
    
    # Calculate variance
    if "estimate_minutes" in task:
        estimated = task["estimate_minutes"]
        actual = task["actual_minutes"]
        variance = ((actual - estimated) / estimated) * 100 if estimated > 0 else 0
        task["time_variance_percent"] = round(variance, 1)
    
    save_data(data)
    
    output = {
        "success": True,
        "task": task,
        "logged": f"{minutes} minutes",
        "total_actual": task["actual_minutes"]
    }
    
    if "time_variance_percent" in task:
        output["variance"] = f"{task['time_variance_percent']}% vs estimate"
    
    print(json.dumps(output, indent=2))

def create_recurring(args) -> None:
    """Create a recurring task (daily, weekly, etc)."""
    data = load_data()
    
    goal = next((g for g in data["goals"] if g["id"] == args.goal_id), None)
    if not goal:
        print(json.dumps({"success": False, "error": f"Goal not found: {args.goal_id}"}), file=sys.stderr)
        sys.exit(1)
    
    task = {
        "id": generate_id("task"),
        "goal_id": args.goal_id,
        "title": args.title,
        "priority": args.priority or "medium",
        "status": "pending",
        "progress": 0,
        "recurring": args.recurring,  # daily, weekly, monthly, after_completion
        "next_due_at": datetime.now(timezone.utc).isoformat() + "Z",
        "created_at": datetime.now(timezone.utc).isoformat() + "Z",
        "notes": ""
    }
    
    if args.estimate:
        task["estimate_minutes"] = int(args.estimate)
    
    data["tasks"].append(task)
    save_data(data)
    
    print(json.dumps({"success": True, "task": task}, indent=2))

def next_recurring(args) -> None:
    """Process recurring tasks and create next occurrence."""
    data = load_data()
    
    task = find_task_by_id(data, args.task_id)
    if not task:
        print(json.dumps({"success": False, "error": f"Task not found: {args.task_id}"}), file=sys.stderr)
        sys.exit(1)
    
    if task.get("recurring") == "none" or "recurring" not in task:
        print(json.dumps({"success": False, "error": "Task is not recurring"}), file=sys.stderr)
        sys.exit(1)
    
    # Only complete if progress is 100%
    if task.get("progress", 0) < 100:
        print(json.dumps({
            "success": False,
            "error": f"Task must be 100% complete before creating next occurrence (current: {task.get('progress', 0)}%)"
        }), file=sys.stderr)
        sys.exit(1)
    
    # Mark current as completed
    task["status"] = "completed"
    task["completed_at"] = datetime.now(timezone.utc).isoformat() + "Z"
    task["progress"] = 100
    
    # Create next occurrence
    next_task = task.copy()
    next_task["id"] = generate_id("task")
    next_task["status"] = "pending"
    next_task["progress"] = 0
    next_task["created_at"] = datetime.now(timezone.utc).isoformat() + "Z"
    next_task["actual_minutes"] = 0
    
    # Calculate next due date
    now = datetime.now(timezone.utc)
    if task["recurring"] == "daily":
        next_due = now + timedelta(days=1)
    elif task["recurring"] == "weekly":
        next_due = now + timedelta(weeks=1)
    elif task["recurring"] == "monthly":
        next_due = now + timedelta(days=30)
    else:
        next_due = now
    
    next_task["next_due_at"] = next_due.isoformat() + "Z"
    
    # Clear completed fields
    for key in ["completed_at", "last_error", "retry_count", "blocked_reason"]:
        next_task.pop(key, None)
    
    data["tasks"].append(next_task)
    save_data(data)
    
    print(json.dumps({
        "success": True,
        "completed": task,
        "next": next_task
    }, indent=2))

def show_velocity(args) -> None:
    """Show task completion velocity."""
    data = load_data()
    
    goal = next((g for g in data["goals"] if g["id"] == args.goal_id), None)
    if not goal:
        print(json.dumps({"success": False, "error": f"Goal not found: {args.goal_id}"}), file=sys.stderr)
        sys.exit(1)
    
    # Get completed tasks for this goal
    completed = [t for t in data["tasks"] 
                 if t["goal_id"] == args.goal_id and t["status"] == "completed"]
    
    # Count by day
    from collections import defaultdict
    by_day = defaultdict(int)
    
    for task in completed:
        if "completed_at" in task:
            completed_date = task["completed_at"].split("T")[0]
            by_day[completed_date] += 1
    
    # Get remaining tasks
    remaining = [t for t in data["tasks"]
                 if t["goal_id"] == args.goal_id and t["status"] != "completed"]
    
    # Calculate average velocity
    velocity = len(completed) / len(by_day) if by_day else 0
    days_to_completion = len(remaining) / velocity if velocity > 0 else 0
    
    print(json.dumps({
        "success": True,
        "goal_id": args.goal_id,
        "completed": len(completed),
        "remaining": len(remaining),
        "days_tracked": len(by_day),
        "velocity_tasks_per_day": round(velocity, 2),
        "estimated_days_to_completion": round(days_to_completion, 1),
        "completions_by_day": dict(sorted(by_day.items()))
    }, indent=2))

# CLI Setup
parser = argparse.ArgumentParser(description="Enhanced Proactive Task Manager - Phase 1")
subparsers = parser.add_subparsers(dest="command", help="Command to execute")

# Mark progress
prog_parser = subparsers.add_parser("mark-progress", help="Update task progress (0-100%)")
prog_parser.add_argument("task_id", help="Task ID")
prog_parser.add_argument("progress", help="Progress percentage (0-100)")

# Mark blocked
blocked_parser = subparsers.add_parser("mark-blocked", help="Mark task as blocked")
blocked_parser.add_argument("task_id", help="Task ID")
blocked_parser.add_argument("reason", help="Why is it blocked?")

# Unblock
unblock_parser = subparsers.add_parser("unblock-task", help="Unblock a task")
unblock_parser.add_argument("task_id", help="Task ID")

# Log time
time_parser = subparsers.add_parser("log-time", help="Log actual time spent")
time_parser.add_argument("task_id", help="Task ID")
time_parser.add_argument("minutes", help="Minutes spent")

# Create recurring
recurring_parser = subparsers.add_parser("create-recurring", help="Create a recurring task")
recurring_parser.add_argument("goal_id", help="Goal ID")
recurring_parser.add_argument("title", help="Task title")
recurring_parser.add_argument("--recurring", choices=["daily", "weekly", "monthly", "after_completion"], 
                              default="weekly", help="Recurrence pattern")
recurring_parser.add_argument("--priority", choices=["low", "medium", "high"], help="Priority")
recurring_parser.add_argument("--estimate", help="Estimated minutes")

# Next recurring
next_rec_parser = subparsers.add_parser("next-recurring", help="Complete and create next occurrence")
next_rec_parser.add_argument("task_id", help="Task ID")

# Velocity
vel_parser = subparsers.add_parser("show-velocity", help="Show completion velocity")
vel_parser.add_argument("goal_id", help="Goal ID")

args = parser.parse_args()

if args.command == "mark-progress":
    mark_progress(args)
elif args.command == "mark-blocked":
    mark_blocked(args)
elif args.command == "unblock-task":
    unblock_task(args)
elif args.command == "log-time":
    log_time(args)
elif args.command == "create-recurring":
    create_recurring(args)
elif args.command == "next-recurring":
    next_recurring(args)
elif args.command == "show-velocity":
    show_velocity(args)
else:
    parser.print_help()
