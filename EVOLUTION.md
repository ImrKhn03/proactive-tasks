# EVOLUTION.md - Evolution Guardrails & VFM/ADL Scoring

**Purpose:** Framework for evaluating new features and architectural decisions to maintain stability while enabling growth.

---

## Overview

Before adding new features to proactive-tasks, evaluate them against two frameworks:

1. **VFM (Value Frequency Multiplier)** - Does this feature deliver value?
2. **ADL (Architecture Design Ladder)** - How well does it fit our design?

This prevents feature creep and maintains production stability.

---

## VFM Protocol - Value Frequency Multiplier

Quantify feature value across four dimensions:

### Scoring Dimensions

| Dimension | Multiplier | How to Score |
|-----------|-----------|-------------|
| **High Frequency** | 3x | How often will this be used? |
| **Failure Reduction** | 3x | Does this prevent errors/data loss? |
| **User Burden** | 2x | Does this reduce manual work? |
| **Self Cost** | 2x | How much infrastructure/maintenance? |

### Scoring Process

1. **High Frequency (3x multiplier):** How often will agents use this feature?
   - 4+ times per session = 10 points
   - 2-4 times per session = 7 points
   - Once per session = 4 points
   - Monthly = 1 point

2. **Failure Reduction (3x multiplier):** Does this prevent data loss or errors?
   - Critical blocker for production = 10 points
   - Major data loss risk = 8 points
   - Minor error prevention = 4 points
   - Nice-to-have = 1 point

3. **User Burden (2x multiplier):** Does this reduce manual work?
   - Eliminates major pain point = 10 points
   - Saves significant time = 7 points
   - Saves minor time = 4 points
   - Convenience feature = 1 point

4. **Self Cost (2x multiplier):** How much infrastructure/maintenance?
   - < 50 lines of code = 10 points
   - 50-200 lines = 7 points
   - 200-500 lines = 4 points
   - > 500 lines = 1 point

### Calculate VFM Score

```
VFM = (High_Frequency × 3) + (Failure_Reduction × 3) + (User_Burden × 2) + (Self_Cost × 2)
Max VFM = (10×3) + (10×3) + (10×2) + (10×2) = 100

Pass threshold: >= 60 points
```

### Example: WAL Protocol (Phase 2)

- **High Frequency:** 10 pts (every update logs)
- **Failure Reduction:** 10 pts (prevents critical data loss on context cutoff)
- **User Burden:** 8 pts (transparent to user, automatic)
- **Self Cost:** 9 pts (elegant, <200 lines)

**VFM Score:** (10×3) + (10×3) + (8×2) + (9×2) = 30 + 30 + 16 + 18 = **94/100** ✅ STRONG PASS

---

## ADL Protocol - Architecture Design Ladder

Prioritizes design values in order of importance:

### Design Priority Ladder (Top = Most Important)

1. **Stability** ⭐⭐⭐
   - Production reliability above all
   - Data integrity never compromised
   - No breaking changes without migration path

2. **Explainability** ⭐⭐
   - Code is readable, not clever
   - Behavior is predictable
   - Errors are debuggable

3. **Reusability** ⭐
   - Components serve multiple goals
   - Patterns are consistent
   - Avoid one-off solutions

4. **Scalability**
   - Works with 10 and 1000 tasks
   - Performance degrades gracefully
   - No hard limits

5. **Novelty**
   - Cool new ideas are nice
   - But never at cost of above 4 values
   - Innovation must serve stability first

### ADL Evaluation Checklist

For each proposed feature, ask:

- [ ] **Stability:** Does this risk existing data? Could it corrupt state?
- [ ] **Explainability:** Can a new maintainer understand this without documentation?
- [ ] **Reusability:** Will other features need this? Is it generic enough?
- [ ] **Scalability:** Will it work with 100x current data volume?
- [ ] **Novelty:** Is this the only/best way to solve the problem?

**Pass rule:** If you answer "no" to Stability or Explainability questions, it fails ADL review.

### Example: Working Buffer (Phase 2)

- ✅ **Stability:** Improves it (prevents context-cutoff data loss)
- ✅ **Explainability:** Simple markdown file, obvious behavior
- ✅ **Reusability:** Template can be used by any agent
- ✅ **Scalability:** Just appends to file, scales fine
- ✅ **Novelty:** Not fancy but effective

**ADL Result:** PASS - Serves stability and explainability first

---

## Combined Evaluation Template

When proposing a new feature:

```markdown
## Feature: [Name]

### VFM Score
- High Frequency: [score] (justification)
- Failure Reduction: [score] (justification)
- User Burden: [score] (justification)
- Self Cost: [score] (justification)
**Total: [score]/100** (PASS/FAIL)

### ADL Review
- Stability: [✅/❌] (comment)
- Explainability: [✅/❌] (comment)
- Reusability: [✅/❌] (comment)
- Scalability: [✅/❌] (comment)
- Novelty: [✅/❌] (comment)

### Decision
[APPROVE/REJECT] - Reasoning based on scores

### Implementation Notes
- Code budget: X lines
- Testing plan: Y
- Maintenance burden: Z
```

---

## Real Examples

### ✅ Feature That Passes Both Frameworks

**Feature:** SESSION-STATE.md + WAL Protocol

- VFM: 94/100 (high frequency, critical failure reduction, elegant implementation)
- ADL: PASS (Stability + Explainability > Novelty)
- **Decision:** APPROVE - Foundational for production stability

### ❌ Feature That Fails VFM

**Feature:** Slack integration notifications

- VFM: 42/100 (low frequency, no failure reduction, high self cost)
- ADL: PASS
- **Decision:** REJECT - Value doesn't justify maintenance burden

### ❌ Feature That Fails ADL

**Feature:** Magical auto-parallelization of tasks

- VFM: 85/100 (high value, rare but powerful)
- ADL: FAIL (Stability risk - could corrupt shared state, hard to explain)
- **Decision:** REJECT - Stability concerns outweigh value

---

## Decision Rules

| Scenario | Decision |
|----------|----------|
| VFM ≥ 60 AND ADL PASS | **APPROVE** |
| VFM < 60 AND ADL PASS | **CONSIDER** (only if critical) |
| VFM ≥ 60 AND ADL FAIL | **REJECT** (too risky) |
| VFM < 60 AND ADL FAIL | **REJECT** (not worth it) |

---

## Commit Message Convention

When implementing evaluated features, reference your scoring:

```
feat(area): brief description

- VFM score: 78/100 (strong value, good implementation cost)
- ADL: PASS (stability-first design)
- Rationale: [Why this feature makes sense]

[Details of implementation]
```

---

## Updating This Framework

As proactive-tasks evolves:

1. Review completed features for real-world VFM accuracy
2. Adjust multipliers if needed (e.g., if User Burden is always high, reduce multiplier)
3. Add new ADL dimensions if architecture patterns change
4. Document lessons learned from features that passed but underperformed

---

**Created for Proactive Tasks v1.2.0 - Phase 2 Production Ready Architecture**

See SKILL.md for core documentation. See PHASE2-PLAN.md for implementation roadmap.
