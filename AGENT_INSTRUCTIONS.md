# AGENT_INSTRUCTIONS.md

Standing rules for every agent working on the **Intelligent Financial Fraud Detection and AML System** (PromptWars 2026). Read this file fully before writing any code. These rules apply on top of the master brief and your department assignment.

Priority order when rules conflict:
1. It works end to end (deployed, demoable, no crashes).
2. It is correct and explainable.
3. It is clean, modular, and maintainable.
4. It feels fast, smooth, and distinctive.
5. It is polished.

Time is short (a few hours). Do not gold-plate. Do not cut anything on the "never cut" list in the master brief.

---

## Part 1: Software engineering practices (all agents)

### 1.1 Core principles

**DRY (Don't Repeat Yourself)**
- If logic appears twice, extract it. Three times is never acceptable.
- One source of truth for each of: thresholds, risk-tier boundaries, weights, feature names, colours, column names, and the transaction schema.
- Constants live in one module (`src/config.py`). No magic numbers scattered in code (`50000`, `0.45`, `85` all belong in config with a name and a comment).
- Feature computation is written once in `build_features(df)` and reused by training, batch scoring, and the real-time path. Training/serving skew is a bug.

**Modularization and separation of concerns**
- One module, one responsibility. A file that does data loading, modelling, and plotting is wrong.
- Layers must not leak: data generation knows nothing about the dashboard; the dashboard never trains a model; detectors never format UI strings.
- Keep pure logic (functions that take data and return data) separate from I/O (files, network, Streamlit/React calls). Pure functions are easy to test and reuse.
- Depend on interfaces, not internals. Other modules call your public function, never reach into your private helpers.

**KISS and YAGNI**
- Choose the simplest approach that meets the requirement. A solid LightGBM beats a fragile deep-learning stack.
- Do not build features nobody asked for. Do not add abstractions for hypothetical futures.

**Other principles**
- **SOLID** where it fits, especially single responsibility and dependency inversion (pass dependencies in, do not hard-code them).
- **Composition over inheritance.** Prefer small functions and dataclasses to class hierarchies.
- **Fail fast, fail loudly.** Validate inputs at module boundaries; raise clear errors with actionable messages. Never swallow exceptions silently.
- **Immutability by default.** Do not mutate input DataFrames or dicts; return new objects (`df = df.copy()` when needed).
- **Determinism.** Every random operation takes a seed from config. Same input produces same output.

### 1.2 Code quality standards

- **Naming:** descriptive, intention-revealing names. `velocity_1h_count` not `v1`. Functions are verbs, data is nouns. Booleans start with `is_`, `has_`, `should_`.
- **Function size:** a function does one thing, ideally under 40 lines. If you need a comment to explain a block, extract it into a named function.
- **Type hints** on all public Python functions. Use `dataclass` or `pydantic` models for the shared schemas instead of loose dicts.
- **Docstrings** on every public function: one line of purpose, inputs, outputs, and any raised errors.
- **Comments explain why, not what.** The code already says what.
- **No dead code**, no commented-out blocks, no leftover `print` debugging. Use the `logging` module.
- **Formatting and linting:** `ruff` (lint and format) for Python; `eslint` and `prettier` for JS/TS. Code must pass with zero warnings before handoff.
- **No global mutable state.** Wrap shared state (like the alert store) in a small class with a clear interface.

### 1.3 Structure and contracts

- Follow the repository layout in the master brief exactly. Do not invent new top-level folders.
- Every module exposes a small, documented public API (`__all__` or a clear entry function) matching the function names in your department section (`build_features`, `predict_fraud_proba`, `score_transaction`, `explain`, and so on).
- Use the **Transaction schema** and **Scoring output schema** from the master brief as typed models in `src/schemas.py`. Everyone imports from there. If you must change a schema, change it in one place and tell the integration agent.
- Configuration through `src/config.py` and environment variables. Never hard-code paths; use `pathlib` and paths derived from the project root.
- Pin dependencies in `requirements.txt` (and `package.json` lockfile for the frontend).

### 1.4 Error handling and robustness

- Validate every external input (API payloads, uploaded CSVs, user filters): types, ranges, required fields, string lengths.
- Handle edge cases explicitly: empty DataFrame, single transaction, new account with no history, missing device or location, zero balance (division by zero), NaN values, timezone-naive vs aware timestamps.
- Cold start rule: a brand-new account must return a sensible score, not a crash. Use population baselines as fallback.
- The UI must never show a raw stack trace. Show a plain message that says what happened and what the user can do.

### 1.5 Testing

Keep tests lean and aimed at what could embarrass us in a demo.
- **Unit tests (pytest)** for: feature functions (no future leakage), each AML detector on a hand-built tiny graph (cycle, structuring, fan-in/out), risk tier boundaries, schema validation.
- **Smoke test** that runs the full pipeline on 500 generated rows and checks the output schema.
- **Model sanity checks:** PR-AUC clearly above the base fraud rate; the time-based split has no overlap.
- Tests must run in under 30 seconds with one command (`pytest -q`).
- Do not mark a task done until its tests pass.

### 1.6 Performance and scalability

- **Vectorize.** No Python `for` loops over DataFrame rows for features. Use pandas/numpy vectorised ops, `groupby().rolling()`, or `transform`.
- Never retrain at app start. Load pre-trained artifacts from `/models`. App cold start target: under 5 seconds.
- Cache expensive computation (`st.cache_data`, `st.cache_resource`, `functools.lru_cache`) with explicit invalidation.
- Use efficient dtypes (`category`, `float32`, parsed datetimes). Keep the demo dataset small enough to load instantly but large enough to be convincing.
- Stream simulator: bounded queue, back-pressure handling, and configurable rate. No unbounded memory growth.
- Document the production path (Kafka/Pub/Sub, feature store, model registry) in the README. Do not build it.

### 1.7 Security, privacy, and responsible AI

- Synthetic data only. Never include real names, numbers, or credentials anywhere.
- No secrets in the repo. Use environment variables and a `.env.example`.
- Mask or hash account IDs in anything user-facing.
- Sanitize and escape any user-supplied text rendered in the UI.
- Do not use protected attributes (religion, caste, gender, and similar) as model features.
- The system recommends; a human analyst decides. Every alert action is written to an audit log.
- Always show model limitations and false-positive trade-offs somewhere visible in the app and the README.

### 1.8 Git and collaboration

- Small, frequent commits with meaningful messages in imperative mood (`Add structuring detector`, not `updates`).
- One branch per department, merged into `main` only when its tests pass. `main` is always runnable.
- Do not touch another department's files without telling the integration agent. If you need a change in their interface, request it; do not patch around it.
- Each department leaves a short `README` section or module docstring covering how to run and test its piece.

### 1.9 Documentation

- Top-level `README.md`: problem, approach, architecture diagram, stack, setup (one command), screenshots, methodology, limitations, privacy and responsible-AI notes, scalability notes, and an acknowledgement of AI-assisted development and third-party libraries (required by the guidelines).
- Keep docs short and accurate. Outdated docs are worse than no docs.

### 1.10 Definition of done (every task)

- [ ] Meets the interface in the department section.
- [ ] No duplicated logic; constants come from config.
- [ ] Types, docstrings, lint, and tests pass.
- [ ] Handles empty, cold-start, and malformed input.
- [ ] No hard-coded paths or secrets.
- [ ] Runs from a clean clone with the documented command.
- [ ] Integrates with the shared schemas without adapters.

---

## Part 2: Frontend and UX standards (Dashboard agents, mainly Department 9)

### 2.1 Stack decision

The dashboard has two acceptable routes. The integration agent chooses one at the start, and all frontend agents follow it.

- **Route A (fastest, Python only):** Streamlit and Plotly, with custom CSS and `streamlit-extras`/components for polish. Choose this if time is very tight.
- **Route B (maximum polish, recommended if time allows):** React (Vite) and TypeScript, Tailwind CSS, with the FastAPI backend serving `/score`, `/alerts`, `/account/{id}`, and a server-sent events or WebSocket stream for the live feed. Deploy the frontend (Vercel/Netlify/Cloud Run static) and the API (Cloud Run/Render/Hugging Face Spaces).

The effects and libraries in sections 2.4 to 2.6 apply to Route B. On Route A, apply the same design principles, the performance rules, and the CSS-only equivalents.

### 2.2 Cross-platform and cross-device requirements (non-negotiable)

The app must work well on:
- **Devices:** phones (360px wide and up), tablets, laptops, and large desktop monitors.
- **Browsers:** current Chrome, Edge, Safari (including iOS Safari), and Firefox.
- **Input:** touch, mouse, and keyboard. Never rely on hover alone. Every hover affordance needs a tap or focus equivalent.
- **Orientation:** portrait and landscape.

Implementation rules:
- **Mobile-first CSS.** Design for the smallest screen, then enhance with breakpoints.
- Use fluid layouts: CSS Grid and Flexbox, `clamp()` for type and spacing, `min()`/`max()`, container queries where useful, `dvh` instead of `vh` (mobile browser bars).
- Touch targets at least 44x44px. Comfortable spacing between interactive elements.
- Respect safe areas (`env(safe-area-inset-*)`) for notched phones.
- **Data-dense views must adapt, not just shrink:**
  - Tables become stacked cards or horizontally scrollable regions with a sticky first column on small screens.
  - Charts resize responsively, simplify on small screens (fewer ticks, no hover-only tooltips), and stay readable.
  - The AML network graph supports pinch-zoom and drag on touch, and offers a simplified list view as a fallback on very small or low-power devices.
  - Navigation is a sidebar on desktop, a bottom tab bar or drawer on mobile.
- Test at 360, 768, 1024, 1440, and 1920 px widths, in a real phone browser (not only dev tools), and on one low-end device or with CPU throttling.
- Use feature detection and progressive enhancement. If a fancy effect is unsupported, fall back gracefully without breaking layout.
- Support dark and light themes via CSS variables and `prefers-color-scheme`, with a manual toggle that persists the choice.

### 2.3 Distinctive design (do not ship generic AI-looking UI)

The product is a **financial-crime analyst's workstation**. It should feel like a serious, precise, trustworthy tool, not a landing-page template. Do the design thinking before coding.

Before building, write a short design plan (in `docs/design.md`):
- **Palette:** 4 to 6 named hex values chosen for this subject (risk semantics matter: Low, Medium, High, Critical must be distinguishable, including for colour-blind users).
- **Type:** one or two typefaces with clear roles and a defined type scale.
- **Layout concept:** a short description and a quick ASCII wireframe for each main view.
- **Principles:** the 3 to 4 ideas that make this UI unique.
- Then review the plan: if any part would be the same for any generic dashboard, change it.

Avoid these tells of generated design:
- A near-black background with a single neon accent as the whole identity, or a cream and terracotta palette.
- Identical rounded cards with the same soft shadow chopping up every page.
- Gradient blobs and glass cards used as decoration with no meaning.
- Tracked-out ALL-CAPS eyebrow labels above every heading.
- One word in a headline set in italic or an accent colour.
- Numbered markers (01, 02, 03) on content that is not a sequence.
- Fade-and-slide-up on every section and a hover lift on every card.
- Generic placeholder copy ("Unlock the power of AI"). Use real, specific content from the fraud/AML domain.

Do instead:
- Let the domain shape the visuals. Think transaction ledgers, risk gauges, flow diagrams, case files, and alert severity ladders. The visual language should come from how analysts actually work.
- Spend boldness in **one** memorable place (for example, the live money-flow network or the risk-timeline view) and keep everything around it quiet and disciplined.
- Use visual structure to carry information: borders, grouping, and density should mean something.
- Write UI copy for analysts in plain language: sentence case, active voice, specific buttons ("Dismiss alert", "Escalate to review"), errors that say what happened and how to fix it, and empty states that tell the user what to do next.
- Keep contrast high, hierarchy clear, and data legible first. Decoration comes last.

### 2.4 Libraries, icons, and effects

Agents are requested to use the following to lift the UI beyond default. Use them with judgement; each must earn its place.

- **React Bits** (reactbits.dev): use selected components for standout moments, such as animated text for the main title or counters, spotlight or aurora-style backgrounds on the hero or empty states, and tasteful interactive elements. Copy only the components you actually use (they are copy-in code, not a heavy dependency), review them for performance, and trim them down.
- **Icons:** one consistent icon set across the app. Use `lucide-react` (or Phosphor/Tabler), never mix sets. Icons carry meaning (risk tier, channel, device, location, pattern type) and always come with accessible labels or tooltips. Use SVG, never icon fonts or raster icons.
- **Motion:** use `motion` (Framer Motion) for layout transitions, list reordering when new alerts arrive, panel open/close, and number counters. Prefer spring physics with short durations (150 to 300 ms for UI feedback). Animate `transform` and `opacity` only.
- **Charts:** Plotly for the analytic views, or `recharts`/`visx`/`d3` for lighter, more custom visuals. Use `react-force-graph` or `cytoscape.js` for the AML network (WebGL/canvas for larger graphs, not SVG with thousands of nodes).
- **Effects to use sparingly and purposefully:**
  - **Motion blur and blur transitions:** a quick blur-in on page or panel transitions, blur on the background behind modals and drawers (`backdrop-filter`), and a brief blur/stretch on fast-changing numbers. Keep blur radii small and durations short.
  - **Glow and pulse** on the single most critical alert, to draw attention exactly where it is needed.
  - **Spotlight/cursor-follow highlights** on desktop only.
  - **Skeleton loaders and shimmer** for loading states, rather than spinners.
  - **Subtle parallax or animated backgrounds** on the landing/overview hero only, never behind dense data.
- Motion must answer a user action or draw attention to a real change (new alert, status change, score update). Do not add motion everywhere. One orchestrated entrance beats scattered effects.

### 2.5 Smoothness and device-adaptive performance (highest frontend priority)

A beautiful UI that stutters is a failed UI. Smoothness beats spectacle.

**Targets**
- 60 fps interactions on mid-range phones. First contentful paint under 1.5 s on a normal connection. Largest contentful paint under 2.5 s. Interaction latency under 100 ms. No layout shift (CLS under 0.1).
- Initial JS bundle as small as reasonably possible. Check with `vite build` and bundle analysis; lazy-load heavy views (graph, model insights).

**Adapt effects to the device and user preference.** Build one small utility (for example `useCapabilities()` in `src/hooks/`) that decides an **effects tier**, and make every animated component read from it instead of deciding on its own (DRY):

| Tier | When | What runs |
|---|---|---|
| Full | Desktop or high-end device, no reduced-motion preference | All effects: blur, glow, spotlight, animated backgrounds, rich transitions |
| Balanced | Mid-range devices or mobile | Core transitions and counters, light blur, no heavy backgrounds or cursor effects |
| Minimal | Low-end device, battery saver, data saver, or `prefers-reduced-motion: reduce` | No decorative motion; instant state changes, simple fades at most, static backgrounds |

Signals to read: `prefers-reduced-motion`, `navigator.hardwareConcurrency`, `navigator.deviceMemory` (where supported), `navigator.connection.saveData` and `effectiveType` (where supported), pointer type (`(pointer: coarse)`), and a measured frame-rate check on first load that can downgrade the tier if the device is struggling. Let users override the tier in a settings menu, and persist the choice.

**Rules**
- Animate only `transform` and `opacity`. Never animate `width`, `height`, `top`, `left`, or `box-shadow` on large areas. Use `will-change` sparingly and remove it after the animation.
- `backdrop-filter` and large `filter: blur()` areas are expensive. Limit them to small, few surfaces, and disable them in Balanced/Minimal tiers.
- Pause or stop animation when the tab is hidden (`visibilitychange`) or the element is off-screen (`IntersectionObserver`). Never run a `requestAnimationFrame` loop that is not needed.
- **Live feed:** batch incoming alerts and render at most once per animation frame or every 250 to 500 ms. Virtualise long lists and tables (`@tanstack/react-virtual`). Cap the DOM at a few hundred rows.
- **Prevent re-render storms:** memoise (`memo`, `useMemo`, `useCallback`) where profiling shows a need, keep state local, split context, and use selectors. Profile with React DevTools before and after.
- Heavy computation (graph layout, large aggregations) goes to a Web Worker or the backend, never the main thread.
- Large graphs: cap the number of rendered nodes, cluster or aggregate, and render the suspicious subgraph first.
- Fonts: self-host, subset, `font-display: swap`, and preload only the primary font. Limit to two families and few weights.
- Images and illustrations: prefer SVG and CSS. If raster is needed, use WebP/AVIF at proper sizes with lazy loading.
- Code-split by route. Defer non-critical libraries until idle.
- Debounce search and filter inputs; throttle scroll and resize handlers.

### 2.6 UX quality bar

- **Clarity first:** the answer to "what needs my attention right now?" must be visible within 3 seconds of opening the app (top alerts, risk counts, one clear call to action).
- **Progressive disclosure:** summary first, details on demand (alert detail panel, expandable reason codes, drill-down from chart to transactions).
- **Every flag is explainable in one glance:** risk score, tier, top 3 reasons in plain language, then SHAP chart and case narrative on expansion.
- **Consistent semantics:** the same colour, icon, and label always mean the same tier or pattern, everywhere.
- **Feedback for every action:** loading skeletons, optimistic updates with undo for review/dismiss, clear success and error states, and toasts that reuse the same verb as the button.
- **Empty, loading, and error states** designed for every view, not left blank.
- **Filtering and search:** by tier, status, pattern type, time range, account, amount. Filters are shareable via the URL.
- **Keyboard support:** logical tab order, visible focus rings, shortcuts for power users (next alert, dismiss, escalate), and an on-screen hint for them.
- **Accessibility (WCAG 2.2 AA):** contrast of at least 4.5:1 for text, never rely on colour alone to show risk (add icon and text label), semantic HTML, ARIA only where needed, screen-reader labels for charts (provide a data table alternative), live regions for new critical alerts, and full support for reduced motion.
- **Demo-readiness:** a one-click "Start demo" that loads pre-seeded data and runs the stream, so judges see value immediately. No login wall. Works on first load on the judges' device.
- Show a short, honest "About this system" panel: synthetic data notice, how scoring works, known limitations.

### 2.7 Frontend engineering rules (DRY and modular applied to UI)

- **Design tokens in one place:** colours, spacing, radii, shadows, durations, easings, and z-index values as CSS variables/Tailwind theme. No hard-coded hex values or pixel values in components.
- **Component hierarchy:** primitives (Button, Badge, Card, Tooltip) then composites (AlertRow, RiskGauge, ReasonList) then views (Overview, Alerts, Network). Primitives are reused everywhere. A new variant is a prop, not a copy.
- One `RiskBadge` component, one `Money` formatter (INR, lakh/crore aware: `₹1,20,000`), one `formatDate` helper, one account-ID masking function. Reuse them.
- One API client module with typed responses generated from or shared with the backend schemas. Components never call `fetch` directly.
- Data fetching with a query library (TanStack Query) for caching, retries, and stale handling. Real-time via a single stream hook that components subscribe to.
- TypeScript strict mode on. No `any` without a comment explaining why.
- Keep components small and focused (aim for under 150 lines). Extract hooks for logic and keep JSX for layout.
- No inline styles for anything reusable. No duplicated media queries; use shared breakpoints/tokens.
- Error boundaries around each major view so one failing widget never blanks the app.

### 2.8 Frontend verification checklist (before handoff)

- [ ] Tested on a real phone and a desktop browser; layouts hold at 360, 768, 1024, 1440, and 1920 px.
- [ ] Works with touch only and with keyboard only.
- [ ] Effects tier switching verified (Full, Balanced, Minimal), including with `prefers-reduced-motion` on.
- [ ] Lighthouse Performance 90 or above and Accessibility 95 or above on mobile profile.
- [ ] No jank with the live feed running at the highest simulated rate for 5 minutes (no memory growth).
- [ ] Dark and light themes both pass contrast checks.
- [ ] No console errors or warnings.
- [ ] Looks specific to this product, not like a template (review against the avoid list in 2.3).
- [ ] A fresh visitor understands the top priority on screen within 3 seconds.

---

## Part 3: Working agreement

- Read the master brief, this file, and your department section before starting.
- Ask the integration agent when an interface or schema is unclear. Do not guess and diverge.
- Prefer a working simple version first, then improve. Never leave `main` broken.
- When you finish, report: what you built, the public functions or components, how to run and test it, known limitations, and anything other agents must know.
- If you are forced to cut scope, cut in the order given in the master brief, and say so in your report.
