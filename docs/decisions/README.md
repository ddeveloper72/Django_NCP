# Django_NCP — Decision Log Index

This directory contains architectural and technical decisions made during the development of Django_NCP.

---

## 📋 **Decision Log Format**

Each decision document should follow this structure:

```markdown
# Decision: [Short Title]

**Date:** YYYY-MM-DD
**Status:** [Proposed/Accepted/Superseded]
**Deciders:** [Names or roles]

## Context

What is the situation that led to this decision?

## Decision

What is the change we're making?

## Consequences

What are the positive and negative impacts of this decision?
```

---

## 📚 **Current Decisions**

| Date | Decision File | Status | Summary |
|------|---------------|--------|---------|
| 2025-09-20 | [001-vscode-automation-setup.md](./001-vscode-automation-setup.md) | Accepted | VS Code runOnSave and SASS compilation setup |
| TBD | [002-bootstrap-to-sass-migration.md](./002-bootstrap-to-sass-migration.md) | Proposed | Migration from Bootstrap to custom SASS with HSE colors |
| TBD | [003-view-refactoring-strategy.md](./003-view-refactoring-strategy.md) | Proposed | Strategy for converting FBVs to CBVs |

---

## 🔄 **Decision Review Process**

1. **Propose:** Create new decision document with "Proposed" status
2. **Review:** Discuss with team/stakeholders if applicable
3. **Accept:** Update status to "Accepted" and implement
4. **Supersede:** If later changed, mark as "Superseded" and link to new decision

---

**Last Updated:** 2025-09-20
