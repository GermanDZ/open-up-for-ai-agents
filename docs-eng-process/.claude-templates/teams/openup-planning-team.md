# OpenUP Planning Team Configuration

This is a task-specific team configuration for iteration planning and roadmap management.

⚠️ **MANDATORY FIRST STEP FOR TEAM LEAD** ⚠️

**BEFORE spawning any teammates, the team lead MUST:**

1. Use `/openup-start-iteration task_id: XXX` to initialize the iteration
2. Only AFTER the iteration is started, then spawn teammates
3. Do NOT skip this step - all work must be tracked in iterations

**Example correct flow:**
```
/openup-start-iteration task_id: T-005
# Then spawn teammates...
```

---


## Team Purpose

Plan iterations, update the roadmap, assess priorities, and coordinate project planning activities.

## Team Members

### project-manager (Lead)
- **Focus**: Lead planning session, coordinate roadmap updates
- **Key Activities**: Iteration planning, task prioritization, risk assessment
- **Collaborates With**: Analyst (requirements scope), Architect (technical feasibility), Developer (estimates)
- **Reference**: `.claude/teammates/project-manager.md`

### analyst
- **Focus**: Review and prioritize requirements
- **Key Activities**: Requirements analysis, stakeholder input, value assessment
- **Collaborates With**: Project Manager (prioritization), Architect (feasibility)
- **Reference**: `.claude/teammates/analyst.md`

### architect (As needed)
- **Focus**: Assess technical feasibility and dependencies
- **Key Activities**: Technical analysis, dependency identification, effort assessment
- **Collaborates With**: Analyst (requirements feasibility), Project Manager (planning)
- **Reference**: `.claude/teammates/architect.md`

### developer (As needed)
- **Focus**: Provide effort estimates for development tasks
- **Key Activities**: Task estimation, technical assessment
- **Collaborates With**: Project Manager (estimates), Architect (technical details)
- **Reference**: `.claude/teammates/developer.md`

## Planning Process

**CRITICAL FIRST STEP**: Before starting planning work, the team lead (project-manager) MUST use `/openup-start-iteration` to initialize the iteration. All work must be tracked as part of an iteration.

1. **Review Current State**
   - Review `docs/project-status.md` for current phase and iteration
   - Review `docs/roadmap.md` for pending tasks
   - Assess what was accomplished in the previous iteration

2. **Identify Candidates**
   - Analyst identifies high-value requirements
   - Architect identifies technical debt and architectural work
   - Project Manager reviews risks and dependencies

3. **Assess Feasibility**
   - Architect assesses technical feasibility
   - Developer provides effort estimates
   - Project Manager assesses resource availability

4. **Prioritize Tasks**
   - Prioritize by value, risk, and dependencies
   - Balance feature work with technical debt
   - Ensure iteration goals are achievable

5. **Create Iteration Plan**
   - Define iteration goal
   - Select tasks for the iteration
   - Assign tasks to roles
   - Define success criteria

6. **Update Documentation**
   - Update `docs/roadmap.md` with task status
   - Create iteration plan document
   - Update `docs/project-status.md`

## Creating This Team

To create an OpenUP Planning team, use this prompt:

```
Create an OpenUP agent team for iteration planning.

Spawn teammates for:
- project-manager: to lead the planning session
- analyst: to review and prioritize requirements
- architect: to assess technical feasibility

The project-manager should lead the planning session and update the roadmap.
The analyst should review requirements and help prioritize based on value.
The architect should assess technical feasibility and identify dependencies.
```

## Task Assignment Guidelines

- **Planning coordination** → project-manager
- **Requirements analysis** → analyst
- **Technical feasibility** → architect
- **Effort estimation** → developer
- **Prioritization** → project-manager + analyst
- **Risk assessment** → project-manager

## Collaboration Patterns

- **Project Manager ↔ Analyst**: Value vs. effort trade-offs
- **Project Manager ↔ Architect**: Technical feasibility assessment
- **Analyst ↔ Architect**: Requirements vs. technical constraints
- **All**: Task prioritization and iteration goal definition

## Example Usage

```
Create an OpenUP planning team for iteration planning.

The team should:
1. Review the current iteration status
2. Identify candidate tasks for the next iteration
3. Assess technical feasibility and effort
4. Prioritize tasks based on value and dependencies
5. Create the iteration plan
6. Update the roadmap and project status
```
