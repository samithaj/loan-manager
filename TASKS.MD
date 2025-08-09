

# Sprint 0 — Foundations (“living contract”, scaffolding)

**Goal:** Repo + CI, typed API contract, FE/BE shells.

* **Backend (FastAPI)**

  * [x] Create `schema.yml` (OpenAPI 3.1) with `/health`, `/me`.
  * Wire FastAPI project skeleton, env config, Pydantic settings, basic logging, error handler.
    * [x] App factory + `/v1` router; `/health`, `/me` endpoints
    * [x] Pydantic settings for env/config (`LM_` env; `LM_DATABASE_URL`)
    * [x] Basic logging + JSON error handler + correlation ID middleware
    * [x] Users bootstrap API: `POST /v1/users` (demo) + `/v1/me` DB-backed
* **Frontend (Next.js + Tailwind)**

  * [x] App shell, route guards, .env, role-aware layout stubs.
  * [x] Dedicated login page (`/login`) that verifies `/v1/me` and saves creds to `localStorage`.
  * [x] Home simplified; link to `/login`. Hydration warning suppressed at root `<html>`.
* **DevEx**

  * [x] Generate types & client: `openapi-typescript` + `openapi-fetch`.
  * [x] Makefile for concurrent dev (`make dev`) and detached runners (`make up/status/logs/stop`).
  * [x] FE scripts: `dev:full`, `ci` (typegen+lint+build)
  * [x] Backend uses uv-only with `backend/requirements.txt` (Poetry removed)
  * [x] Install PostgreSQL 17 locally via Homebrew
  * [x] Database folder with migrations and seed (`make db` applies)
  * [x] Root `pnpm` scripts for supabase-like workflows (migrations/seed helpers)
  * CI: lint/format/test; pre-commit hooks; Dockerfiles (dev/prod).
  * Observability seed: request ID/correlation ID middleware; log JSON.
* **Best practices to follow**

  * Use OpenAPI as the single source of truth; generate TS types & a typed client to prevent FE/BE drift. ([openapi-ts.dev][1])
  * Keep all traffic over TLS 1.2+; plan to avoid persisting Basic credentials in the browser. (Basic is acceptable **only** over TLS; prefer a server-side proxy or route handlers for the `Authorization` header.) ([OWASP Cheat Sheet Series][2])
  * For Next.js data calls, decide cache behavior per request (`fetch` with revalidate/no-store) instead of global toggles. ([Next.js][3])
  * Include correlation IDs compatible with W3C Trace Context / OpenTelemetry from day one. ([REST API Tutorial][4])

---

# Sprint 1 — Org & reference data (offices, staff, holidays)

**Goal:** Read-only reference screens to unblock later forms.

* **Backend**

  * [x] `/offices`, `/staff`, `/holidays` (GET).
  * [x] Basic CRUD for `/offices`, `/staff`, `/holidays`.
  * Pagination + `sort` implemented consistently. (client-side for now)
* **Frontend**

  * [x] Simple tables with paging/sorting at `/reference`.
  * [x] Holidays CRUD UI (add/edit/delete with optimistic updates); no-refresh updates.
  * [x] Separate pages: `/reference/offices`, `/reference/staff`, `/reference/holidays` with add/edit/delete UIs.
* **Best practices**

  * Consistent pagination/sorting and stable ordering improve API usability. ([Stack Overflow][5])

---

# Sprint 2 — Clients CRUD

**Goal:** First real CRUD + search; sets the validation pattern.

* **Backend**

  * [x] `/clients` list/create; `/clients/{id}` get/update/delete; basic search `q`.
  * Server-side validation (NIC/mobile uniqueness if configured).
* **Frontend**

  * [x] Client list, create/edit/delete, inline validation.
  * [x] Client detail view at `/clients/{id}`.
  * [x] Homepage links to reference and clients pages.
* **Testing**

  * FastAPI `TestClient` + pytest for happy/edge paths. ([FastAPI][6])
* **Best practices**

  * Enforce authorization checks on every object access server-side; never trust client roles alone (avoid BOLA). Use the OWASP Authorization guidance. ([OWASP Cheat Sheet Series][7])

---

# Sprint 3 — Loan products CRUD

**Goal:** Define loan product catalog; unblock loan applications.

* **Backend**

  * [x] `/loan-products` list/create.
  * [x] Validation: interestRate bounds, repaymentFrequency enum.
* **Frontend**

  * [x] Product list & create form.
  * [x] Top header toolbar with authenticated menu; Home shows Login when unauthenticated.
* **Best practices**

  * Keep validation at the server; mirror basic rules client-side only for UX (defense in depth per OWASP). ([martinfowler.com][8])

---

# Sprint 4 — Loans: application → approval → disbursement (core lifecycle)

**Goal:** Strict state machine with idempotent commands.

* **Backend**

  * `/loans` create; `/loans/{id}` get/put (PENDING only).
  * Commands via `/loans/{id}?command=approve|disburse|close` with `Idempotency-Key`.
  * Audit log entries.
* **Frontend**

  * Loan workspace: header, timeline, action drawer for approve/disburse.
* **Best practices**

  * Make POST commands idempotent using an **Idempotency-Key** header (client UUIDs). This allows safe retries and prevents double-approve/disburse. ([Stripe Docs][9], [IETF Datatracker][10])

---

# Sprint 5 — Transactions & receipts (repayment/prepay/etc.)

**Goal:** Money-moving calls produce durable transactions + printable receipts.

* **Backend**

  * `/loans/{id}?command=repayment|prepay|foreclosure|writeoff|waiveInterest|recovery` → returns `{transaction, loan}` with `receiptNumber`.
  * `/loans/{id}/transactions/template?command=…`.
* **Frontend**

  * Payment form + “Print receipt” using react-to-print component.
* **Best practices**

  * Print directly from a dedicated receipt component using **react-to-print** to keep the markup stable. ([Jasper Carpizo][11])
  * Reuse the Idempotency-Key pattern for **all** write commands. ([Stripe Docs][9])

---

# Sprint 6 — Charges

**Goal:** Add/adjust/remove charges; pay charge (cash).

* **Backend**

  * `/loans/{id}/charges` CRUD, `/pay` to post payment (returns a transaction).
* **Frontend**

  * Charge management UI; “Pay charge” flow & receipt.
* **Best practices**

  * Treat charge payment as a first-class transaction with the same idempotent POST discipline. ([Stripe Docs][12])

---

# Sprint 7 — Collateral & vehicle inventory

**Goal:** Attach collateral; simple vehicle inventory; conflict-free allocation.

* **Backend**

  * `/loans/{id}/collaterals` CRUD.
  * `/vehicle-inventory` CRUD; `:allocate`/`:release`.
  * On disbursement, if `vehicleInventoryId` present → atomically `IN_STOCK → SOLD`, else proceed.
  * Use `409 Conflict` on allocation races.
* **Frontend**

  * Inventory table with “Allocate to loan”; loan collateral tab.
* **Best practices**

  * Use **409 Conflict** to signal concurrent allocation/update races; don’t overload 400/500. ([IETF Datatracker][13])

---

# Sprint 8 — Documents (upload/list/download) + file safety

**Goal:** Upload per client/loan with size/type limits.

* **Backend**

  * Multipart uploads; content-type allowlist; 25MB default; optional AV hook.
* **Frontend**

  * Drag-and-drop uploader; preview common types.
* **Best practices**

  * Follow OWASP File Upload guidance: strict allowlist, size limits, AV scanning (e.g., ClamAV), never trust client MIME.

---

# Sprint 9 — Bulk upload (CSV) + Jobs runner

**Goal:** Async ingestion for clients/loans with job status.

* **Backend**

  * `/bulk/clients` & `/bulk/loans` accept CSV → return `202 Accepted {jobId}`.
  * `/jobs/{jobId}` status; batch-only `:run` endpoints for COB & delinquency.
  * Produce per-row success/failure stats.
* **Frontend**

  * Upload wizard; status polling page.
* **Best practices**

  * Use **202 Accepted** + **status endpoint in Location** for long-running work; poll until `SUCCEEDED/FAILED`. ([Microsoft Learn][14])

---

# Sprint 10 — Delinquency buckets & daily classification job

**Goal:** Configurable buckets; show bucket + DPD on loans.

* **Backend**

  * Buckets config; daily job writes `DelinquencyStatus`.
  * Expose on loan read; guard against partial updates.
* **Frontend**

  * Display current bucket on loan cards and details; simple report link.
* **Best practices**

  * Schedule the job off the request path (worker/cron). For long or heavy tasks, use a queue/worker (e.g., Celery/RQ) instead of in-process background tasks. ([Stack Overflow][15])

---

# Sprint 11 — Reschedule (preview → commit, version-checked)

**Goal:** Two-phase reschedule with `previewVersion` token.

* **Backend**

  * `/reschedule/preview` returns schedule + `previewVersion`.
  * `/reschedule/commit` requires `Idempotency-Key` + matching `previewVersion` or 409.
* **Frontend**

  * Side-by-side schedule diff; explicit “Commit” step.
* **Best practices**

  * Keep preview and commit separate to avoid accidental writes; reject commit on drift with 409 (conflict). ([IETF Datatracker][13])

---

# Sprint 12 — Reports (loan portfolio, delinquency) + CSV/JSON export

**Goal:** Parameterized report runner.

* **Backend**

  * `/reports/{loanPortfolio|delinquency}/run?format=JSON|CSV`.
* **Frontend**

  * Simple parameters + “Download CSV” button.
* **Best practices**

  * Keep reports read-only; whitelist params to avoid injection. (OWASP API guidance.) ([martinfowler.com][8])

---

# Sprint 13 — Webhooks v1 (feature-flagged)

**Goal:** Reliable outbound events with signed deliveries.

* **Backend**

  * Outbox table + dispatcher; events: `loan.approved`, `loan.disbursed`, `loan.transaction.posted`, `loan.status.changed`, `loan.delinquency.updated`.
  * Deliveries: HMAC-SHA256 over raw body; retries with backoff; redelivery endpoint.
  * Management endpoints: register/list/delete/test; deliveries list/redeliver.
* **Best practices**

  * Sign webhook payloads and verify on receivers (Stripe popularized this pattern). ([Stripe Docs][16])
  * Make delivery reliable with an **outbox pattern** (write domain change + enqueue delivery in the same DB txn, then a worker pushes). ([microservices.io][17])

---

# Sprint 14 — Observability & hardening pass

**Goal:** Production-ready metrics, traces, logs; auth hardening; performance.

* **Backend**

  * Structured logs (JSON), correlation IDs, metrics & traces (OpenTelemetry).
  * Rate limits on sensitive endpoints; ETag/optimistic locking if applicable.
  * Deployment: Uvicorn behind a process manager (Gunicorn) or platform guidance; container health checks. ([Uvicorn][18])
* **Frontend**

  * Audit display; error boundaries; consistent toast errors.
* **Security**

  * Review Basic Auth handling: ensure HTTPS everywhere; prefer passing credentials to the API from the server (Next.js Route Handlers/proxy) rather than storing in `localStorage`. ([OWASP Cheat Sheet Series][2])

---

## Notes on architecture choices (why this order)

* We start with **read-only reference data** and **clients** to unblock loan submission screens later with minimal coupling.
* All **state-changing** paths adopt **Idempotency-Key** early, so payments/approvals are safe to retry across the app. ([Stripe Docs][9])
* **Bulk + jobs** ship only after core CRUD is stable, using the standard **202 + status** pattern so the FE doesn’t block. ([Microsoft Learn][14])
* **Webhooks** land after transactions exist, implemented via **transactional outbox** for durability. ([microservices.io][17])

---

## “Done” checklist we’ll reuse every sprint

* Contract tests pass against the OpenAPI (FE client compiles + happy-path calls succeed). ([Speakeasy][19])
* Unit + integration tests (pytest + FastAPI TestClient) green. ([FastAPI][6])
* RBAC enforced server-side (no client-only checks). ([OWASP Cheat Sheet Series][7])
* Observability events/logs include `correlationId` and user/role (where allowed). ([REST API Tutorial][4])
* Docs updated in the OpenAPI and FE “how to” page (screenshots of new flows).

---



[1]: https://openapi-ts.dev/?utm_source=chatgpt.com "OpenAPI TypeScript"
[2]: https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Security_Cheat_Sheet.html "Transport Layer Security - OWASP Cheat Sheet Series"
[3]: https://nextjs.org/docs/app/api-reference/functions/fetch?utm_source=chatgpt.com "Functions: fetch"
[4]: https://restfulapi.net/idempotent-rest-apis/?utm_source=chatgpt.com "Idempotency - What is an Idempotent REST API?"
[5]: https://stackoverflow.com/questions/51347704/stripe-verify-web-hook-signature-hmac-sha254-hapi-js?utm_source=chatgpt.com "Stripe verify web-hook signature HMAC sha254 HAPI.js"
[6]: https://fastapi.tiangolo.com/tutorial/testing/?utm_source=chatgpt.com "Testing - FastAPI"
[7]: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html "Authorization - OWASP Cheat Sheet Series"
[8]: https://martinfowler.com/articles/feature-toggles.html?utm_source=chatgpt.com "Feature Toggles (aka Feature Flags)"
[9]: https://docs.stripe.com/api/idempotent_requests?utm_source=chatgpt.com "Idempotent requests | Stripe API Reference"
[10]: https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/?utm_source=chatgpt.com "The Idempotency-Key HTTP Header Field"
[11]: https://jcarpizo.github.io/owasp-info/cheatsheets/Access_Control_Cheat_Sheet.html?utm_source=chatgpt.com "Access Control · OWASP Cheat Sheet Series"
[12]: https://docs.stripe.com/error-low-level?utm_source=chatgpt.com "Advanced error handling"
[13]: https://datatracker.ietf.org/doc/html/rfc7231?utm_source=chatgpt.com "RFC 7231 - Hypertext Transfer Protocol (HTTP/1.1)"
[14]: https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design?utm_source=chatgpt.com "Best practices for RESTful web API design - Azure - Microsoft Learn"
[15]: https://stackoverflow.com/questions/72970534/transactional-outbox-pattern-vs-event-sourcing?utm_source=chatgpt.com "Transactional outbox pattern vs Event Sourcing"
[16]: https://docs.stripe.com/webhooks?utm_source=chatgpt.com "Receive Stripe events in your webhook endpoint"
[17]: https://microservices.io/patterns/microservices.html?utm_source=chatgpt.com "Pattern: Microservice Architecture"
[18]: https://www.uvicorn.org/deployment/?utm_source=chatgpt.com "Deployment"
[19]: https://www.speakeasy.com/blog/contract-testing-with-openapi "Contract testing with OpenAPI | Speakeasy"
