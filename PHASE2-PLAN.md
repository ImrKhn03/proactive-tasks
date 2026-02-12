# Phase 2 Implementation Plan - Proactive Tasks v1.2.0

**Goal:** Add Proactive Agent v3.1.0 architecture patterns (WAL, SESSION-STATE, self-healing)  
**Timeline:** ~2-3 hours  
**Author:** Toki (commits under ImrKhn03)  

---

## Phase 2 Features (Detailed Breakdown)

### 1. SESSION-STATE.md Integration ⭐ CRITICAL
**What:** Active working memory for current task session  
**Why:** Captures immediate context without losing to chat history compression

**Implementation:**
- [ ] Create SESSION-STATE.md template in workspace root
- [ ] On every `mark-progress`, `log-time`, `mark-blocked` → update SESSION-STATE.md
- [ ] Store: Current task, progress %, time logged, any blockers
- [ ] On compaction, move SESSION-STATE → daily memory file, create fresh SESSION-STATE.md

**Files to modify:**
- task_manager_phase2.py (new)
- SESSION-STATE.md (new template)

**Example:**
```markdown
# SESSION-STATE.md - Active Working Memory
Last updated: 2026-02-12T08:35:00Z

## Current Task
- ID: task_412f65a0
- Title: Create server templates
- Progress: 75%
- Estimated: 120 min
- Actual logged: 65 min (45% faster than estimate)

## Blockers
- None

## Next action
Mark as complete and move to next task
```

---

### 2. WAL Protocol (Write-Ahead Logging) ⭐ CRITICAL
**What:** Write critical changes BEFORE responding to user  
**Why:** Prevent data loss on context cutoff, ensure persistence

**Triggers for WAL:**
- ✏️ Corrections ("It's X, not Y")
- 📍 Proper nouns (task names, goal names)
- 💰 Numbers (progress %, time, dates)
- 📌 Task status changes (pending → in_progress, etc)
- 🎯 Decisions made ("use this approach")
- ❌ Errors encountered

**Implementation:**
- [ ] Add `log_to_wal(event_type, content)` function
- [ ] Call BEFORE any JSON output
- [ ] WAL entries go to: `memory/WAL-2026-02-12.log`

**Files to modify:**
- task_manager_phase2.py
- Add memory/WAL-YYYY-MM-DD.log rotation

**Example:**
```python
def mark_progress(args):
    # WAL FIRST
    log_to_wal("PROGRESS_CHANGE", {
        "task_id": args.task_id,
        "old_progress": task.get("progress", 0),
        "new_progress": args.progress,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    # THEN modify data
    task["progress"] = args.progress
    save_data(data)
    # THEN respond
    print(json.dumps(...))
```

---

### 3. Working Buffer (Danger Zone Capture) ⚠️ IMPORTANT
**What:** Capture everything between memory compaction points  
**Why:** Prevent info loss when context gets truncated mid-session

**Implementation:**
- [ ] Create `memory/working-buffer.md` 
- [ ] On each task update, append to working-buffer
- [ ] On daily log write (e.g., during compaction), flush working-buffer → daily file
- [ ] Auto-rotate working-buffer daily

**Files to modify:**
- task_manager_phase2.py
- Add working-buffer.md template

**Example:**
```markdown
# Working Buffer - 2026-02-12
Captured during danger zone (between compaction)

## Task Updates
- task_412: Progress 50% → 75% (15:34 UTC)
- task_ef2: Blocked "Waiting on schema" (15:35 UTC)
- task_7bb: Recurring next occurrence created (15:36 UTC)

## Time Logs
- task_412: 25 min logged (15:37 UTC)

## Notes
- User mentioned speed issue with 1000+ tasks
- Consider indexing for next version
```

---

### 4. Autonomous Cron Patterns 🚀 IMPORTANT
**What:** Distinguish `systemEvent` (interactive) vs `isolated agentTurn` (background)  
**Why:** Background work shouldn't interrupt main session

**Implementation:**
- [ ] Add HEARTBEAT.md guidance section
- [ ] Document when to use each pattern
- [ ] Provide example cron configurations

**Files to modify:**
- Add to SKILL.md: "Autonomous Operation" section
- Add HEARTBEAT-CONFIG.md (example setups)

**Example guidance:**
```markdown
## Autonomous Work Patterns

### ✅ Use `isolated agentTurn` for:
- Background velocity checks
- Weekly recurring task creation
- Cleanup/maintenance operations
- "Don't interrupt main session" work

### ✅ Use `systemEvent` for:
- User requests ("complete this task")
- Interactive queries ("show velocity")
- User-facing updates

### ❌ Don't use `systemEvent` for background work
- Cron fires while main session busy
- Prompt ignored, work doesn't happen
- Use `isolated agentTurn` instead
```

---

### 5. Self-Healing Mechanisms 🔧 NICE-TO-HAVE
**What:** Auto-detect and fix broken states  
**Why:** Resilience without user intervention

**Implementation:**
- [ ] Add health check command: `python3 scripts/task_manager_phase2.py health-check`
- [ ] Detects: Orphaned recurring tasks, impossible states, corrupted times
- [ ] Auto-fixes: Removes impossible states, resets bad dates

**Examples to catch:**
- Recurring task with no parent goal → remove
- Task status="completed" but next_due_at in future → fix
- actual_minutes > estimate_minutes * 10 → flag for review
- Task with progress=100 but status="pending" → auto-complete

**Files to modify:**
- task_manager_phase2.py (add health-check command)

---

### 6. Evolution Guardrails (VFM/ADL) 📋 OPTIONAL
**What:** Structured decision-making for feature additions  
**Why:** Prevent feature creep, maintain stability

**Implementation:**
- [ ] Add EVOLUTION.md with scoring framework
- [ ] VFM Protocol: Score new features (High Frequency 3x, Failure Reduction 3x, User Burden 2x, Self Cost 2x)
- [ ] ADL Protocol: Stability > Explainability > Reusability > Scalability > Novelty
- [ ] Reference in commit messages: "VFM score: 72/100"

**Files to create:**
- EVOLUTION.md (scoring framework)
- Document in SKILL.md

---

## Task Breakdown (For execution)

### Task 1: SESSION-STATE.md + WAL Protocol (90 min)
- [ ] Design SESSION-STATE.md schema
- [ ] Implement log_to_wal() function
- [ ] Integrate into mark-progress, log-time, mark-blocked
- [ ] Test: Make 5 updates, verify WAL logs created
- [ ] Update SKILL.md with SESSION-STATE explanation

### Task 2: Working Buffer Implementation (45 min)
- [ ] Create working-buffer.md template
- [ ] Add append-to-buffer function
- [ ] Integrate into all task update commands
- [ ] Add daily flush to memory/YYYY-MM-DD.md
- [ ] Test: Verify buffer logs, flush works

### Task 3: Autonomous Cron Patterns & Docs (30 min)
- [ ] Write "Autonomous Operation" section in SKILL.md
- [ ] Create HEARTBEAT-CONFIG.md with examples
- [ ] Add cron examples (isolated vs systemEvent)
- [ ] Update README with autonomy explanation

### Task 4: Self-Healing Health Check (45 min)
- [ ] Design health check logic
- [ ] Implement: detect orphaned, impossible states
- [ ] Implement: auto-fix (remove, reset)
- [ ] Test: Create broken states, run health-check, verify fixes

### Task 5: Evolution Guardrails Documentation (20 min)
- [ ] Create EVOLUTION.md with VFM/ADL frameworks
- [ ] Add examples (why a feature passed/failed scoring)
- [ ] Reference in SKILL.md

### Task 6: Integration & Testing (30 min)
- [ ] Rename task_manager_phase2.py → task_manager.py (merge with original)
- [ ] Test full workflow: create goal → task → mark progress → log time
- [ ] Verify SESSION-STATE, WAL, working-buffer all captured
- [ ] Test health-check catches and fixes broken states

### Task 7: Documentation & Git Cleanup (20 min)
- [ ] Update SKILL.md with all new sections
- [ ] Update README.md (v1.2.0 features)
- [ ] Add CHANGELOG.md (v1.0 → v1.1 → v1.2)
- [ ] Git commits with semantic messages (under your name)

---

## Total Effort Estimate

| Task | Duration | Complexity |
|------|----------|-----------|
| SESSION-STATE + WAL | 90 min | High |
| Working Buffer | 45 min | Medium |
| Autonomous Cron Docs | 30 min | Low |
| Self-Healing | 45 min | Medium |
| Evolution Guardrails | 20 min | Low |
| Integration & Testing | 30 min | Medium |
| Documentation | 20 min | Low |
| **TOTAL** | **280 min** | **~4.5 hours** |

**Optimistic estimate:** 3 hours (focused execution)  
**Realistic estimate:** 4-5 hours (with testing, iteration)

---

## Success Criteria

When Phase 2 is complete:
- ✅ SESSION-STATE.md created and updated on every task change
- ✅ WAL logs capture all critical events
- ✅ Working buffer auto-flushes to daily memory
- ✅ HEARTBEAT.md has autonomous cron guidance
- ✅ health-check command detects and fixes broken states
- ✅ EVOLUTION.md documents decision framework
- ✅ All commits under ImrKhn03 name
- ✅ GitHub repo created with full history
- ✅ v1.2.0 ready for ClawdHub release

---

## Notes

**This is the difference between "good task tracker" and "production-ready agent framework":**
- Phase 1 = Core features
- Phase 2 = Resilience, persistence, autonomy, safety
- After Phase 2: v1.2.0 rivals Proactive Agent v3.1.0 in architecture

**Starting when ready. Will notify you when Phase 2 is complete and ready to push.**
