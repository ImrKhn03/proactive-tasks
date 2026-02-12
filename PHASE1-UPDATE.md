# Proactive Tasks - Phase 1 Features Update

**Release:** v1.1.0  
**Date:** 2026-02-12  
**Author:** Toki

## What's New

### Phase 1 Enhancements — Persistence, Progress, Time Tracking

We've analyzed **Proactive Agent v3.1.0** (industry-leading agent framework) and implemented the top missing features in our proactive-tasks skill. This makes our tool production-ready for serious autonomous work.

## New Commands

### 1. **Progress Tracking** (0-100%)
```bash
python3 scripts/task_manager_phase1.py mark-progress <task-id> <0-100>
```

**Why:** Know how close tasks are. Partial progress is real progress.

**Example:**
```bash
$ python3 scripts/task_manager_phase1.py mark-progress task_001 50
# Task moves to "in_progress" at 50%
# Task auto-completes when progress hits 100%
```

### 2. **Time Tracking**
```bash
python3 scripts/task_manager_phase1.py log-time <task-id> <minutes>
```

**Why:** Measure actual vs estimated time. Build velocity data.

**Example:**
```bash
$ python3 scripts/task_manager_phase1.py log-time task_001 45
# Logs 45 minutes
# Calculates variance: "25% over estimate"
# Data feeds into velocity tracking
```

### 3. **Blocking with Reasons**
```bash
python3 scripts/task_manager_phase1.py mark-blocked <task-id> "<reason>"
python3 scripts/task_manager_phase1.py unblock-task <task-id>
```

**Why:** Know WHY a task is stuck. Better messaging to your human.

**Example:**
```bash
$ python3 scripts/task_manager_phase1.py mark-blocked task_001 "Waiting on API key from Imran"
# Task status shows exact blocker
# Can message human with specific ask
```

### 4. **Recurring Tasks** (Daily/Weekly/Monthly)
```bash
python3 scripts/task_manager_phase1.py create-recurring <goal-id> "<title>" \
  --recurring daily|weekly|monthly|after_completion \
  --priority high|medium|low \
  --estimate <minutes>
```

**Why:** Automate repetitive work. Daily standup, weekly reviews, etc.

**Example:**
```bash
$ python3 scripts/task_manager_phase1.py create-recurring goal_001 "Code review" \
  --recurring weekly --priority high --estimate 30

$ python3 scripts/task_manager_phase1.py next-recurring task_123
# Marks current as done
# Auto-creates next occurrence for next week
```

### 5. **Velocity Tracking**
```bash
python3 scripts/task_manager_phase1.py show-velocity <goal-id>
```

**Why:** Know how fast you're moving. Estimate when you'll finish.

**Example:**
```bash
$ python3 scripts/task_manager_phase1.py show-velocity goal_001
{
  "velocity_tasks_per_day": 2.5,
  "remaining": 15,
  "estimated_days_to_completion": 6.0
}
# You're completing 2.5 tasks/day
# 15 tasks left = ~6 days to finish goal
```

## Data Schema (Enhanced)

Tasks now include:

```json
{
  "id": "task_001",
  "title": "Build server templates",
  "status": "in_progress",
  "progress": 50,
  "estimate_minutes": 120,
  "actual_minutes": 45,
  "time_variance_percent": -62.5,
  "recurring": "weekly",
  "next_due_at": "2026-02-19T08:00:00Z",
  "blocked_reason": "Waiting on schema design",
  "created_at": "2026-02-12T08:00:00Z",
  "completed_at": null,
  "updated_at": "2026-02-12T08:30:00Z"
}
```

## Improvements Inspired by Proactive Agent v3.1.0

### What We Learned from Industry Leaders

**Proactive Agent v3.1.0** covers:
- WAL Protocol (Write-Ahead Logging for context preservation)
- Working Buffer (danger zone capture)
- Autonomous vs Prompted crons
- Evolution guardrails (ADL/VFM protocols)

**What we implemented from their patterns:**
1. ✅ **Progress tracking** — Know partial completion
2. ✅ **Time tracking** — Build velocity data
3. ✅ **Blocking with reasons** — Know why stuck
4. ✅ **Recurring tasks** — Automate repetition
5. ✅ **Velocity metrics** — Predict completion

**What we're adding next (Phase 2):**
- WAL Protocol integration (capture task status changes)
- SESSION-STATE.md (active working memory)
- working-buffer.md (danger zone logging)
- Self-healing (auto-fix failed tasks)
- Evolution guardrails (VFM/ADL scoring)

## Integration with Heartbeat

Add to your `HEARTBEAT.md`:

```markdown
## Proactive Tasks (Every heartbeat) 🚀

### Work Phase
- [ ] Run `python3 skills/proactive-tasks/scripts/task_manager_phase1.py next-task`
- [ ] Work on task for 10-15 minutes
- [ ] Log progress: `mark-progress <id> <0-100>`
- [ ] Log time: `log-time <id> <minutes>`

### Status Phase
- [ ] If blocked: `mark-blocked <id> "<reason>"` + message human
- [ ] If done: `next-task` auto-returns next priority

### Check Velocity
- [ ] `show-velocity <goal-id>` — Know how fast we're moving
- [ ] Predict completion: "6 days at current velocity"
```

## Example Workflow

**Day 1:**
```bash
$ python3 scripts/task_manager_phase1.py next-task
# Returns: "Build server templates" (priority: high)

$ python3 scripts/task_manager_phase1.py mark-progress task_412 25
# 25% done

$ python3 scripts/task_manager_phase1.py log-time task_412 15
# Logged 15 min, estimate was 120 min (-87.5%)
```

**Day 2 (heartbeat fires):**
```bash
$ python3 scripts/task_manager_phase1.py next-task
# Returns same task

$ python3 scripts/task_manager_phase1.py mark-progress task_412 60
$ python3 scripts/task_manager_phase1.py log-time task_412 20
# Total: 35 min logged, 60% done

$ python3 scripts/task_manager_phase1.py show-velocity goal_42
# velocity: 1.5 tasks/day
# remaining: 2 tasks
# ETA: 1.3 days
```

**Day 3 (at 95% done):**
```bash
$ python3 scripts/task_manager_phase1.py mark-progress task_412 100
# Auto-completes!
# Next heartbeat returns next task automatically
```

## Migration Path

**Your existing tasks are safe.** The enhanced commands work with the same `tasks.json`:

1. Keep using old task_manager.py for basic commands
2. Use task_manager_phase1.py for new features
3. Gradually migrate to Phase 1 features
4. Merge Phase 1 into main task_manager.py once stable

## What This Enables

With Phase 1 features, you can now:

✅ **Track progress** — 0% to 100%, not just binary done/not-done  
✅ **Measure velocity** — "2.5 tasks/day" — predict when you'll finish  
✅ **Know why you're stuck** — Specific blockers, not vague status  
✅ **Automate repetition** — Weekly reviews, daily checks run themselves  
✅ **Estimate better** — Actual vs estimated time, improve forecasts next time  

## Next: Phase 2

When you're ready, we'll add:
- SESSION-STATE.md integration
- WAL Protocol triggers
- Working Buffer capturing
- Self-healing mechanisms
- Safe evolution guardrails

---

**Ready to push to ClawdHub? Let's document everything, test thoroughly, and release v1.1.0!**
