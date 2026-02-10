# Tiered Context Configuration

This configuration defines three context tiers for OpenUP skills and agent teams. Each tier provides different levels of detail, allowing you to balance token usage with process compliance.

## Context Tiers

### Tier 1: Minimal (Fast Mode)

**Token Budget**: ~1,000 tokens
**Use Case**: Quick tasks, small changes, rapid iteration

**Includes**:
- Current task description only
- No role instructions
- No process documentation
- Essential file paths only

**Commands**:
```bash
python3 .claude/scripts/batch-context.py --minimal
```

**Best For**:
- `/openup-quick-task` usage
- Hot fixes
- Single-file changes
- Documentation updates

---

### Tier 2: Standard (Default)

**Token Budget**: ~4,000 tokens
**Use Case**: Regular development work, most iterations

**Includes**:
- Current task + project status summary
- Relevant role instructions (single role)
- Essential process steps
- Current phase guidance
- Recent agent logs (last 5 entries)

**Commands**:
```bash
python3 .claude/scripts/batch-context.py --pretty
```

**Best For**:
- Standard iteration work
- Feature implementation
- Bug fixes requiring analysis
- Most agent team operations

---

### Tier 3: Full (Strict Mode)

**Token Budget**: ~12,000 tokens
**Use Case**: Formal reviews, phase transitions, complex decisions

**Includes**:
- Full project context (all documents)
- All role instructions
- Complete SOPs and process documentation
- Full roadmap and vision
- All agent logs
- Risk list and architecture notebook

**Commands**:
```bash
python3 .claude/scripts/batch-context.py --include vision risk-list architecture-notebook --pretty
```

**Best For**:
- Phase transitions (`/openup-phase-review`)
- Architecture decisions
- Retrospectives
- Planning sessions
- Compliance requirements

---

## Tier Selection Guide

| Situation | Recommended Tier | Reason |
|-----------|------------------|--------|
| Hot fix in production | Tier 1 | Speed critical |
| Small documentation change | Tier 1 | Minimal context needed |
| Regular feature work | Tier 2 | Balance of context and efficiency |
| Bug investigation | Tier 2 | Need some context but not full |
| New feature implementation | Tier 2 | Standard development workflow |
| Phase review | Tier 3 | Full compliance required |
| Architecture decision | Tier 3 | Need full context |
| Stakeholder review | Tier 3 | Formal documentation needed |

---

## Per-Skill Tier Configuration

Skills can specify their default tier:

```yaml
---
name: openup-quick-task
default_tier: minimal
estimated_tokens: 1000
---

---
name: openup-start-iteration
default_tier: standard
estimated_tokens: 4000
---

---
name: openup-phase-review
default_tier: full
estimated_tokens: 12000
---
```

---

## Environment Configuration

Set default tier via environment variable:

```bash
# In .claude/settings.json or shell
export OPENUP_CONTEXT_TIER=standard  # minimal | standard | full
```

---

## Token Usage Tracking

Track actual token usage per tier:

```bash
# View tier statistics
python3 .claude/scripts/token-tracker.py --by-tier

# Expected vs actual
python3 .claude/scripts/token-tracker.py --compare
```

---

## Tier Override

Override default tier for specific operations:

```yaml
# In skill invocation
/openup-start-iteration context_tier: minimal

# For agent teams
Create team with context_tier: full
```

---

## Optimization Targets

| Metric | Tier 1 | Tier 2 | Tier 3 |
|--------|--------|--------|--------|
| Token Usage | ~1,000 | ~4,000 | ~12,000 |
| Speed | Fastest | Standard | Slowest |
| Compliance | Minimal | Standard | Full |
| Traceability | Basic | Full | Complete |
| Recommended Usage | 20% | 70% | 10% |
