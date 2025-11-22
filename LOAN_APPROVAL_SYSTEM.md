# Loan Approval Processor System

## Overview

A comprehensive, end-to-end loan approval processor system with a robust state machine workflow, role-based access control, and document management capabilities.

## Architecture

### System Components

1. **Backend (FastAPI)**
   - RESTful API with async SQLAlchemy ORM
   - JWT-based authentication with RBAC
   - State machine for loan application workflow
   - Document storage with pre-signed URLs (S3-compatible)
   - Comprehensive audit logging

2. **Frontend (Next.js 14 + Tailwind CSS)**
   - Server and Client components
   - Responsive UI with Tailwind CSS
   - Role-specific views (LMO and LO)
   - Real-time status updates

3. **Database (PostgreSQL)**
   - Normalized schema with referential integrity
   - JSONB for flexible metadata
   - Full audit trail with immutable logs

## Actors & Roles

### Loan Management Officer (LMO)
- Creates loan applications
- Uploads customer and vehicle documents
- Submits applications for approval
- Responds to "needs more info" requests
- Tracks application status

**Permissions:**
- `loan_applications:read`
- `loan_applications:write`
- `loan_applications:submit`
- `loan_applications:upload_documents`

### Loan Officer (LO)
- Reviews submitted applications
- Approves/Rejects applications
- Requests additional information
- Adds internal notes
- Monitors approval queue

**Permissions:**
- `loan_applications:read`
- `loan_applications:review`
- `loan_applications:approve`
- `loan_applications:reject`
- `loan_applications:request_info`

### Admin/Supervisor
- Manages users and roles
- Configures branches
- Audits decisions
- Full system access

**Permissions:**
- All permissions (wildcard `*`)

## State Machine Workflow

```mermaid
stateDiagram-v2
    [*] --> DRAFT
    DRAFT --> SUBMITTED: LMO submits
    DRAFT --> CANCELLED: Cancel
    SUBMITTED --> UNDER_REVIEW: LO starts review
    SUBMITTED --> CANCELLED: Cancel
    UNDER_REVIEW --> NEEDS_MORE_INFO: Request info
    UNDER_REVIEW --> APPROVED: Approve
    UNDER_REVIEW --> REJECTED: Reject
    UNDER_REVIEW --> CANCELLED: Cancel
    NEEDS_MORE_INFO --> SUBMITTED: LMO resubmits
    NEEDS_MORE_INFO --> CANCELLED: Cancel
    APPROVED --> [*]
    REJECTED --> [*]
    CANCELLED --> [*]
```

### States

1. **DRAFT** - Application created but not submitted
2. **SUBMITTED** - Sent to loan officer queue
3. **UNDER_REVIEW** - Loan officer reviewing
4. **NEEDS_MORE_INFO** - Additional documents/info required
5. **APPROVED** - Application approved (terminal state)
6. **REJECTED** - Application rejected (terminal state)
7. **CANCELLED** - Application cancelled (terminal state)

### Allowed Transitions

| From State       | To States                                                    |
|------------------|--------------------------------------------------------------|
| DRAFT            | SUBMITTED, CANCELLED                                         |
| SUBMITTED        | UNDER_REVIEW, CANCELLED                                      |
| UNDER_REVIEW     | NEEDS_MORE_INFO, APPROVED, REJECTED, CANCELLED               |
| NEEDS_MORE_INFO  | SUBMITTED, CANCELLED                                         |
| APPROVED         | (terminal)                                                   |
| REJECTED         | (terminal)                                                   |
| CANCELLED        | (terminal)                                                   |

## Database Schema

### Tables

1. **branches** - Branch offices
   - `id`, `code`, `name`, `region`, `address`, `phone`, `email`, `is_active`

2. **loan_applications** - Main application table
   - `id`, `application_no`, `lmo_user_id`, `branch_id`
   - `requested_amount`, `tenure_months`, `status`
   - `created_at`, `updated_at`, `submitted_at`, `reviewed_at`, `decided_at`

3. **loan_application_customers** - Customer details
   - `id`, `application_id`, `nic`, `full_name`, `dob`
   - `address`, `phone`, `email`

4. **loan_application_vehicles** - Vehicle details
   - `id`, `application_id`, `chassis_no`, `engine_no`
   - `make`, `model`, `year`, `color`, `registration_no`

5. **loan_application_documents** - Uploaded documents
   - `id`, `application_id`, `uploaded_by`, `doc_type`
   - `file_url`, `file_name`, `file_size`, `file_hash`, `mime_type`
   - `meta_json` (JSONB for OCR, dimensions, etc.)

6. **loan_application_decisions** - Decision history
   - `id`, `application_id`, `officer_user_id`, `decision`
   - `notes`, `decided_at`

7. **loan_application_audits** - Immutable audit trail
   - `id`, `application_id`, `actor_user_id`, `action`
   - `from_status`, `to_status`, `payload_json`, `created_at`

### Enums

- **ApplicationStatus**: `DRAFT`, `SUBMITTED`, `UNDER_REVIEW`, `NEEDS_MORE_INFO`, `APPROVED`, `REJECTED`, `CANCELLED`
- **DocumentType**: `NIC_FRONT`, `NIC_BACK`, `CUSTOMER_PHOTO`, `CERTIFICATE_OF_REGISTRATION`, `VEHICLE_PHOTO_*`, etc.
- **DecisionType**: `APPROVED`, `REJECTED`, `NEEDS_MORE_INFO`

## API Endpoints

### Branch Management
- `POST /api/v1/loan-applications/branches` - Create branch
- `GET /api/v1/loan-applications/branches` - List branches
- `GET /api/v1/loan-applications/branches/{id}` - Get branch

### Loan Applications
- `POST /api/v1/loan-applications` - Create application (DRAFT)
- `GET /api/v1/loan-applications` - List with filters
- `GET /api/v1/loan-applications/{id}` - Get details
- `PATCH /api/v1/loan-applications/{id}` - Update draft

### State Transitions
- `POST /api/v1/loan-applications/{id}/submit` - Submit for review
- `POST /api/v1/loan-applications/{id}/start-review` - Start review
- `POST /api/v1/loan-applications/{id}/decision` - Make decision
- `POST /api/v1/loan-applications/{id}/cancel` - Cancel application

### Documents
- `POST /api/v1/loan-applications/{id}/documents/presign` - Get upload URL
- `POST /api/v1/loan-applications/documents/{id}/confirm` - Confirm upload
- `GET /api/v1/loan-applications/documents/{id}/download` - Get download URL
- `GET /api/v1/loan-applications/{id}/documents` - List documents
- `DELETE /api/v1/loan-applications/documents/{id}` - Delete document

### Audit & Stats
- `GET /api/v1/loan-applications/{id}/timeline` - Get timeline
- `GET /api/v1/loan-applications/stats/queue` - Queue statistics

## Document Storage

### Supported Modes

1. **Local Storage** (Development)
   - Files stored in `uploads/loan_documents/`
   - Served via FastAPI static files

2. **S3-Compatible Storage** (Production)
   - AWS S3, MinIO, DigitalOcean Spaces, Google Cloud Storage
   - Pre-signed URLs for secure upload/download
   - Configurable TTL (default 1 hour)

### Configuration

```bash
# Local storage (default)
STORAGE_MODE=local

# S3-compatible storage
STORAGE_MODE=s3
S3_BUCKET_NAME=loan-documents
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_ENDPOINT=https://s3.amazonaws.com  # Optional for S3-compatible services
```

### Upload Flow

1. **Request Pre-signed URL**
   ```json
   POST /api/v1/loan-applications/{id}/documents/presign
   {
     "doc_type": "NIC_FRONT",
     "filename": "nic_front.jpg",
     "content_type": "image/jpeg",
     "file_size": 524288
   }
   ```

2. **Upload to Storage**
   - For S3: PUT to pre-signed URL with file
   - For local: PUT to API endpoint

3. **Confirm Upload**
   ```json
   POST /api/v1/loan-applications/documents/{doc_id}/confirm
   {
     "doc_id": "...",
     "file_hash": "sha256_hash",
     "meta_json": {"width": 1024, "height": 768}
   }
   ```

## Frontend Pages

### LMO Views

1. **Application List** (`/loan-applications`)
   - View all applications
   - Filter by status, branch, NIC, chassis no
   - Pagination

2. **Create Application Wizard** (`/loan-applications/new`)
   - Step 1: Loan details
   - Step 2: Customer information
   - Step 3: Vehicle information
   - Step 4: Review & submit
   - Save as draft or submit directly

3. **Application Detail** (`/loan-applications/[id]`)
   - Full application details
   - Document management
   - Timeline/audit trail
   - Submit/cancel actions

### Loan Officer Views

1. **Approval Queue** (`/loan-applications/queue`)
   - Statistics dashboard (submitted, under review, etc.)
   - Filter by status
   - Quick decision actions
   - SLA indicators

2. **Review Screen** (Same as application detail)
   - Customer & vehicle summary
   - Document viewer/gallery
   - Decision modal (Approve/Reject/Request Info)
   - Mandatory decision notes

## Security & Compliance

### RBAC Implementation
- Permission-based access control
- Role hierarchy support
- Branch-scoped access for managers
- API endpoint protection

### Audit Trail
- Immutable append-only logs
- Every state change recorded
- Actor tracking
- Payload snapshots

### File Security
- Private file storage
- Pre-signed URLs with short TTL
- File hash verification (SHA-256)
- File size validation
- MIME type checking

### PII Protection
- Customer data encrypted at rest
- Secure transmission (HTTPS)
- Access logging
- GDPR/compliance-ready

## Installation & Setup

### 1. Database Migration

```bash
# Apply migration
psql -U postgres -d loan_manager -f database/migrations/0010_loan_approval_system.sql

# Verify tables
psql -U postgres -d loan_manager -c "\dt loan_*"
```

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Configure environment
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/loan_manager"
export STORAGE_MODE=local  # or s3

# Run server
uvicorn app.main:app --reload
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 4. Create Test Users

```sql
-- Create Loan Management Officer
INSERT INTO users (username, password_hash, roles_csv)
VALUES ('lmo_test', 'hashed_password', 'loan_management_officer');

-- Create Loan Officer
INSERT INTO users (username, password_hash, roles_csv)
VALUES ('lo_test', 'hashed_password', 'loan_officer');
```

## Testing

### Run Test Suite

```bash
# Backend tests
pytest tests/test_loan_application_workflow.py -v

# Integration tests
pytest tests/integration/ -v
```

### Test Coverage

- State machine transitions
- RBAC permissions
- Document upload/download
- Timeline generation
- API endpoints
- Error handling

## Phase 2 Features (Future)

### 1. Auto-validation
- OCR for NIC and CR documents
- Chassis number verification
- Duplicate detection
- Risk scoring

### 2. Rule-based Pre-scoring
- Vehicle age/make risk scoring
- Customer credit history
- Automated recommendations
- Red flag detection

### 3. Assignment & SLA
- Auto-assign to officers
- Workload balancing
- SLA timers with escalation
- Performance metrics

### 4. Integrations
- Core banking system
- CRM integration
- Credit bureau API
- SMS/WhatsApp notifications
- Email alerts

### 5. Advanced Analytics
- Approval rate trends
- Decision time metrics
- Branch performance
- Officer productivity
- Risk analysis

## Deployment

### Production Checklist

- [ ] Configure S3/cloud storage
- [ ] Set up SSL/TLS certificates
- [ ] Configure database backups
- [ ] Set up monitoring (Sentry, CloudWatch)
- [ ] Configure rate limiting
- [ ] Enable antivirus scanning for uploads
- [ ] Set up CDN for static files
- [ ] Configure log aggregation
- [ ] Set up alerting
- [ ] Document DR procedures

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://...

# Storage
STORAGE_MODE=s3
S3_BUCKET_NAME=loan-documents
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

# Security
JWT_SECRET=...
JWT_AUDIENCE=loan-manager
JWT_ISSUER=https://api.yourcompany.com

# Application
DEBUG=false
ALLOWED_ORIGINS=https://app.yourcompany.com
MAX_FILE_SIZE=10485760  # 10MB
```

## Support & Maintenance

### Monitoring Points
- Application submission rate
- Approval/rejection rates
- Average decision time
- Document upload failures
- API error rates
- Database query performance

### Logs to Monitor
- State transition errors
- RBAC violations
- File upload failures
- Invalid transitions
- Slow queries

## Contributing

See `CONTRIBUTING.md` for development guidelines.

## License

Proprietary - All rights reserved.
