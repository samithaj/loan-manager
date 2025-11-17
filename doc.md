
       Comprehensive Loan Manager Codebase Overview

       1. Overall Project Structure and Architecture

       The loan-manager project follows a modern full-stack architecture with clear separation of concerns:

       /Users/sam/Documents/dev/sk/sk-system/loan-manager/
       ├── backend/          # FastAPI backend
       │   ├── app/
       │   │   ├── models/   # SQLAlchemy ORM models
       │   │   ├── routers/  # API endpoint handlers
       │   │   ├── services/ # Business logic layer
       │   │   ├── auth.py   # JWT authentication
       │   │   ├── rbac.py   # Role-based access control
       │   │   ├── db.py     # Database configuration
       │   │   └── main.py   # Application entry point
       │   └── requirements.txt
       ├── frontend/         # Next.js frontend
       │   └── src/
       │       ├── app/      # Next.js 15 app router pages
       │       ├── components/ # React components
       │       ├── lib/      # API client utilities
       │       └── types/    # TypeScript types (auto-generated)
       ├── database/
       │   └── migrations/   # SQL migration files
       └── Makefile         # Development commands

       Architecture Pattern: The application follows a three-tier architecture:
       - Presentation Layer: Next.js 15 with React Server Components
       - API Layer: FastAPI with async/await patterns
       - Data Layer: PostgreSQL with SQLAlchemy async ORM

       2. Backend Framework: FastAPI

       Framework: FastAPI 0.115.0 (Python 3.11+)

       Key Dependencies:
       - fastapi==0.115.0 - Modern async web framework
       - uvicorn[standard]==0.30.6 - ASGI server
       - pydantic==2.8.2 - Data validation
       - sqlalchemy[asyncio]==2.0.36 - Async ORM
       - asyncpg==0.30.0 - PostgreSQL async driver
       - python-jose[cryptography]==3.3.0 - JWT handling
       - loguru==0.7.2 - Structured logging

       Application Configuration (/Users/sam/Documents/dev/sk/sk-system/loan-manager/backend/app/main.py):
       - API version: /v1 prefix
       - CORS enabled for localhost:3000 (Next.js dev server)
       - Structured JSON logging with correlation IDs
       - Custom error handlers for consistent error responses
       - Middleware: correlation ID tracking, request logging

       3. Authentication and Authorization System

       Authentication Mechanism: Dual approach
       1. JWT Token-based Authentication (Primary)
         - RS256 signed JWTs with auto-generated RSA key pairs
         - HttpOnly cookies for token storage (secure by default)
         - Access tokens: 15 minutes TTL
         - Refresh tokens: 7 days TTL
         - JWKS endpoint: /.well-known/jwks.json for token verification
       2. HTTP Basic Authentication (Legacy/Demo mode)
         - Configurable via demo_open_basic_auth setting
         - Falls back to database user verification

       Key Auth Files:
       - /Users/sam/Documents/dev/sk/sk-system/loan-manager/backend/app/auth.py - JWT generation, login/logout endpoints
       - /Users/sam/Documents/dev/sk/sk-system/loan-manager/backend/app/services/users.py - User creation and credential verification
       - /Users/sam/Documents/dev/sk/sk-system/loan-manager/backend/app/rbac.py - RBAC implementation

       Authentication Flow:
       1. User submits credentials to /v1/auth/login
       2. Backend verifies against database using SHA256 hash (note: demo-grade, should use bcrypt in production)
       3. Returns access and refresh tokens as HttpOnly cookies
       4. Frontend makes authenticated requests with cookies automatically included
       5. Backend verifies JWT on each request using get_current_user dependency

       4. Role-Based Access Control (RBAC) Implementation

       RBAC System (/Users/sam/Documents/dev/sk/sk-system/loan-manager/backend/app/rbac.py):

       Role Storage: Users have comma-separated roles in users.roles_csv field

       Authorization Functions:
       - get_current_user(request) - Extracts and validates JWT from cookies or Bearer token
       - require_roles(*needed) - Dependency factory for role-based endpoint protection

       Example Usage:
       @router.get("/admin-only")
       async def admin_endpoint(user=Depends(require_roles("admin"))):
           # Only accessible to users with "admin" role
           pass

       Frontend RBAC (/Users/sam/Documents/dev/sk/sk-system/loan-manager/frontend/src/components/RoleGuard.tsx):
       - Client-side role checking component
       - Calls /v1/me endpoint to verify user roles
       - Redirects to login if unauthorized
       - Note: Frontend guards are UX-only; server enforces actual security

       Middleware Protection (/Users/sam/Documents/dev/sk/sk-system/loan-manager/frontend/src/middleware.ts):
       - Next.js middleware for route protection
       - Verifies JWT using JWKS
       - Currently protects /loan-products route requiring admin or user role

       5. Database Models and ORM

       ORM: SQLAlchemy 2.0.36 with async support

       Database: PostgreSQL (using asyncpg driver)

       Connection: Async engine with postgresql+asyncpg:// connection string

       Base Configuration (/Users/sam/Documents/dev/sk/sk-system/loan-manager/backend/app/db.py):
       - DeclarativeBase for all models
       - Async session maker
       - Database URL from environment: LM_DATABASE_URL

       Core Models:

       1. User Model (/Users/sam/Documents/dev/sk/sk-system/loan-manager/backend/app/models/user.py)
         - UUID primary key
         - Username (unique)
         - Password hash (SHA256)
         - Roles as CSV string with property accessor
       2. Client Model (/Users/sam/Documents/dev/sk/sk-system/loan-manager/backend/app/models/client.py)
         - String ID
         - Display name, mobile, national ID, address
         - Created timestamp
       3. Loan Product Model (/Users/sam/Documents/dev/sk/sk-system/loan-manager/backend/app/models/loan_product.py)
         - String ID
         - Name, interest rate, term months, repayment frequency
       4. Loan Model (/Users/sam/Documents/dev/sk/sk-system/loan-manager/backend/app/models/loan.py)
         - String ID
         - Foreign keys: client_id, product_id
         - Principal, interest rate, term, status
         - Disbursement date
         - Status flow: PENDING → APPROVED → DISBURSED → CLOSED/WRITTEN_OFF
       5. Loan Transaction Model
         - Transaction types: REPAYMENT, PREPAY, FORECLOSURE, WRITEOFF, WAIVEINTEREST, RECOVERY
         - Amount, date, receipt number, posted_by user
       6. Loan Charge Model
         - Charges linked to loans
         - Amount, due date, status
       7. Collateral Model
         - Type (VEHICLE, LAND)
         - Value, JSONB details field
       8. Vehicle Inventory Model
         - VIN/frame number, brand, model, plate, color
         - Purchase price, MSRP
         - Status: IN_STOCK, SOLD
         - Linked to loans for vehicle financing
       9. Document Model
         - Owner type and ID (polymorphic)
         - Name, mime type, size
         - Upload timestamp
       10. Delinquency Models
         - DelinquencyBucket: Configurable ranges (min/max days)
         - DelinquencyStatus: Current bucket per loan
       11. Reference Data Models (/Users/sam/Documents/dev/sk/sk-system/loan-manager/backend/app/models/reference.py)
         - Office: id, name
         - Staff: id, name, role
         - Holiday: id, name, date
       12. Idempotency Model (/Users/sam/Documents/dev/sk/sk-system/loan-manager/backend/app/models/idempotency.py)
         - Tracks idempotency keys for state-changing operations
         - Stores request path, response status, and response body

       Database Migrations (/Users/sam/Documents/dev/sk/sk-system/loan-manager/database/migrations/0001_init.sql):
       - SQL-based migrations (not using Alembic)
       - Initial schema with all tables and indexes
       - Foreign key constraints for referential integrity

       6. API Endpoints Structure

       API Routers (all under /v1 prefix):

       1. Authentication (/Users/sam/Documents/dev/sk/sk-system/loan-manager/backend/app/auth.py)
         - POST /v1/auth/login - Login with credentials
         - POST /v1/auth/logout - Clear auth cookies
         - GET /v1/.well-known/jwks.json - JWT public keys
       2. Users (/Users/sam/Documents/dev/sk/sk-system/loan-manager/backend/app/routers/users.py)
         - POST /v1/users - Create user
       3. Clients (/Users/sam/Documents/dev/sk/sk-system/loan-manager/backend/app/routers/clients.py)
         - GET /v1/clients - List clients (with search)
         - POST /v1/clients - Create client
         - GET /v1/clients/{clientId} - Get client details
         - PUT /v1/clients/{clientId} - Update client
         - DELETE /v1/clients/{clientId} - Delete client
       4. Loan Products (loan_products.py)
         - Full CRUD for loan products
       5. Loans (/Users/sam/Documents/dev/sk/sk-system/loan-manager/backend/app/routers/loans.py)
         - GET /v1/loans - List loans (paginated, filterable by client/status)
         - POST /v1/loans - Create loan
         - GET /v1/loans/{loanId} - Get loan details with schedule
         - PUT /v1/loans/{loanId} - Update pending loan
         - POST /v1/loans/{loanId}?command={action} - Loan state transitions
             - Commands: approve, disburse, close, repayment, prepay, foreclosure, writeoff, waiveInterest, recovery
         - GET /v1/loans/{loanId}/transactions/template - Get transaction template
         - GET /v1/clients/{clientId}/accounts - Get client's loans
       6. Charges (charges.py)
         - Loan charge management
       7. Collateral (collateral.py)
         - Collateral and vehicle inventory management
       8. Documents (documents.py)
         - Document upload/download/listing
       9. Delinquency (delinquency.py)
         - Delinquency bucket configuration
         - Delinquency classification
       10. Jobs (jobs.py)
         - Batch job management (COB, delinquency classification)
       11. Reports (reports.py)
         - Report generation (portfolio, delinquency)
       12. Reschedule (reschedule.py)
         - Loan schedule preview and rescheduling
       13. Webhooks (webhooks.py)
         - Webhook configuration and delivery
       14. Reference Data (/Users/sam/Documents/dev/sk/sk-system/loan-manager/backend/app/routers/reference.py)
         - Full CRUD for offices, staff, holidays

       Common Patterns:
       - Idempotency key support via Idempotency-Key header
       - Structured error responses with error codes
       - Pagination for list endpoints
       - State machine validation for loan transitions
       - Correlation ID tracking for request tracing

       7. Frontend Technology

       Framework: Next.js 15.4.6 (React 19)

       Key Technologies:
       - Styling: Tailwind CSS 4
       - TypeScript: Full type safety
       - API Client: openapi-fetch with auto-generated types from OpenAPI schema
       - JWT Handling: jose library for JWT verification
       - Fonts: Geist Sans and Geist Mono

       Frontend Structure:
       /Users/sam/Documents/dev/sk/sk-system/loan-manager/frontend/src/
       ├── app/
       │   ├── layout.tsx          # Root layout with Header
       │   ├── page.tsx            # Home page
       │   ├── login/page.tsx      # Login page
       │   ├── profile/page.tsx    # User profile
       │   ├── clients/            # Client management pages
       │   ├── loan-products/      # Loan products
       │   └── reference/          # Reference data (offices, staff, holidays)
       ├── components/
       │   ├── Header.tsx          # Navigation header with auth status
       │   ├── RoleGuard.tsx       # Role-based component wrapper
       │   ├── AuthForm.tsx        # Authentication form
       │   ├── ClientsManager.tsx  # Client management UI
       │   ├── LoanProductManager.tsx
       │   ├── OfficeManager.tsx
       │   ├── StaffManager.tsx
       │   ├── HolidayManager.tsx
       │   └── PagedTable.tsx      # Reusable pagination component
       ├── lib/
       │   └── api.ts             # API client configuration
       ├── types/
       │   └── api.d.ts           # Auto-generated TypeScript types from OpenAPI
       └── middleware.ts          # Route protection middleware

       Authentication Flow:
       1. Login submits to /v1/auth/login with credentials
       2. Cookies set automatically by backend
       3. Frontend dispatches auth:updated event
       4. Header component listens and refetches /v1/me
       5. Protected routes use middleware for JWT verification

       API Integration (/Users/sam/Documents/dev/sk/sk-system/loan-manager/frontend/src/lib/api.ts):
       - Uses openapi-fetch for type-safe API calls
       - Base URL from environment: NEXT_PUBLIC_API_BASE_URL
       - Legacy Basic Auth support via localStorage

       Type Generation:
       - Command: npm run typegen
       - Converts OpenAPI schema to TypeScript types
       - Ensures frontend and backend stay in sync

       8. Configuration and Deployment Setup

       Backend Configuration (/Users/sam/Documents/dev/sk/sk-system/loan-manager/backend/app/config.py):
       - Environment prefix: LM_
       - Settings:
         - debug: Development mode (default: True)
         - database_url: PostgreSQL connection string
         - demo_open_basic_auth: Demo mode flag (default: False)
         - JWT settings (issuer, audience, TTL) - all optional with defaults

       Environment Variables:
       - LM_DATABASE_URL - Database connection
       - NEXT_PUBLIC_API_BASE_URL - Frontend API endpoint

       Development Setup (/Users/sam/Documents/dev/sk/sk-system/loan-manager/Makefile):

       Key Commands:
       - make install - Install dependencies (backend + frontend)
       - make db - Run database migrations
       - make dev - Run both backend and frontend with hot reload
       - make backend - Run backend only (port 8000)
       - make frontend - Run frontend only (port 3000)
       - make up - Start both services in background
       - make stop - Stop all services
       - make typegen - Generate TypeScript types from OpenAPI

       Backend Server:
       - Host: localhost
       - Port: 8000
       - Command: uvicorn app.main:app --reload

       Frontend Server:
       - Port: 3000
       - Command: next dev

       Database Setup:
       1. Requires PostgreSQL server running
       2. Create database: loan_manager
       3. Run migrations: make db (with DATABASE_URL set)
       4. Seed data via database/seed.sql

       Code Quality Tools:
       - Backend: ruff (linter), black (formatter), mypy (type checker)
       - Frontend: ESLint, TypeScript strict mode

       Logging:
       - Structured JSON logging via loguru
       - Correlation IDs for request tracing
       - Request/response logging middleware
       - Logs include: method, path, status, duration, principal, correlationId

       Deployment Considerations:
       - No Docker configuration found (development-focused)
       - No CI/CD configuration visible
       - PostgreSQL required for production
       - HTTPS recommended (CORS allows localhost only)
       - JWT keys should be persisted via environment variables in production
       - Password hashing needs upgrade (currently SHA256, should use bcrypt/argon2)

       Key Architectural Highlights

       1. Async-First: Entire backend uses async/await for better performance
       2. Type Safety: End-to-end type safety from database to frontend via OpenAPI
       3. Idempotency: Built-in idempotency key support for critical operations
       4. State Machine: Loan status transitions with validation
       5. Audit Trail: Transaction records with receipt numbers and posted_by tracking
       6. Modular Design: Clean separation of routers, models, services
       7. Developer Experience: Hot reload, type generation, structured logging
       8. Security: JWT with HttpOnly cookies, RBAC, correlation IDs for tracing

       Areas for Production Hardening

       1. Password hashing (upgrade from SHA256 to bcrypt/argon2)
       2. JWT key persistence (currently generates on startup)
       3. Database connection pooling configuration
       4. Rate limiting and request validation
       5. Container deployment setup (Docker/Kubernetes)
       6. Environment-based configuration management
       7. Comprehensive test coverage
       8. API documentation (Swagger UI)
       9. Monitoring and alerting setup
       10. Backup and disaster recovery procedures