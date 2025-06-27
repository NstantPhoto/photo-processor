# SESSION_PROTOCOL.md

Maintaining continuity across development sessions for Nstant Nfinity.

## AT THE START OF EACH SESSION

### 1. State Current Location
Always begin with:
```
"We are working on [component] in Nstant Nfinity"
```

Examples:
- "We are working on the Hot Folder Monitor in Nstant Nfinity"
- "We are working on the Exposure Correction Node in Nstant Nfinity"
- "We are working on UI Polish in Nstant Nfinity"

### 2. Reference Last Checkpoint
Review what was accomplished:
```
"Last session we completed [feature/task]"
```

Check:
- PROJECT_STATE.md for last updates
- Git commits from previous session
- Any TODO comments left in code

### 3. Define Session Goal
Be specific about today's objective:
```
"This session we will implement [specific feature]"
```

Goals should be:
- Achievable in 2-4 hours
- Specific and measurable
- Aligned with current sprint

### 4. Confirm Understanding
Before starting, summarize:
```
"Please summarize the task and approach"
```

Should include:
- What we're building
- How it fits into the system
- Expected outcomes
- Potential challenges

## DURING THE SESSION

### Major Step Checkpoints
After completing each major step:
```
"Checkpoint: We've completed [step]. Next is [step]."
```

Examples:
- "Checkpoint: We've completed the interface design. Next is stub implementation."
- "Checkpoint: We've completed core logic. Next is error handling."
- "Checkpoint: We've completed unit tests. Next is integration."

### When Confused
If something is unclear:
```
"I need clarification on [specific aspect]"
```

Provide:
- What you understand so far
- Where confusion arose
- What information would help

### Before Big Changes
Always ask before major modifications:
```
"This will modify [component]. Should I proceed?"
```

Include:
- What will change
- Why it's needed
- Impact on other components
- Rollback plan if needed

### Progress Updates
Every 30-45 minutes:
```
"Progress: [what's done], [what's in progress], [what's next]"
```

## AT THE END OF EACH SESSION

### 1. Summary
Comprehensive session summary:
```
"This session we implemented [features/components]"
```

Include:
- Components created/modified
- Files changed
- Features completed
- Features partially done

### 2. Testing
Report test results:
```
"We tested [components] with [results]"
```

Details:
- Unit tests run and passed
- Integration tests status
- Manual testing performed
- Any failing tests

### 3. Next Steps
Clear direction for next session:
```
"Next session should focus on [specific task]"
```

Consider:
- Incomplete work from this session
- Next priority from sprint
- Any blockers discovered
- Dependencies needed

### 4. Update Documentation
**CRITICAL: Update PROJECT_STATE.md**

```markdown
## COMPLETED COMPONENTS
- [x] Component Name v1.0
  - Path: `/path/to/component`
  - Description: What it does
  - Test Status: X/Y passing
  - Version: 1.0
  - Last Updated: YYYY-MM-DD

## CURRENT SPRINT
[Update progress]

## KNOWN ISSUES
[Add any new issues discovered]
```

## SESSION TYPES

### Feature Development Session
Focus: Implementing new functionality
- Follow 5-phase workflow
- Complete at least one full phase
- Update tests and docs

### Bug Fix Session
Focus: Resolving specific issues
- Reproduce bug first
- Fix with minimal changes
- Add regression tests
- Document in KNOWN ISSUES

### Refactoring Session
Focus: Improving existing code
- Must have approval first
- Keep functionality identical
- Improve performance/readability
- Full test suite must pass

### UI/UX Session
Focus: Interface improvements
- Visual polish
- Animation smoothness
- Responsive design
- User feedback

### Performance Session
Focus: Optimization
- Run benchmarks first
- Profile bottlenecks
- Implement improvements
- Verify benchmarks improved

## HANDOFF TEMPLATE

Use this template at session end:

```markdown
## Session Summary - [DATE]

### Location
Working on: [Component] in Nstant Nfinity

### Completed
- ✓ [Specific feature/task]
- ✓ [Tests written/passed]
- ✓ [Documentation updated]

### In Progress
- ◐ [Partially complete feature]
- ◐ [Needs: specific work]

### Blockers
- ⚠️ [Any blocking issues]

### Next Session
Focus on: [Specific next task]
Prerequisites: [Any setup needed]
Estimated time: [X hours]

### Code Status
- All tests: [PASSING/FAILING]
- Lint status: [CLEAN/ISSUES]
- Build status: [SUCCESS/FAILING]

### Notes
[Any important context for next session]
```

## CONTINUITY CHECKLIST

Before ending ANY session:

- [ ] Code compiles without errors
- [ ] Tests are passing (or documented why not)
- [ ] No uncommitted work (commit with WIP if needed)
- [ ] PROJECT_STATE.md updated
- [ ] Clear next steps documented
- [ ] Any blocking issues noted

## RECOVERY PROTOCOL

If session ends unexpectedly:

1. **Check Git Status**
   ```bash
   git status
   git diff
   ```

2. **Save Work**
   ```bash
   git add -A
   git commit -m "WIP: [what was being worked on]"
   ```

3. **Document State**
   - Add RECOVERY_NOTES.md
   - Describe what was being attempted
   - List any errors encountered

4. **Next Session**
   - Start with recovery
   - Review WIP commit
   - Continue or rollback

## COMMUNICATION STYLE

### Clear and Direct
- "I will now implement X"
- "This approach has Y trade-offs"
- "I encountered error Z"

### Proactive Updates
- Don't wait to be asked
- Report issues immediately
- Celebrate small wins

### Technical Precision
- Use correct terminology
- Reference file paths
- Include error messages

## SUCCESS METRICS

A successful session has:
- Clear progress on stated goal
- Updated documentation
- Clean handoff for next session
- No broken functionality
- Learned something new

## REMEMBER

> "Every session builds on the last. Clear communication ensures nothing is lost between sessions."

This protocol ensures that whether it's tomorrow or next month, we can pick up exactly where we left off and continue building Nstant Nfinity efficiently.