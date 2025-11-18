# Use Cases (derived from BUSINESS_REQUIREMENTS.md)

## Actors
- **Loan Officer**: Creates, approves, disburses loans; reschedules; closes loans
- **Teller / Collections Officer**: Posts payments (repayment/prepay/recovery), pays charges; prints receipts
- **Operations Engineer**: Runs batch jobs (COB, delinquency); monitors job status
- **System Administrator**: Manages users/roles; reference data (offices, staff, holidays); config

## Conventions
- All state-changing POSTs require `Idempotency-Key` for safe retries.
- Server enforces RBAC; UI guards are UX only.
- JWT via HttpOnly cookies; `/v1/me` used across UI.

---

## 1. Authentication
- **Goal**: Sign in/out; access current user
- **Main flow**: Login → server sets HttpOnly tokens → UI shows role-aware navigation → `/v1/me` returns `{username, roles}`; logout clears cookies
- **Edge**: Invalid credentials (401); expired/invalid token (401); roles missing (403 on protected pages)
- **Success**: User can access permitted pages; unauthorized redirected to Login

## 2. Clients
- **Goal**: Manage clients; view details and linked loans
- **Main flow**: List + search; create/edit/delete; view `/clients/{id}`; quick actions for linked loans
- **Edge**: Duplicate IDs/NIC/phone (409 if enforced); not found (404)
- **Success**: Clients persist; searchable; consistent CRUD

## 3. Loan Products
- **Goal**: Define loan product catalog
- **Main flow**: List + create; validate `interestRate` and `repaymentFrequency`
- **Edge**: Duplicate product id (409); invalid frequency/rate (400)
- **Success**: Products available for loan creation dropdowns

## 4. Loans Lifecycle (Application → Approval → Disbursement → Close)
- **Goal**: Strict state transitions
- **Main flow**:
  - Create loan (PENDING) with client, product, principal, term; optional interestRate
  - Approve (PENDING → APPROVED)
  - Disburse (APPROVED → DISBURSED), set `disbursedOn`; optional auto-allocate vehicle inventory
  - Close (DISBURSED → CLOSED)
- **Edge**: Invalid state transitions (409); missing Idempotency-Key (400); not found (404)
- **Success**: State machine enforced; actions idempotent

## 5. Transactions & Receipts
- **Goal**: Record money-moving events with printable receipts
- **Main flow**: Repayment / Prepay / Foreclosure / Write-off / Waive Interest / Recovery → returns `{transaction, loan}` incl. `receiptNumber`; UI prints receipt
- **Edge**: Invalid amounts/dates; out-of-order posting; insufficient state (e.g., not DISBURSED)
- **Success**: Durable transaction linked to loan; receipt printable

## 6. Charges
- **Goal**: Manage charges and payments
- **Main flow**: List/add/update/delete charges; pay charge (CASH) → creates transaction
- **Edge**: Double pay (idempotency prevents duplicates); invalid status transitions
- **Success**: Accurate charge lifecycle; payments reflected in transactions

## 7. Collateral & Vehicle Inventory
- **Goal**: Track collateral; manage vehicle inventory for sales financing
- **Main flow**: Add/modify/remove collateral; list inventory; allocate/release; on disbursement with `vehicleInventoryId` → atomically mark SOLD and link
- **Edge**: Allocation races (409); release non-allocated (409); disburse without allocation (allowed if other collateral present)
- **Success**: No double-allocation; consistent inventory status

## 8. Documents
- **Goal**: Upload/list/download
- **Main flow**: Upload per client/loan (multipart) with size/type limits; list; download
- **Edge**: Oversized/invalid types; optional AV scan failure
- **Success**: Safe document handling; audit-friendly

## 9. Delinquency
- **Goal**: Classify loans into buckets daily
- **Main flow**: Configure buckets; daily job writes `DelinquencyStatus`; surface bucket and DPD on loan reads
- **Edge**: Partial updates avoided; job idempotent
- **Success**: Accurate bucket/DPD visible in UI

## 10. Reports
- **Goal**: Run read-only reports (loan portfolio, delinquency)
- **Main flow**: Parameterized `GET /reports/{name}/run?format=JSON|CSV` → UI download
- **Edge**: Invalid params rejected; large outputs streamed
- **Success**: Reliable report outputs in chosen format

## 11. Bulk Upload (CSV)
- **Goal**: Async ingestion for clients/loans
- **Main flow**: Upload CSV → 202 Accepted `{jobId}`; poll `/jobs/{jobId}` until `SUCCEEDED/FAILED`; show per-row stats
- **Edge**: Malformed rows; partial success; retries
- **Success**: Large batches processed safely with visibility

## 12. Jobs Runner
- **Goal**: Trigger batch-only operations (COB, delinquency)
- **Main flow**: POST `/jobs/{name}:run` (batch host only) → returns `{jobId}`; track `/jobs/{jobId}`
- **Edge**: Concurrency control; backoffs; failure reporting
- **Success**: Jobs trackable with clear lifecycle

## 13. Reschedule (Preview → Commit)
- **Goal**: Two-phase schedule change with drift protection
- **Main flow**: Preview → `schedule` + `previewVersion`; Commit with `previewVersion` + Idempotency-Key
- **Edge**: Version mismatch (409); loan state changed
- **Success**: Safe, explicit rescheduling

## 14. Webhooks (Feature-flagged)
- **Goal**: Outbound events for integrations
- **Main flow**: Register/list/delete webhooks; dispatcher delivers signed events; redeliver attempts
- **Edge**: Delivery retries; signature validation failures; de-dup by eventId
- **Success**: Reliable events for `loan.approved|disbursed|transaction.posted|status.changed|delinquency.updated`

## 15. Admin & Reference Data
- **Goal**: Offices, staff, holidays; users/roles
- **Main flow**: CRUD for reference data; minimal user management; CORS/observability configured
- **Edge**: Duplicates (409); validation errors
- **Success**: Stable org setup that supports all flows



