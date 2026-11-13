# Project Guidelines & Agent Directives

Welcome to **promwar**! This file outlines core architecture rules, development standards, and workflows expected from any autonomous agent or developer working in this repository.

---

## 1. Skills Library Location

All agent skills are centralized in the single folder:
```
.agents/skills/
```

Before undertaking complex tasks, inspect and invoke the appropriate skills:

| Capability / Task | Recommended Skill |
|---|---|
| **Ideation & Brainstorming** | `.agents/skills/brainstorming` |
| **Writing Implementation Plans** | `.agents/skills/writing-plans` |
| **Executing Plans** | `.agents/skills/executing-plans` |
| **Frontend UI/UX Polish** | `.agents/skills/frontend-design`, `.agents/skills/web-design-guidelines` |
| **React & Next.js Performance** | `.agents/skills/react-best-practices`, `.agents/skills/composition-patterns` |
| **Testing (Unit, Integration & E2E)**| `.agents/skills/test-driven-development`, `.agents/skills/webapp-testing` |
| **Systematic Debugging** | `.agents/skills/systematic-debugging` |
| **Code Review & Verification** | `.agents/skills/requesting-code-review`, `.agents/skills/verification-before-completion` |
| **Security Auditing (OWASP)** | `.agents/skills/security-audit` |
| **Backend & API Architecture** | `.agents/skills/backend-development` |
| **Deployment & Hosting** | `.agents/skills/deploy-to-vercel` |

---

## 2. Core Engineering Standards

1. **Test-Driven & Verified Code**:
   - Write or update unit/integration tests when creating or modifying features.
   - Run verification checks (`npm test`, build checks, linter) before declaring a task complete.

2. **Strict Typing & Input Validation**:
   - Never use `any` types unnecessarily. Use strict schemas (e.g. Zod) for all external input points.

3. **Security by Default**:
   - Follow OWASP Top 10 guidelines (refer to `.agents/skills/security-audit`).
   - Validate authorization on every data access query; never rely solely on client-provided IDs.
   - Never commit sensitive secrets or keys.

4. **Clean Git Practices**:
   - Commit logical, atomic changes with descriptive commit messages following Conventional Commits (`feat:`, `fix:`, `refactor:`, `docs:`).

