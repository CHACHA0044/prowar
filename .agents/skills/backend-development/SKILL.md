---
name: backend-development
description: Clean architecture, API design, data validation, and backend service patterns for scalable applications.
---

# Backend Engineering Best Practices

## Architectural Principles

1. **Separation of Concerns**:
   - **Controllers / Route Handlers**: Handle HTTP protocol concerns (request parsing, response status codes, header formatting).
   - **Services / Use Cases**: Encapsulate domain and business logic independent of transport protocol.
   - **Data Access Layer**: Repositories or ORM queries isolate database access.

2. **Strict Request & Response Validation**:
   - Parse and validate every incoming payload at the system boundary using runtime schema validators (e.g., Zod, Valibot, or Joi).
   ```typescript
   import { z } from 'zod';

   export const CreateItemSchema = z.object({
     title: z.string().min(1).max(100),
     tags: z.array(z.string()).default([]),
   });
   ```

3. **Graceful Error Handling**:
   - Avoid generic 500 error cascades. Distinguish operational errors (bad user inputs, resource not found) from programmer errors (null reference, unhandled rejection).
   - Use centralized error-handling middleware. Do not leak stack traces or internal implementation details to clients in production.

4. **Database & Transaction Management**:
   - Group multi-step mutations in database transactions to ensure consistency.
   - Index query columns frequently filtered in `WHERE`, `ORDER BY`, or `JOIN` conditions.
   - Use pooling for database connections to avoid exhausting connection limits.

5. **Observability & Logging**:
   - Use structured logging (JSON) with log levels (`debug`, `info`, `warn`, `error`).
   - Attach correlation/trace IDs (`X-Request-Id`) across request flows for rapid debugging.

