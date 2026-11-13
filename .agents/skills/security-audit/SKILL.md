---
name: security-audit
description: Security auditing, vulnerability prevention, and OWASP secure coding practices for web applications and APIs.
---

# Security Audit & Secure Coding Best Practices

## Overview
This skill provides actionable security guidelines, vulnerability prevention techniques, and audit checklists aligned with OWASP Top 10 standards for backend, frontend, and API development.

## Core Security Principles

### 1. Authentication & Session Management
- **Passwords & Hashes**: Never store plaintext passwords. Always use strong adaptive hashing (Argon2id, bcrypt with sufficient work factor, or PBKDF2).
- **Tokens (JWT)**:
  - Sign tokens with strong asymmetric algorithms (e.g., Ed25519, RS256) or adequately long symmetric secrets (`HS256` with >= 256 bits of entropy).
  - Explicitly verify and enforce `alg` and issuer/audience claims.
  - Store sensitive auth tokens in `HttpOnly`, `Secure`, `SameSite=Strict/Lax` cookies rather than `localStorage` to avoid XSS theft.
- **Session Lifecycle**: Implement token expiration, rotation on privilege changes, and explicit invalidation upon logout.

### 2. Authorization & Access Control (Broken Object-Level Authorization - BOLA / IDOR)
- Never rely on client-supplied IDs without verifying ownership or tenancy:
  ```typescript
  // BAD
  const userRecord = await db.user.findUnique({ where: { id: req.params.id } });

  // GOOD
  const userRecord = await db.user.findFirst({
    where: { id: req.params.id, organizationId: req.user.organizationId }
  });
  ```
- Deny access by default; enforce role-based access control (RBAC) or attribute-based access control (ABAC) at middleware or service layers.

### 3. Injection Prevention
- **SQL / NoSQL Injection**: Always use parameterized queries or trusted ORMs (Prisma, Drizzle, TypeORM). Never concatenate strings into query statements.
- **Command Injection**: Avoid `eval()`, `exec()`, or invoking child processes with unescaped shell strings. Use parameterized APIs like `execFile()` or array-based argument spawning.

### 4. Cross-Site Scripting (XSS) Prevention
- In modern frameworks (React, Next.js, Vue), avoid `dangerouslySetInnerHTML` or `v-html` unless content is thoroughly sanitized with `DOMPurify`.
- Enforce strict Content Security Policy (CSP) headers in HTTP responses.

### 5. Cross-Site Request Forgery (CSRF) Prevention
- For cookie-based stateful authentication, enforce anti-CSRF tokens or configure `SameSite=Strict` / `SameSite=Lax` cookies.
- For custom APIs, require standard or custom headers (e.g., `Authorization: Bearer <token>` or `X-Requested-With`).

### 6. Secrets & Environment Configuration
- Never commit secrets, API keys, service accounts, or `.env` files to git.
- Validate that all required environment variables are present and typed at boot time using schemas (e.g., `zod` or `joi`).
- Mask sensitive data (passwords, tokens, PII) in logs.

### 7. Rate Limiting & Resource Exhaustion (DoS)
- Protect public-facing endpoints (especially auth, password reset, search, and AI completion routes) with rate limiters (e.g., Redis-backed sliding window / Upstash).
- Set payload size limits on incoming JSON and multipart request bodies.
- Enforce pagination limits (never allow unbounded `limit` or `take` queries).

