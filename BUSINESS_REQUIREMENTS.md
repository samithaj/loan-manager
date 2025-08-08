 

==== main_document =====
---

# Executive summary (Loans-focused)

**Loan Manager** is a single-tenant lending platform with:

 * **Backend:** Python **FastAPI** (HTTP Basic Auth) exposing open APIs for client/loan lifecycle, loan actions (repay, prepay, foreclosure, write-off, waive interest, recovery), charges, collateral (incl. vehicle inventory), documents (incl. bulk upload), delinquency buckets & daily classification job, schedule preview/reschedule, receipts, and minimal reporting.
* **Frontend:** **Next.js + Tailwind CSS**, role-aware UI for loan officers, tellers/collections, and admins, featuring loan workspaces, action drawers, printable receipts (react-to-print), and report runners.
* **“Living contract”:** One **OpenAPI** spec used by FastAPI and auto-generated FE types/clients—so the UI and API never drift.

---

# Context & personas (Loans)

* **Loan Officer**: Creates/approves/disburses loans; handles reschedules and closures.
* **Teller / Collections Officer**: Records repayments, prepayments, recovery, charge payments; prints receipts.
* **Operations Engineer**: Runs daily jobs (COB, delinquency classification), monitors batch status.
* **System Administrator**: Manages users/roles, offices/staff, holidays, currencies, payment types.

---

# Scope (Loans)

## In scope

* **Auth:** HTTP Basic (over TLS). Single tenant (no tenant selector).
* **Clients:** Create/edit/view; link to loans; bulk upload CSV.
* **Loan products:** Terms, rates, repayment schedule rules.
* **Loans:** Application → approval → disbursement → transactions; schedule preview/reschedule; closure.
* **Loan actions:** repayment, prepay, foreclosure, write-off, waive interest, recovery payment.
* **Charges:** Add/adjust/remove; pay charge (cash only).
* **Collateral:** Simple collateral (land, existing vehicle) **plus** basic **vehicle inventory** model for new vehicle (e.g., bicycle) sales financing.
* **Documents:** Upload/download (per loan & per client), preview common types; **bulk upload** for loans/clients CSV.
* **Delinquency:** Configurable buckets; daily classification job; display bucket on loans.
* **Reports:** Minimal runner: loan portfolio/delinquency; CSV/JSON.
* **Jobs:** Start/track batch jobs (COB, delinquency), restricted to a “batch” process.
* **Org data:** Offices, staff, holidays; **currency fixed to LKR**; **payment type fixed to CASH**.
* **Receipts:** Repayment payload returns `receiptNumber`; FE prints via react-to-print.

## Out of scope

* Multi-tenant, savings/deposits/shares, accounting module, payment gateways, KYC/AML, SMS/marketing.

---

# User stories & acceptance criteria (Loans subset)

| ID   | Story                                                    | Acceptance Criteria                                                                 | Priority |
| ---- | -------------------------------------------------------- | ----------------------------------------------------------------------------------- | -------- |
| L-1  | As a user, I sign in with Basic auth                     | Valid creds → 200; otherwise 401; session persisted in browser securely             | High     |
| L-2  | As a user, I create/edit/view clients                    | CRUD with validation; duplicates prevented by NIC/phone if configured               | High     |
| L-3  | As a user, I bulk upload clients/loans                   | Upload CSV → job ID; status shows success/failure per row                           | High     |
| L-4  | As a loan officer, I submit/approve/disburse loans       | Status transitions enforced; audit logged                                           | High     |
| L-5  | As a teller, I post repayments and print receipts        | Response includes `receiptNumber`; printable receipt generated                      | High     |
| L-6  | As a user, I perform loan actions                        | Prepay/foreclosure/write-off/waiveInterest/recovery succeed with correct validation | High     |
| L-7  | As a user, I manage charges                              | Add/update/remove; pay charge in CASH mode only                                     | High     |
| L-8  | As a user, I manage collateral (incl. vehicle inventory) | Add vehicle inventory entry or attach simple collateral types                       | Medium   |
| L-9  | As a user, I upload loan/client documents                | Multipart upload; list/download/preview; size/type limits                           | Medium   |
| L-10 | As ops, I run COB & delinquency job                      | Start job; poll status; errors logged; no partial data corruption                   | Medium   |
| L-11 | As a user, I reschedule a loan                           | Preview new schedule before commit; irreversible when committed                     | Medium   |
| L-12 | As a user, I run basic reports                           | Parameterized report runner; CSV/JSON export                                        | Medium   |
| L-13 | As a loan officer, vehicle auto-allocates on disburse (when applicable) | If `vehicleInventoryId` provided or pre-allocated, disburse atomically links item → SOLD and to the loan; otherwise proceed using other collateral | Medium   |

---

# Functional overview (Loans)

* **Auth & Roles:** Basic auth; RBAC (view/create/approve/disburse/postTransaction/manageCharges/manageCollateral/manageDocuments/runJobs/runReports/admin) with granular reschedule permissions: `loan.reschedule.preview` and `loan.reschedule.commit`.
* **Clients & Loans:** Linked lifecycle; strict status transitions; idempotent state-changing calls.
* **Transactions & Receipts:** All value-changing actions produce durable transactions with `receiptNumber`.
* **Collateral:** Simple schema + vehicle inventory entity for retail vehicle (e.g., bicycle) financing.
* **Documents:** Multipart storage with virus-scan hook option; signed download URLs optional.
* **Delinquency:** Config buckets; daily job; surface current bucket + days past due.
* **Reports:** Read-only runner with whitelisted parameters; no SQL exposure to FE.
* **Jobs:** Async, tracked via `/jobs/{jobId}`; only available on batch host (config flag).
* **Vehicle inventory allocation:** Optional auto-allocation on **disbursement** when a `vehicleInventoryId` is provided (or pre-allocated to the loan). If other collateral (LAND/VEHICLE) is present and no inventory item is selected, disbursement still proceeds. Inventory state changes are atomic within the disbursement transaction: `IN_STOCK → ALLOCATED (optional reserve) → SOLD`. Concurrency conflicts return `409`.

---

# Interfaces & integrations (Loans subset)

* **HTTP JSON APIs** (OpenAPI below) over TLS.
* **CSV bulk ingestion** endpoints (multipart) producing async jobs.
* **Webhooks (optional later):** Outbound event posts on loan state changes.
* **Printing:** FE uses **react-to-print** for receipt components.

---

## Why you need webhooks

- **Real-time integrations without polling:** notify external systems when a loan is approved/disbursed/paid.
- **Receipts & customer comms:** trigger a small service to print a receipt or send SMS/WhatsApp on `loan.transaction.posted`.
- **Ops & analytics:** stream events into a warehouse/log sink; reconcile cash, monitor delinquency changes.
- **Safer than direct coupling:** keep your core API clean; partners subscribe to events you choose to expose.
- **Auditability:** immutable event log + delivery history = easier investigations.

### My recommendation

Ship a minimal, feature-flagged webhook layer now:

- **Events (v1):** `loan.approved`, `loan.disbursed`, `loan.transaction.posted`, `loan.status.changed`, `loan.delinquency.updated`.
- **Outbox pattern** in DB → signed HTTP POST deliveries (HMAC-SHA256 over body).
- **Retries** with backoff; **replay** endpoint; **delivery log**.

Delivery request (example):

```json
{
  "eventId": "evt_123",
  "eventType": "loan.transaction.posted",
  "occurredAt": "2025-08-08T09:15:00Z",
  "tenant": "single",
  "data": {
    "loanId": "LN-00123",
    "transaction": {
      "id": "TX-987",
      "type": "REPAYMENT",
      "amount": 12500,
      "date": "2025-08-08",
      "receiptNumber": "RCPT-5567"
    }
  }
}
```

Headers: `X-LM-Event-ID`, `X-LM-Event-Type`, `X-LM-Timestamp`, `X-LM-Signature` (HMAC-SHA256 over body).

Retry policy: 0s → 30s → 2m → 10m → 1h (max 5). Timeout 5s.

Idempotency: receivers must de-dupe by `eventId`.

### OpenAPI additions (concise)

- `POST /webhooks` – register a target URL & secret
- `GET /webhooks` / `DELETE /webhooks/{id}`
- `POST /webhooks/{id}:test` – send a sample event
- `GET /webhooks/deliveries?webhookId=…` – list recent attempts
- `POST /webhooks/deliveries/{deliveryId}:redeliver` – manual retry

# Data model (Loans)

**Core entities**

* **Client** `{id, displayName, mobile, nationalId, address, …}`
* **LoanProduct** `{id, name, interestRate, termMonths, repaymentFrequency, penaltyRules, …}`
* **LoanAccount** `{id, clientId, productId, principal, interestRate, termMonths, status, disbursedOn, schedule[], delinquencyStatus, collateral[], …}`
* **LoanTransaction** `{id, loanId, type, amount, date, receiptNumber, postedBy, …}`
* **LoanCharge** `{id, loanId, name, amount, dueDate, status}`
* **Collateral** `{id, loanId, type (VEHICLE|LAND), details:{…}, value}`
* **VehicleInventory** `{id, vinOrFrameNumber, brand, model, color, plate?, purchasePrice, msrp, status (IN_STOCK|ALLOCATED|SOLD), linkedLoanId?}`
* **Document** `{id, ownerType (CLIENT|LOAN), ownerId, name, mimeType, size, uploadedOn}`
* **DelinquencyBucket** `{id, name, minDays, maxDays}`
* **DelinquencyStatus** `{loanId, currentBucketId, daysPastDue, asOfDate}`
* **Office**, **Staff**, **Holiday**
* **Currency**: fixed config `{code:"LKR", name:"Sri Lankan Rupee", decimals:2}`
* **PaymentType**: fixed config `{code:"CASH", name:"Cash"}`

---

# Non-functional requirements (Loans)

* **Security:** TLS 1.2+; HTTP Basic only; RBAC; audit logs for state-changing actions.
* **Reliability:** Idempotency via `Idempotency-Key` on POST commands (dedupe window 24h); optimistic locking (ETag).
* **Observability:** Structured logs, metrics; job/command traces; error correlation IDs.
* **Performance:** P95 < 300ms for reads, < 800ms for writes under reference load; batch jobs schedulable.
* **Pagination:** `page`, `pageSize` (max 200), `sort`.
* **Validation:** Strong server-side validation; safe defaults; rate limiting on sensitive endpoints.
* **Files:** Max 25MB per document by default; content-type allowlist; virus-scan hook.
* **Localization:** UI text only (no currency switching); numbers/dates localized.

---

# Living API contract

Below is the **OpenAPI 3.1** spec that both FastAPI and Next.js will consume. This is the single source of truth.

> **How FE stays in sync (recommended):**
>
> * Generate types: `openapi-typescript schema.yml -o src/types/api.d.ts`
> * Create a thin client with `openapi-fetch` or `orval` using this spec.
> * Use those types in your Next.js data layer (see snippet after YAML).

```yaml
openapi: 3.1.0
info:
  title: Loan Manager API
  version: 1.0.0
  description: Single-tenant loans-only API for Loan Manager (FastAPI backend).
servers:
  - url: https://api.loanmanager.local/v1
security:
  - basicAuth: []
components:
  securitySchemes:
    basicAuth:
      type: http
      scheme: basic
  parameters:
    Page:
      name: page
      in: query
      schema: { type: integer, minimum: 1, default: 1 }
    PageSize:
      name: pageSize
      in: query
      schema: { type: integer, minimum: 1, maximum: 200, default: 25 }
    Sort:
      name: sort
      in: query
      schema: { type: string, description: "e.g. createdOn,desc" }
    IdempotencyKey:
      name: Idempotency-Key
      in: header
      schema: { type: string }
      description: "Provide for state-changing POSTs to ensure idempotency."
  headers:
    X-LM-Event-ID:
      description: Unique event id for idempotency at receivers
      schema: { type: string }
    X-LM-Event-Type:
      description: Event type name
      schema:
        type: string
        enum: [loan.approved, loan.disbursed, loan.transaction.posted, loan.status.changed, loan.delinquency.updated]
    X-LM-Timestamp:
      description: Event creation time (server clock)
      schema: { type: string, format: date-time }
    X-LM-Signature:
      description: HMAC-SHA256 (hex) over raw request body using the webhook's secret
      schema: { type: string }
  schemas:
    Error:
      type: object
      required: [code, message]
      properties:
        code: { type: string }
        message: { type: string }
        correlationId: { type: string }
    Client:
      type: object
      required: [id, displayName]
      properties:
        id: { type: string }
        displayName: { type: string }
        mobile: { type: string, nullable: true }
        nationalId: { type: string, nullable: true }
        address: { type: string, nullable: true }
        createdOn: { type: string, format: date-time }
    ClientCreate:
      type: object
      required: [displayName]
      properties:
        displayName: { type: string }
        mobile: { type: string, nullable: true }
        nationalId: { type: string, nullable: true }
        address: { type: string, nullable: true }
    LoanProduct:
      type: object
      required: [id, name, interestRate, termMonths, repaymentFrequency]
      properties:
        id: { type: string }
        name: { type: string }
        interestRate: { type: number }
        termMonths: { type: integer }
        repaymentFrequency: { type: string, enum: [WEEKLY, BIWEEKLY, MONTHLY] }
        penaltyRules: { type: object, additionalProperties: true, nullable: true }
    LoanAccount:
      type: object
      required: [id, clientId, productId, principal, status]
      properties:
        id: { type: string }
        clientId: { type: string }
        productId: { type: string }
        principal: { type: number }
        interestRate: { type: number }
        termMonths: { type: integer }
        status: { type: string, enum: [PENDING, APPROVED, DISBURSED, CLOSED, WRITTEN_OFF] }
        disbursedOn: { type: string, format: date, nullable: true }
        delinquencyStatus: { $ref: '#/components/schemas/DelinquencyStatus' }
        collateral: 
          type: array
          items: { $ref: '#/components/schemas/Collateral' }
        schedule:
          type: array
          items: { $ref: '#/components/schemas/ScheduleInstallment' }
    ScheduleInstallment:
      type: object
      required: [period, dueDate, principalDue, interestDue, totalDue, paid]
      properties:
        period: { type: integer }
        dueDate: { type: string, format: date }
        principalDue: { type: number }
        interestDue: { type: number }
        totalDue: { type: number }
        paid: { type: boolean }
    ScheduleChangeRequest:
      type: object
      description: "e.g. {rescheduleFromDate, newInterestRate, extraTerms}"
      additionalProperties: true
    SchedulePreviewResponse:
      type: object
      required: [schedule, previewVersion]
      properties:
        previewVersion: { type: string }
        schedule:
          type: array
          items: { $ref: '#/components/schemas/ScheduleInstallment' }
    LoanTransaction:
      type: object
      required: [id, loanId, type, amount, date, receiptNumber]
      properties:
        id: { type: string }
        loanId: { type: string }
        type: { type: string, enum: [REPAYMENT, PREPAYMENT, FORECLOSURE, WRITE_OFF, WAIVE_INTEREST, RECOVERY] }
        amount: { type: number }
        date: { type: string, format: date }
        receiptNumber: { type: string }
        postedBy: { type: string, nullable: true }
    LoanCharge:
      type: object
      required: [id, loanId, name, amount, status]
      properties:
        id: { type: string }
        loanId: { type: string }
        name: { type: string }
        amount: { type: number }
        dueDate: { type: string, format: date, nullable: true }
        status: { type: string, enum: [PENDING, PAID, WAIVED] }
    Collateral:
      type: object
      required: [id, type, value]
      properties:
        id: { type: string }
        type: { type: string, enum: [VEHICLE, LAND] }
        value: { type: number }
        details:
          type: object
          description: "For VEHICLE: inventoryId (if from inventory), plate, vin or frameNumber; LAND: deedNo, location."
          additionalProperties: true
    VehicleInventory:
      type: object
      required: [id, brand, model, status]
      properties:
        id: { type: string }
        vinOrFrameNumber: { type: string }
        brand: { type: string }
        model: { type: string }
        plate: { type: string, nullable: true }
        color: { type: string, nullable: true }
        purchasePrice: { type: number, nullable: true }
        msrp: { type: number, nullable: true }
        status: { type: string, enum: [IN_STOCK, ALLOCATED, SOLD] }
        linkedLoanId: { type: string, nullable: true }
    Document:
      type: object
      required: [id, ownerType, ownerId, name, mimeType, size, uploadedOn]
      properties:
        id: { type: string }
        ownerType: { type: string, enum: [CLIENT, LOAN] }
        ownerId: { type: string }
        name: { type: string }
        mimeType: { type: string }
        size: { type: integer }
        uploadedOn: { type: string, format: date-time }
    DelinquencyBucket:
      type: object
      required: [id, name, minDays, maxDays]
      properties:
        id: { type: string }
        name: { type: string }
        minDays: { type: integer }
        maxDays: { type: integer }
    DelinquencyStatus:
      type: object
      required: [currentBucketId, daysPastDue, asOfDate]
      properties:
        currentBucketId: { type: string }
        daysPastDue: { type: integer }
        asOfDate: { type: string, format: date }
    Office:
      type: object
      properties:
        id: { type: string }
        name: { type: string }
    Staff:
      type: object
      properties:
        id: { type: string }
        name: { type: string }
        role: { type: string }
    Holiday:
      type: object
      properties:
        id: { type: string }
        name: { type: string }
        date: { type: string, format: date }
    Currency:
      type: object
      properties:
        code: { type: string, enum: [LKR] }
        name: { type: string, default: "Sri Lankan Rupee" }
        decimals: { type: integer, default: 2 }
    PaymentType:
      type: object
      properties:
        code: { type: string, enum: [CASH] }
        name: { type: string, default: "Cash" }

    # Webhooks
    Webhook:
      type: object
      required: [id, url, active, createdOn]
      properties:
        id: { type: string }
        url: { type: string, format: uri }
        secret:
          type: string
          writeOnly: true
          description: "HMAC secret used to sign deliveries."
        active: { type: boolean, default: true }
        createdOn: { type: string, format: date-time }
    WebhookCreate:
      type: object
      required: [url, secret]
      properties:
        url: { type: string, format: uri }
        secret: { type: string }
    WebhookDelivery:
      type: object
      required: [id, webhookId, eventId, eventType, status, attemptCount]
      properties:
        id: { type: string }
        webhookId: { type: string }
        eventId: { type: string }
        eventType:
          type: string
          enum: [loan.approved, loan.disbursed, loan.transaction.posted, loan.status.changed, loan.delinquency.updated]
        status: { type: string, enum: [PENDING, DELIVERED, FAILED] }
        attemptCount: { type: integer }
        lastAttemptAt: { type: string, format: date-time, nullable: true }
        lastResponseStatus: { type: integer, nullable: true }
        lastError: { type: string, nullable: true }
    WebhookEvent:
      type: object
      required: [eventId, eventType, occurredAt, tenant, data]
      properties:
        eventId: { type: string }
        eventType:
          type: string
          enum: [loan.approved, loan.disbursed, loan.transaction.posted, loan.status.changed, loan.delinquency.updated]
        occurredAt: { type: string, format: date-time }
        tenant: { type: string, description: "Tenant identifier; 'single' in this deployment." }
        data:
          description: "Event-specific payload. See event data schemas."
          oneOf:
            - $ref: '#/components/schemas/LoanApprovedEventData'
            - $ref: '#/components/schemas/LoanDisbursedEventData'
            - $ref: '#/components/schemas/LoanTransactionPostedEventData'
            - $ref: '#/components/schemas/LoanStatusChangedEventData'
            - $ref: '#/components/schemas/LoanDelinquencyUpdatedEventData'
    # Event data payloads
    LoanApprovedEventData:
      type: object
      required: [loanId]
      properties:
        loanId: { type: string }
    LoanDisbursedEventData:
      type: object
      required: [loanId]
      properties:
        loanId: { type: string }
    LoanTransactionPostedEventData:
      type: object
      required: [loanId, transaction]
      properties:
        loanId: { type: string }
        transaction: { $ref: '#/components/schemas/LoanTransaction' }
    LoanStatusChangedEventData:
      type: object
      required: [loanId, fromStatus, toStatus]
      properties:
        loanId: { type: string }
        fromStatus: { type: string, enum: [PENDING, APPROVED, DISBURSED, CLOSED, WRITTEN_OFF] }
        toStatus: { type: string, enum: [PENDING, APPROVED, DISBURSED, CLOSED, WRITTEN_OFF] }
    LoanDelinquencyUpdatedEventData:
      type: object
      required: [loanId, delinquencyStatus]
      properties:
        loanId: { type: string }
        delinquencyStatus: { $ref: '#/components/schemas/DelinquencyStatus' }

webhooks:
  eventDelivery:
    post:
      summary: Outbound webhook event delivery to subscriber URLs
      description: |
        The platform sends signed HTTP POSTs to registered webhook URLs with HMAC-SHA256 over the raw body using the subscriber's secret.
        Retry policy: 0s → 30s → 2m → 10m → 1h (max 5). Timeout 5s. Any 2xx is considered success.
      parameters:
        - name: X-LM-Event-ID
          in: header
          required: true
          schema: { type: string }
        - name: X-LM-Event-Type
          in: header
          required: true
          schema:
            type: string
            enum: [loan.approved, loan.disbursed, loan.transaction.posted, loan.status.changed, loan.delinquency.updated]
        - name: X-LM-Timestamp
          in: header
          required: true
          schema: { type: string, format: date-time }
        - name: X-LM-Signature
          in: header
          required: true
          schema: { type: string }
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/WebhookEvent' }
            examples:
              transactionPosted:
                summary: loan.transaction.posted payload
                value:
                  eventId: evt_123
                  eventType: loan.transaction.posted
                  occurredAt: 2025-08-08T09:15:00Z
                  tenant: single
                  data:
                    loanId: LN-00123
                    transaction:
                      id: TX-987
                      loanId: LN-00123
                      type: REPAYMENT
                      amount: 12500
                      date: 2025-08-08
                      receiptNumber: RCPT-5567
      responses:
        '200': { description: Acknowledged }

paths:
  /health:
    get:
      summary: Health check
      responses:
        '200': { description: OK }

  /me:
    get:
      summary: Get current user profile (Basic auth)
      responses:
        '200':
          description: Current user
          content:
            application/json:
              schema:
                type: object
                properties:
                  username: { type: string }
                  roles: { type: array, items: { type: string } }
        '401': { description: Unauthorized, content: { application/json: { schema: { $ref: '#/components/schemas/Error' } } } }

  # Clients
  /clients:
    get:
      summary: List clients
      parameters: [ { $ref: '#/components/parameters/Page' }, { $ref: '#/components/parameters/PageSize' }, { $ref: '#/components/parameters/Sort' }, { name: q, in: query, schema: { type: string } } ]
      responses:
        '200':
          description: Paged clients
          content:
            application/json:
              schema:
                type: object
                properties:
                  items: { type: array, items: { $ref: '#/components/schemas/Client' } }
                  page: { type: integer }
                  pageSize: { type: integer }
                  total: { type: integer }
    post:
      summary: Create client
      requestBody:
        required: true
        content: { application/json: { schema: { $ref: '#/components/schemas/ClientCreate' } } }
      responses:
        '201': { description: Created, content: { application/json: { schema: { $ref: '#/components/schemas/Client' } } } }

  /clients/{clientId}:
    get:
      summary: Get client
      parameters: [ { name: clientId, in: path, required: true, schema: { type: string } } ]
      responses:
        '200': { description: Client, content: { application/json: { schema: { $ref: '#/components/schemas/Client' } } } }
    put:
      summary: Update client
      parameters: [ { name: clientId, in: path, required: true, schema: { type: string } } ]
      requestBody:
        required: true
        content: { application/json: { schema: { $ref: '#/components/schemas/ClientCreate' } } }
      responses:
        '200': { description: Updated, content: { application/json: { schema: { $ref: '#/components/schemas/Client' } } } }

  /clients/{clientId}/accounts:
    get:
      summary: List client loans
      parameters: [ { name: clientId, in: path, required: true, schema: { type: string } } ]
      responses:
        '200':
          description: Loans for client
          content:
            application/json:
              schema:
                type: array
                items: { $ref: '#/components/schemas/LoanAccount' }

  # Loan products
  /loan-products:
    get:
      summary: List loan products
      responses:
        '200':
          description: Loan products
          content:
            application/json:
              schema:
                type: array
                items: { $ref: '#/components/schemas/LoanProduct' }
    post:
      summary: Create loan product
      requestBody:
        required: true
        content: { application/json: { schema: { $ref: '#/components/schemas/LoanProduct' } } }
      responses:
        '201': { description: Created, content: { application/json: { schema: { $ref: '#/components/schemas/LoanProduct' } } } }

  # Loans
  /loans:
    get:
      summary: List loans
      parameters: [ { $ref: '#/components/parameters/Page' }, { $ref: '#/components/parameters/PageSize' }, { $ref: '#/components/parameters/Sort' }, { name: clientId, in: query, schema: { type: string } }, { name: status, in: query, schema: { type: string } } ]
      responses:
        '200':
          description: Paged loans
          content:
            application/json:
              schema:
                type: object
                properties:
                  items: { type: array, items: { $ref: '#/components/schemas/LoanAccount' } }
                  page: { type: integer }
                  pageSize: { type: integer }
                  total: { type: integer }
    post:
      summary: Submit loan application
      parameters: [ { $ref: '#/components/parameters/IdempotencyKey' } ]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [clientId, productId, principal, termMonths]
              properties:
                clientId: { type: string }
                productId: { type: string }
                principal: { type: number }
                interestRate: { type: number, nullable: true }
                termMonths: { type: integer }
                collateral: { type: array, items: { $ref: '#/components/schemas/Collateral' }, nullable: true }
      responses:
        '201': { description: Created, content: { application/json: { schema: { $ref: '#/components/schemas/LoanAccount' } } } }

  /loans/{loanId}:
    get:
      summary: Get loan
      parameters: [ { name: loanId, in: path, required: true, schema: { type: string } } ]
      responses:
        '200': { description: Loan, content: { application/json: { schema: { $ref: '#/components/schemas/LoanAccount' } } } }
    put:
      summary: Update loan (only when PENDING)
      parameters: [ { name: loanId, in: path, required: true, schema: { type: string } }, { $ref: '#/components/parameters/IdempotencyKey' } ]
      requestBody:
        required: true
        content: { application/json: { schema: { $ref: '#/components/schemas/LoanAccount' } } }
      responses:
        '200': { description: Updated, content: { application/json: { schema: { $ref: '#/components/schemas/LoanAccount' } } } }

  /loans/{loanId}/transactions/template:
    get:
      summary: Get a transaction template
      parameters:
        - { name: loanId, in: path, required: true, schema: { type: string } }
        - { name: command, in: query, required: true, schema: { type: string, enum: [repayment, prepay, foreclosure, writeoff, waiveInterest, recovery] } }
      responses:
        '200':
          description: Template fields for the given transaction
          content: { application/json: { schema: { type: object, additionalProperties: true } } }

  /loans/{loanId}:
    post:
      summary: Perform a loan command
      description: "Use ?command=approve|disburse|close|repayment|prepay|foreclosure|writeoff|waiveInterest|recovery"
      parameters:
        - { name: loanId, in: path, required: true, schema: { type: string } }
        - { name: command, in: query, required: true, schema: { type: string, enum: [approve, disburse, close, repayment, prepay, foreclosure, writeoff, waiveInterest, recovery] } }
        - { $ref: '#/components/parameters/IdempotencyKey' }
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              description: "Fields depend on command; repayment-like commands require {amount, date}. When command=disburse, you may provide vehicleInventoryId to auto-allocate/sell an inventory vehicle to this loan."
              properties:
                amount: { type: number }
                date: { type: string, format: date }
                vehicleInventoryId: { type: string, description: "When command=disburse, the inventory item to allocate/sell." }
                notes: { type: string }
      responses:
        '200':
          description: Updated loan (and transaction if applicable)
          content:
            application/json:
              schema:
                type: object
                properties:
                  loan: { $ref: '#/components/schemas/LoanAccount' }
                  transaction: { $ref: '#/components/schemas/LoanTransaction' }

  # Charges
  /loans/{loanId}/charges:
    get:
      summary: List loan charges
      parameters: [ { name: loanId, in: path, required: true, schema: { type: string } } ]
      responses:
        '200': { description: Charges, content: { application/json: { schema: { type: array, items: { $ref: '#/components/schemas/LoanCharge' } } } } }
    post:
      summary: Add a charge
      parameters: [ { name: loanId, in: path, required: true, schema: { type: string } } ]
      requestBody:
        required: true
        content: { application/json: { schema: { $ref: '#/components/schemas/LoanCharge' } } }
      responses:
        '201': { description: Created, content: { application/json: { schema: { $ref: '#/components/schemas/LoanCharge' } } } }

  /loans/{loanId}/charges/{chargeId}:
    put:
      summary: Update a charge
      parameters: [ { name: loanId, in: path, required: true, schema: { type: string } }, { name: chargeId, in: path, required: true, schema: { type: string } } ]
      requestBody:
        required: true
        content: { application/json: { schema: { $ref: '#/components/schemas/LoanCharge' } } }
      responses:
        '200': { description: Updated, content: { application/json: { schema: { $ref: '#/components/schemas/LoanCharge' } } } }
    delete:
      summary: Remove a charge
      parameters: [ { name: loanId, in: path, required: true, schema: { type: string } }, { name: chargeId, in: path, required: true, schema: { type: string } } ]
      responses:
        '204': { description: Deleted }

  /loans/{loanId}/charges/{chargeId}/pay:
    post:
      summary: Pay a charge (CASH only)
      parameters:
        - { name: loanId, in: path, required: true, schema: { type: string } }
        - { name: chargeId, in: path, required: true, schema: { type: string } }
        - { $ref: '#/components/parameters/IdempotencyKey' }
      requestBody:
        required: true
        content: { application/json: { schema: { type: object, required: [amount, date], properties: { amount: { type: number }, date: { type: string, format: date } } } } }
      responses:
        '200': { description: Charge paid, content: { application/json: { schema: { $ref: '#/components/schemas/LoanTransaction' } } } }

  # Collateral
  /loans/{loanId}/collaterals:
    get:
      summary: List collateral
      parameters: [ { name: loanId, in: path, required: true, schema: { type: string } } ]
      responses:
        '200': { description: Collateral list, content: { application/json: { schema: { type: array, items: { $ref: '#/components/schemas/Collateral' } } } } }
    post:
      summary: Add collateral
      parameters: [ { name: loanId, in: path, required: true, schema: { type: string } } ]
      requestBody:
        required: true
        content: { application/json: { schema: { $ref: '#/components/schemas/Collateral' } } }
      responses:
        '201': { description: Created, content: { application/json: { schema: { $ref: '#/components/schemas/Collateral' } } } }

  /loans/{loanId}/collaterals/{collateralId}:
    put:
      summary: Update collateral
      parameters:
        - { name: loanId, in: path, required: true, schema: { type: string } }
        - { name: collateralId, in: path, required: true, schema: { type: string } }
      requestBody:
        required: true
        content: { application/json: { schema: { $ref: '#/components/schemas/Collateral' } } }
      responses:
        '200': { description: Updated, content: { application/json: { schema: { $ref: '#/components/schemas/Collateral' } } } }
    delete:
      summary: Remove collateral
      parameters:
        - { name: loanId, in: path, required: true, schema: { type: string } }
        - { name: collateralId, in: path, required: true, schema: { type: string } }
      responses:
        '204': { description: Deleted }

  # Vehicle inventory
  /vehicle-inventory:
    get:
      summary: List vehicle inventory
      parameters: [ { $ref: '#/components/parameters/Page' }, { $ref: '#/components/parameters/PageSize' }, { name: status, in: query, schema: { type: string } }, { name: q, in: query, schema: { type: string } } ]
      responses:
        '200':
          description: Inventory
          content: { application/json: { schema: { type: object, properties: { items: { type: array, items: { $ref: '#/components/schemas/VehicleInventory' } }, page: { type: integer }, pageSize: { type: integer }, total: { type: integer } } } } }
    post:
      summary: Create inventory item
      requestBody: { required: true, content: { application/json: { schema: { $ref: '#/components/schemas/VehicleInventory' } } } }
      responses:
        '201': { description: Created, content: { application/json: { schema: { $ref: '#/components/schemas/VehicleInventory' } } } }

  /vehicle-inventory/{id}:
    put:
      summary: Update inventory item
      parameters: [ { name: id, in: path, required: true, schema: { type: string } } ]
      requestBody: { required: true, content: { application/json: { schema: { $ref: '#/components/schemas/VehicleInventory' } } } }
      responses:
        '200': { description: Updated, content: { application/json: { schema: { $ref: '#/components/schemas/VehicleInventory' } } } }

  /vehicle-inventory/{id}:allocate:
    post:
      summary: Allocate (reserve) a vehicle to a loan (pre-disbursement)
      parameters: [ { name: id, in: path, required: true, schema: { type: string } } ]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [loanId]
              properties:
                loanId: { type: string }
      responses:
        '200': { description: Allocated, content: { application/json: { schema: { $ref: '#/components/schemas/VehicleInventory' } } } }
        '409': { description: Conflict (already allocated/sold), content: { application/json: { schema: { $ref: '#/components/schemas/Error' } } } }

  /vehicle-inventory/{id}:release:
    post:
      summary: Release a reserved vehicle from a loan
      parameters: [ { name: id, in: path, required: true, schema: { type: string } } ]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [loanId]
              properties:
                loanId: { type: string }
      responses:
        '200': { description: Released, content: { application/json: { schema: { $ref: '#/components/schemas/VehicleInventory' } } } }
        '409': { description: Conflict (not allocated to this loan), content: { application/json: { schema: { $ref: '#/components/schemas/Error' } } } }

  # Documents
  /clients/{clientId}/documents:
    get:
      summary: List client documents
      parameters: [ { name: clientId, in: path, required: true, schema: { type: string } } ]
      responses:
        '200': { description: Docs, content: { application/json: { schema: { type: array, items: { $ref: '#/components/schemas/Document' } } } } }
    post:
      summary: Upload client document
      parameters: [ { name: clientId, in: path, required: true, schema: { type: string } } ]
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required: [file, name]
              properties:
                file: { type: string, format: binary }
                name: { type: string }
      responses:
        '201': { description: Uploaded, content: { application/json: { schema: { $ref: '#/components/schemas/Document' } } } }

  /loans/{loanId}/documents:
    get:
      summary: List loan documents
      parameters: [ { name: loanId, in: path, required: true, schema: { type: string } } ]
      responses:
        '200': { description: Docs, content: { application/json: { schema: { type: array, items: { $ref: '#/components/schemas/Document' } } } } }
    post:
      summary: Upload loan document
      parameters: [ { name: loanId, in: path, required: true, schema: { type: string } } ]
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required: [file, name]
              properties:
                file: { type: string, format: binary }
                name: { type: string }
      responses:
        '201': { description: Uploaded, content: { application/json: { schema: { $ref: '#/components/schemas/Document' } } } }

  /documents/{documentId}/content:
    get:
      summary: Download document content
      parameters: [ { name: documentId, in: path, required: true, schema: { type: string } } ]
      responses:
        '200':
          description: Binary file
          content:
            application/octet-stream: {}

  # Reschedule (split preview/commit)
  /loans/{loanId}/reschedule/preview:
    post:
      summary: Preview schedule changes (no state change)
      parameters:
        - { name: loanId, in: path, required: true, schema: { type: string } }
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/ScheduleChangeRequest' }
      responses:
        '200':
          description: Recalculated schedule
          content:
            application/json:
              schema: { $ref: '#/components/schemas/SchedulePreviewResponse' }

  /loans/{loanId}/reschedule/commit:
    post:
      summary: Commit schedule changes (state changing)
      parameters:
        - { name: loanId, in: path, required: true, schema: { type: string } }
        - { $ref: '#/components/parameters/IdempotencyKey' }
      requestBody:
        required: true
        content:
          application/json:
            schema:
              allOf:
                - $ref: '#/components/schemas/ScheduleChangeRequest'
                - type: object
                  required: [previewVersion]
                  properties:
                    previewVersion:
                      type: string
                      description: "Must match the last preview for this loan to avoid drift."
      responses:
        '200':
          description: Updated loan
          content:
            application/json:
              schema: { $ref: '#/components/schemas/LoanAccount' }
        '409':
          description: Version mismatch or loan state changed since preview

  # Reports
  /reports/{reportName}/run:
    get:
      summary: Run a report
      parameters:
        - { name: reportName, in: path, required: true, schema: { type: string, enum: [loanPortfolio, delinquency] } }
        - { name: fromDate, in: query, schema: { type: string, format: date } }
        - { name: toDate, in: query, schema: { type: string, format: date } }
        - { name: format, in: query, schema: { type: string, enum: [JSON, CSV], default: JSON } }
      responses:
        '200':
          description: Report output
          content:
            application/json:
              schema: { type: object, additionalProperties: true }
            text/csv:
              schema: { type: string, format: binary }

  # Bulk upload
  /bulk/clients:
    post:
      summary: Bulk upload clients (CSV)
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required: [file]
              properties:
                file: { type: string, format: binary }
      responses:
        '202':
          description: Accepted, returns job id
          content:
            application/json:
              schema: { type: object, properties: { jobId: { type: string } } }

  /bulk/loans:
    post:
      summary: Bulk upload loans (CSV)
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required: [file]
              properties:
                file: { type: string, format: binary }
      responses:
        '202':
          description: Accepted, returns job id
          content:
            application/json:
              schema: { type: object, properties: { jobId: { type: string } } }

  # Jobs (batch-only)
  /jobs/{jobName}:run:
    post:
      summary: Start a batch job (available only on batch host)
      description: "jobName: loanCOB | delinquencyClassification | bulkClients | bulkLoans"
      parameters: [ { name: jobName, in: path, required: true, schema: { type: string } } ]
      responses:
        '202':
          description: Started
          content:
            application/json:
              schema: { type: object, properties: { jobId: { type: string } } }

  /jobs/{jobId}:
    get:
      summary: Get job status
      parameters: [ { name: jobId, in: path, required: true, schema: { type: string } } ]
      responses:
        '200':
          description: Job status
          content:
            application/json:
              schema:
                type: object
                properties:
                  id: { type: string }
                  name: { type: string }
                  status: { type: string, enum: [QUEUED, RUNNING, SUCCEEDED, FAILED] }
                  startedAt: { type: string, format: date-time }
                  finishedAt: { type: string, format: date-time, nullable: true }
                  stats: { type: object, additionalProperties: true }

  # Org & reference data (LKR & CASH only)
  /offices:
    get:
      summary: List offices
      responses:
        '200': { description: Offices, content: { application/json: { schema: { type: array, items: { $ref: '#/components/schemas/Office' } } } } }

  /staff:
    get:
      summary: List staff
      responses:
        '200': { description: Staff, content: { application/json: { schema: { type: array, items: { $ref: '#/components/schemas/Staff' } } } } }

  /holidays:
    get:
      summary: List holidays
      responses:
        '200': { description: Holidays, content: { application/json: { schema: { type: array, items: { $ref: '#/components/schemas/Holiday' } } } } }

  /currencies:
    get:
      summary: Get configured currency (LKR only)
      responses:
        '200': { description: Currency, content: { application/json: { schema: { $ref: '#/components/schemas/Currency' } } } }

  /payment-types:
    get:
      summary: Get payment type (CASH only)
      responses:
        '200': { description: PaymentType, content: { application/json: { schema: { $ref: '#/components/schemas/PaymentType' } } } }

  # Webhook management
  /webhooks:
    get:
      summary: List registered webhooks
      responses:
        '200':
          description: Webhooks
          content:
            application/json:
              schema:
                type: array
                items: { $ref: '#/components/schemas/Webhook' }
    post:
      summary: Register a webhook
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/WebhookCreate' }
      responses:
        '201': { description: Created, content: { application/json: { schema: { $ref: '#/components/schemas/Webhook' } } } }

  /webhooks/{id}:
    delete:
      summary: Delete a webhook
      parameters: [ { name: id, in: path, required: true, schema: { type: string } } ]
      responses:
        '204': { description: Deleted }

  /webhooks/{id}:test:
    post:
      summary: Send a sample event to a webhook
      parameters: [ { name: id, in: path, required: true, schema: { type: string } } ]
      responses:
        '202': { description: Test enqueued }

  /webhooks/deliveries:
    get:
      summary: List recent deliveries
      parameters:
        - { name: webhookId, in: query, schema: { type: string } }
        - { $ref: '#/components/parameters/Page' }
        - { $ref: '#/components/parameters/PageSize' }
      responses:
        '200':
          description: Deliveries
          content:
            application/json:
              schema:
                type: object
                properties:
                  items: { type: array, items: { $ref: '#/components/schemas/WebhookDelivery' } }
                  page: { type: integer }
                  pageSize: { type: integer }
                  total: { type: integer }

  /webhooks/deliveries/{deliveryId}:redeliver:
    post:
      summary: Trigger a redelivery attempt
      parameters: [ { name: deliveryId, in: path, required: true, schema: { type: string } } ]
      responses:
        '202': { description: Redelivery enqueued }

```

---

# Minimal FE service layer (Next.js)

Use the OpenAPI file above as your truth. One simple path:

1. **Generate types**

```bash
npm i -D openapi-typescript openapi-fetch
openapi-typescript schema.yml -o src/types/api.d.ts
```

2. **Create a typed client**

```ts
// src/lib/api.ts
import createClient from 'openapi-fetch';
import type { paths } from '@/types/api'; // generated by openapi-typescript

export const api = createClient<paths>({
  baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL + '/v1',
  headers: () => ({
    // Basic auth: pass via browser only over HTTPS; or proxy through Next.js Route Handler
    Authorization: 'Basic ' + btoa(`${localStorage.getItem('u')}:${localStorage.getItem('p')}`),
  }),
});
```

3. **Example calls in UI**

```ts
// list loans
const { data, error } = await api.GET('/loans', { params: { query: { page: 1, pageSize: 25 } } });

// repayment with printable receipt
const { data: tx } = await api.POST('/loans/{loanId}', {
  params: { path: { loanId }, query: { command: 'repayment' } },
  body: { amount, date },
  headers: { 'Idempotency-Key': crypto.randomUUID() },
});
// tx.transaction.receiptNumber -> render with react-to-print

// reschedule preview -> commit flow (previewVersion token)
const preview = await api.POST('/loans/{loanId}/reschedule/preview', {
  params: { path: { loanId } },
  body: { rescheduleFromDate, newInterestRate },
});
if (preview.data) {
  const { previewVersion } = preview.data;
  const commit = await api.POST('/loans/{loanId}/reschedule/commit', {
    params: { path: { loanId } },
    headers: { 'Idempotency-Key': crypto.randomUUID() },
    body: { rescheduleFromDate, newInterestRate, previewVersion },
  });
}
```

> If you prefer **fully generated clients**, swap `openapi-fetch` for **orval** or **openapi-generator** (typescript-fetch). The key is: **do not hand-code request/response types**—always import from the generated definitions.

---

##