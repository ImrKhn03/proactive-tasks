#!/usr/bin/env python3
"""
Phase 2 Extensions for Proactive Task Manager
Adds: SESSION-STATE.md, WAL (Write-Ahead Logging), working buffer, health-check
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any

# Setup paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_FILE = DATA_DIR / "tasks.json"
WORKSPACE_ROOT = PROJECT_ROOT.parent.parent
MEMORY_DIR = WORKSPACE_ROOT / "memory"
SESSION_STATE_FILE = WORKSPACE_ROOT / "SESSION-STATE.md"
WORKING_BUFFER_FILE = MEMORY_DIR / "working-buffer.md"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
MEMORY_DIR.mkdir(exist_ok=True)


def load_data() -> Dict[str, Any]:
    """Load tasks data from JSON file."""
    if not DATA_FILE.exists():
        return {"goals": [], "tasks": []}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)


def save_data(data: Dict[str, Any]) -> None:
    """Save tasks data to JSON file."""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def find_task_by_id(data: Dict[str, Any], task_id: str) -> Optional[Dict]:
    """Find a task by ID."""
    for task in data["tasks"]:
        if task["id"] == task_id:
            return task
    return None


def find_goal_by_id(data: Dict[str, Any], goal_id: str) -> Optional[Dict]:
    """Find a goal by ID."""
    for goal in data["goals"]:
        if goal["id"] == goal_id:
            return goal
    return None


def log_to_wal(event_type: str, content: Dict[str, Any]) -> None:
    """
    Write-Ahead Logging: Log critical changes BEFORE persisting data.
    
    Ensures no data loss on context cutoff - all critical changes are recorded
    in the WAL log before response is sent to user.
    
    Args:
        event_type: Type of event (PROGRESS_CHANGE, TIME_LOG, STATUS_CHANGE, etc)
        content: Event details (task_id, old_value, new_value, timestamp)
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    wal_file = MEMORY_DIR / f"WAL-{today}.log"
    
    # Create WAL entry
    wal_entry = {
        "timestamp": timestamp,
        "event_type": event_type,
        "content": content
    }
    
    # Append to WAL log
    with open(wal_file, 'a') as f:
        f.write(json.dumps(wal_entry) + "\n")


def append_to_buffer(event_type: str, details: str) -> None:
    """
    Append to working buffer - captures all changes during "danger zone" (between compaction).
    
    Working buffer is auto-flushed to daily memory file on compaction.
    Prevents info loss when context gets truncated mid-session.
    
    Args:
        event_type: Type of update (PROGRESS, TIME_LOG, STATUS_CHANGE, etc)
        details: Human-readable description
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = f"- {event_type} ({timestamp}): {details}\n"
    
    with open(WORKING_BUFFER_FILE, 'a') as f:
        f.write(entry)


def update_session_state(task: Dict, goal: Dict, action: str = "") -> None:
    """
    Update SESSION-STATE.md with current task context.
    
    SESSION-STATE.md is the active working memory for current session.
    Updated on every task change to maintain immediate context.
    """
    progress = task.get("progress", 0)
    estimate = task.get("estimate_minutes", 0)
    actual = task.get("actual_minutes", 0)
    status = task.get("status", "pending")
    
    # Calculate velocity (actual vs estimate ratio)
    velocity = ""
    if estimate > 0:
        ratio = actual / estimate
        if ratio < 1:
            velocity = f"{int((1 - ratio) * 100)}% faster than estimate"
        elif ratio > 1:
            velocity = f"{int((ratio - 1) * 100)}% slower than estimate"
        else:
            velocity = "on pace with estimate"
    
    content = f"""# SESSION-STATE.md - Active Working Memory
Last updated: {datetime.now(timezone.utc).isoformat()}

## Current Task
- ID: {task.get("id", "unknown")}
- Title: {task.get("title", "N/A")}
- Status: {status}
- Progress: {progress}%
- Estimated: {estimate} min
- Actual logged: {actual} min {f"({velocity})" if velocity else ""}

## Goal Context
- ID: {goal.get("id", "unknown")}
- Title: {goal.get("title", "N/A")}
- Priority: {goal.get("priority", "medium")}

## Task Details
- Created: {task.get("created_at", "N/A")}
- Updated: {task.get("updated_at", "N/A")}
- Notes: {task.get("notes", "None")}

## Blockers
- {task.get("blocked_reason", "None")}

## Next Action
{action or "Continue with current task or mark as complete"}
"""
    
    with open(SESSION_STATE_FILE, 'w') as f:
        f.write(content)


def mark_progress(task_id: str, progress: int, notes: str = "") -> None:
    """Mark task progress (0-100%)."""
    data = load_data()
    task = find_task_by_id(data, task_id)
    
    if not task:
        print(json.dumps({"success": False, "error": f"Task not found: {task_id}"}), file=sys.stderr)
        sys.exit(1)
    
    old_progress = task.get("progress", 0)
    
    # WAL FIRST - log before modifying
    log_to_wal("PROGRESS_CHANGE", {
        "task_id": task_id,
        "old_progress": old_progress,
        "new_progress": progress,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    # Update task
    task["progress"] = progress
    task["updated_at"] = datetime.now(timezone.utc).isoformat() + "Z"
    if notes:
        if task.get("notes"):
            task["notes"] += "\n" + notes
        else:
            task["notes"] = notes
    
    # Auto-update status based on progress
    if progress >= 100 and task.get("status") != "completed":
        task["status"] = "in_progress"
    elif progress > 0 and task.get("status") == "pending":
        task["status"] = "in_progress"
    
    save_data(data)
    
    # Update SESSION-STATE
    goal = find_goal_by_id(data, task.get("goal_id", ""))
    if goal:
        update_session_state(task, goal, f"Progress marked: {old_progress}% → {progress}%")
    
    # Append to working buffer
    append_to_buffer("PROGRESS", f"{task_id}: {old_progress}% → {progress}%")
    
    result = {
        "success": True,
        "task": task,
        "progress_change": f"{old_progress}% → {progress}%"
    }
    print(json.dumps(result, indent=2))


def log_time(task_id: str, minutes: int, notes: str = "") -> None:
    """Log time spent on a task."""
    data = load_data()
    task = find_task_by_id(data, task_id)
    
    if not task:
        print(json.dumps({"success": False, "error": f"Task not found: {task_id}"}), file=sys.stderr)
        sys.exit(1)
    
    old_actual = task.get("actual_minutes", 0)
    new_actual = old_actual + minutes
    
    # WAL FIRST
    log_to_wal("TIME_LOG", {
        "task_id": task_id,
        "minutes_logged": minutes,
        "old_total": old_actual,
        "new_total": new_actual,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    # Update task
    task["actual_minutes"] = new_actual
    task["updated_at"] = datetime.now(timezone.utc).isoformat() + "Z"
    
    if notes:
        if task.get("notes"):
            task["notes"] += "\n" + notes
        else:
            task["notes"] = notes
    
    # Auto-update status
    if task.get("status") == "pending" and new_actual > 0:
        task["status"] = "in_progress"
    
    save_data(data)
    
    # Update SESSION-STATE
    goal = find_goal_by_id(data, task.get("goal_id", ""))
    if goal:
        update_session_state(task, goal, f"Logged {minutes} min (total: {new_actual} min)")
    
    # Append to working buffer
    append_to_buffer("TIME_LOG", f"{task_id}: +{minutes} min (total: {new_actual} min)")
    
    # Calculate velocity
    estimate = task.get("estimate_minutes", 0)
    velocity = ""
    if estimate > 0:
        ratio = new_actual / estimate
        if ratio < 1:
            velocity = f"{int((1 - ratio) * 100)}% faster than estimate"
        elif ratio > 1:
            velocity = f"{int((ratio - 1) * 100)}% slower than estimate"
    
    result = {
        "success": True,
        "task": task,
        "time_logged": minutes,
        "total_actual": new_actual,
        "estimate": estimate,
        "velocity": velocity
    }
    print(json.dumps(result, indent=2))


def mark_blocked(task_id: str, reason: str) -> None:
    """Mark task as blocked with reason."""
    data = load_data()
    task = find_task_by_id(data, task_id)
    
    if not task:
        print(json.dumps({"success": False, "error": f"Task not found: {task_id}"}), file=sys.stderr)
        sys.exit(1)
    
    old_status = task.get("status", "pending")
    
    # WAL FIRST
    log_to_wal("STATUS_CHANGE", {
        "task_id": task_id,
        "old_status": old_status,
        "new_status": "blocked",
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    # Update task
    task["status"] = "blocked"
    task["blocked_reason"] = reason
    task["updated_at"] = datetime.now(timezone.utc).isoformat() + "Z"
    
    save_data(data)
    
    # Update SESSION-STATE
    goal = find_goal_by_id(data, task.get("goal_id", ""))
    if goal:
        update_session_state(task, goal, f"BLOCKED: {reason}")
    
    # Append to working buffer
    append_to_buffer("BLOCKED", f"{task_id}: {reason}")
    
    result = {
        "success": True,
        "task": task,
        "status_change": f"{old_status} → blocked",
        "reason": reason
    }
    print(json.dumps(result, indent=2))


def health_check() -> None:
    """
    Detect and report broken states in tasks.
    Auto-fixes: orphaned recurring, impossible states, corrupted times.
    """
    data = load_data()
    issues = []
    fixes = []
    
    for task in data["tasks"]:
        task_id = task.get("id", "unknown")
        
        # Check 1: Orphaned recurring (recurring=true but no parent goal)
        if task.get("recurring") and not task.get("goal_id"):
            issues.append(f"Orphaned recurring task: {task_id}")
            task["recurring"] = None
            fixes.append(f"Removed recurring flag from {task_id}")
        
        # Check 2: Impossible state (completed=true but progress < 100)
        if task.get("status") == "completed" and task.get("progress", 100) < 100:
            issues.append(f"Impossible state: {task_id} completed but progress={task.get('progress')}%")
            task["progress"] = 100
            fixes.append(f"Set progress=100% for completed task {task_id}")
        
        # Check 3: Impossible state (completed=true but status != completed)
        if task.get("status") == "completed" and not task.get("completed_at"):
            issues.append(f"Inconsistent completion: {task_id} status=completed but no completed_at")
            task["completed_at"] = datetime.now(timezone.utc).isoformat() + "Z"
            fixes.append(f"Added completed_at timestamp to {task_id}")
        
        # Check 4: Time corruption (actual_minutes > estimate * 10)
        if task.get("actual_minutes", 0) > task.get("estimate_minutes", 1) * 10:
            ratio = task.get("actual_minutes", 0) / task.get("estimate_minutes", 1)
            issues.append(f"Time anomaly: {task_id} actual={task.get('actual_minutes')}m vs estimate={task.get('estimate_minutes')}m ({ratio:.1f}x)")
        
        # Check 5: Bad dates (future dates for completed tasks)
        if task.get("status") == "completed":
            completed_at = task.get("completed_at", "")
            if completed_at > datetime.now(timezone.utc).isoformat():
                issues.append(f"Bad date: {task_id} completed_at={completed_at} is in future")
                task["completed_at"] = datetime.now(timezone.utc).isoformat() + "Z"
                fixes.append(f"Reset completed_at for {task_id}")
    
    # Save any auto-fixes
    if fixes:
        save_data(data)
    
    # Log health check to WAL
    log_to_wal("HEALTH_CHECK", {
        "issues_found": len(issues),
        "auto_fixes_applied": len(fixes),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    result = {
        "success": True,
        "health_status": "healthy" if not issues else "issues_found",
        "issues": issues,
        "auto_fixes": fixes,
        "summary": f"Found {len(issues)} issues, auto-fixed {len(fixes)}"
    }
    print(json.dumps(result, indent=2))


def flush_working_buffer() -> None:
    """
    Flush working buffer to daily memory file.
    Called during compaction or end-of-session.
    """
    if not WORKING_BUFFER_FILE.exists():
        return
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    daily_file = MEMORY_DIR / f"{today}.md"
    
    # Read buffer
    with open(WORKING_BUFFER_FILE, 'r') as f:
        buffer_content = f.read()
    
    # Append to daily file
    section = f"\n## Task Updates\n{buffer_content}\n"
    with open(daily_file, 'a') as f:
        f.write(section)
    
    # Clear buffer
    WORKING_BUFFER_FILE.write_text("")
    
    result = {
        "success": True,
        "message": f"Buffer flushed to {daily_file}",
        "lines_flushed": len(buffer_content.split('\n'))
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: task_manager_phase2.py <command> [args]")
        print("Commands: mark-progress, log-time, mark-blocked, health-check, flush-buffer")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "mark-progress":
        task_id = sys.argv[2] if len(sys.argv) > 2 else None
        progress = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        notes = sys.argv[4] if len(sys.argv) > 4 else ""
        if not task_id:
            print("Usage: task_manager_phase2.py mark-progress <task_id> <progress> [notes]", file=sys.stderr)
            sys.exit(1)
        mark_progress(task_id, progress, notes)
    
    elif command == "log-time":
        task_id = sys.argv[2] if len(sys.argv) > 2 else None
        minutes = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        notes = sys.argv[4] if len(sys.argv) > 4 else ""
        if not task_id:
            print("Usage: task_manager_phase2.py log-time <task_id> <minutes> [notes]", file=sys.stderr)
            sys.exit(1)
        log_time(task_id, minutes, notes)
    
    elif command == "mark-blocked":
        task_id = sys.argv[2] if len(sys.argv) > 2 else None
        reason = sys.argv[3] if len(sys.argv) > 3 else "No reason specified"
        if not task_id:
            print("Usage: task_manager_phase2.py mark-blocked <task_id> <reason>", file=sys.stderr)
            sys.exit(1)
        mark_blocked(task_id, reason)
    
    elif command == "health-check":
        health_check()
    
    elif command == "flush-buffer":
        flush_working_buffer()
    
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)
