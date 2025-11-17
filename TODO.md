# Bicycle Hire Purchase System - Integration TODO

## 📋 Overview

This document outlines the complete integration plan for adding a **Bicycle Hire Purchase System** to the existing Loan Manager application. The integration will reuse the existing FastAPI backend, PostgreSQL database, authentication system, and RBAC infrastructure.

### System Architecture

**Current System:**
- Backend: FastAPI with SQLAlchemy async ORM
- Frontend: Next.js 15 with React Server Components
- Database: PostgreSQL with asyncpg
- Auth: JWT with HttpOnly cookies + RBAC
- Existing Features: Loan management, client management, reference data

**New Features to Add:**
- Public bicycle catalog website (no auth required)
- Customer application portal for hire purchase
- Staff bicycle inventory management
- Application review and approval workflow
- Multi-branch bicycle sales support
- Role-based access control for 6+ user types

### Key Benefits

✅ **Reuses existing infrastructure** - No need to rebuild authentication, database, or API patterns
✅ **Type-safe end-to-end** - OpenAPI schema generates TypeScript types
✅ **Multi-tenant ready** - Branch-scoped access control built-in
✅ **Production-grade** - Inherits logging, error handling, and security from existing system
✅ **Fast development** - Leverage existing components and patterns

---

## 🎯 Goals & Features

### Public Website (Customer-Facing)

1. **Home Page**
   - Hero section with CTA
   - Featured bicycles grid
   - Quick filters (New/Used, Branch, Price)
   - "How It Works" explainer section

2. **Bicycle Catalog**
   - Grid/list view with filtering
   - Filters: Condition, Branch, Price range, Brand
   - Pagination
   - "From X/month" pricing display

3. **Bicycle Detail Page**
   - Photo carousel
   - Complete specifications
   - Finance calculator
   - "Apply for Hire Purchase" CTA

4. **Application Form**
   - Customer details (Name, Phone, Email, NIP)
   - Employment information
   - Bicycle selection
   - Branch selection
   - Tenure selection (12/24/36/48 months)
   - Down payment input

5. **Branch Listing**
   - All branches with contact info
   - Map links
   - Operating hours

### Staff Back-Office

1. **Application Management**
   - List all applications with filters
   - View application details
   - Approve/reject applications
   - Convert approved applications to loans
   - Add notes and track review history

2. **Bicycle Inventory Management**
   - CRUD operations for bicycles
   - Multi-image upload with thumbnails
   - Bulk import from CSV
   - Status management (Available/Reserved/Sold/Maintenance)
   - Branch assignment

3. **Branch Management**
   - Configure branch details
   - Set operating hours
   - Enable/disable bicycle sales per branch
   - Display order for public site

4. **Role-Based Access Control**
   - Admin: Full system access
   - Branch Manager: Manage single branch
   - Sales Agent: Review applications, create loans
   - Inventory Manager: Manage bicycle inventory
   - Finance Officer: Approve loans, manage payments
   - Customer Service: View applications, communicate with customers
   - Auditor: Read-only access to all data

5. **Dashboard & Reporting**
   - Application pipeline widget
   - Inventory status summary
   - Branch performance metrics
   - Conversion funnel analytics

---

## 🏗️ Phase 1: Database Schema Extensions

### Task 1.1: Create Migration File

**File:** `database/migrations/0002_bicycle_hire_purchase.sql`

**Subtasks:**
- [ ] Create `bicycles` table with all fields
  - [ ] Add id (TEXT, primary key)
  - [ ] Add title, brand, model, year
  - [ ] Add condition (NEW/USED enum)
  - [ ] Add license_plate (unique)
  - [ ] Add frame_number, engine_number
  - [ ] Add pricing fields (purchase_price, cash_price, hire_purchase_price)
  - [ ] Add duty_amount, registration_fee
  - [ ] Add mileage_km, description
  - [ ] Add branch_id (foreign key to offices)
  - [ ] Add status (AVAILABLE/RESERVED/SOLD/MAINTENANCE)
  - [ ] Add image_urls (JSONB), thumbnail_url
  - [ ] Add created_at, updated_at timestamps

- [ ] Create indexes for bicycles table
  - [ ] idx_bicycles_branch (branch_id)
  - [ ] idx_bicycles_status (status)
  - [ ] idx_bicycles_condition (condition)
  - [ ] idx_bicycles_license_plate (license_plate)

- [ ] Create `bicycle_applications` table
  - [ ] Add id (TEXT, primary key)
  - [ ] Add customer fields (full_name, phone, email, nip_number)
  - [ ] Add address fields (address_line1, address_line2, city)
  - [ ] Add employment fields (employer_name, monthly_income)
  - [ ] Add bicycle_id (foreign key to bicycles)
  - [ ] Add branch_id (foreign key to offices)
  - [ ] Add tenure_months, down_payment
  - [ ] Add status (PENDING/UNDER_REVIEW/APPROVED/REJECTED/CONVERTED_TO_LOAN)
  - [ ] Add notes, loan_id (foreign key to loans)
  - [ ] Add submitted_at, reviewed_by, reviewed_at

- [ ] Create indexes for bicycle_applications table
  - [ ] idx_bicycle_applications_status (status)
  - [ ] idx_bicycle_applications_branch (branch_id)
  - [ ] idx_bicycle_applications_submitted_at (submitted_at)

- [ ] Extend `offices` table
  - [ ] Add allows_bicycle_sales (BOOLEAN, default TRUE)
  - [ ] Add bicycle_display_order (INTEGER)
  - [ ] Add map_coordinates (JSONB)
  - [ ] Add operating_hours (TEXT)
  - [ ] Add public_description (TEXT)

- [ ] Seed default data
  - [ ] Insert bicycle hire purchase loan product
  - [ ] Create test branches (10+ branches)
  - [ ] Create sample bicycles

**Testing:**
- [ ] Run migration: `make db`
- [ ] Verify all tables created
- [ ] Verify all indexes created
- [ ] Verify foreign key constraints work
- [ ] Verify check constraints work

---

### Task 1.2: Create SQLAlchemy Models

**File:** `backend/app/models/bicycle.py`

**Subtasks:**
- [ ] Create BicycleCondition enum (NEW, USED)
- [ ] Create BicycleStatus enum (AVAILABLE, RESERVED, SOLD, MAINTENANCE)
- [ ] Create Bicycle model class
  - [ ] Add all mapped columns matching database schema
  - [ ] Add relationship to Office (branch)
  - [ ] Add relationship to BicycleApplication (backref)
- [ ] Create helper methods
  - [ ] `to_dict()` method for serialization
  - [ ] `to_public_dict()` method (excludes internal fields)
  - [ ] `calculate_monthly_payment()` method

**File:** `backend/app/models/bicycle_application.py`

**Subtasks:**
- [ ] Create ApplicationStatus enum
- [ ] Create BicycleApplication model class
  - [ ] Add all mapped columns
  - [ ] Add relationship to Bicycle
  - [ ] Add relationship to Office (branch)
  - [ ] Add relationship to Loan
  - [ ] Add relationship to User (reviewed_by)
- [ ] Create helper methods
  - [ ] `to_dict()` method
  - [ ] `can_approve()` validation method
  - [ ] `can_reject()` validation method

**File:** `backend/app/models/reference.py` (extend existing)

**Subtasks:**
- [ ] Add new columns to Office model
  - [ ] allows_bicycle_sales
  - [ ] bicycle_display_order
  - [ ] map_coordinates
  - [ ] operating_hours
  - [ ] public_description
- [ ] Add `to_public_dict()` method to Office model

**Testing:**
- [ ] Import models in Python shell
- [ ] Test model instantiation
- [ ] Test relationships work
- [ ] Test to_dict() methods
- [ ] Run mypy type checking

---

### Task 1.3: Extend RBAC System

**File:** `backend/app/rbac.py`

**Subtasks:**
- [ ] Add new role constants
  - [ ] BRANCH_MANAGER
  - [ ] SALES_AGENT
  - [ ] INVENTORY_MANAGER
  - [ ] FINANCE_OFFICER
  - [ ] CUSTOMER_SERVICE
  - [ ] AUDITOR

- [ ] Define ROLE_PERMISSIONS dictionary
  - [ ] Map ADMIN to ["*"]
  - [ ] Map BRANCH_MANAGER to bicycle/application/loan permissions
  - [ ] Map SALES_AGENT to application/client/loan permissions
  - [ ] Map INVENTORY_MANAGER to bicycle/document permissions
  - [ ] Map FINANCE_OFFICER to loan approval permissions
  - [ ] Map CUSTOMER_SERVICE to application/client read/write
  - [ ] Map AUDITOR to ["*.read"] wildcard

- [ ] Implement `require_permission(permission: str)` function
  - [ ] Check if user is admin (return immediately)
  - [ ] Collect all permissions from user's roles
  - [ ] Check exact permission match
  - [ ] Check wildcard permission match ("*", "*.read")
  - [ ] Raise HTTPException(403) if no match

- [ ] Implement `require_branch_access(branch_id: str, user: User)` function
  - [ ] Check if user is admin (return True)
  - [ ] Check if user is branch_manager
  - [ ] Verify user.metadata["branch_id"] matches requested branch_id
  - [ ] Raise HTTPException(403) if no match

- [ ] Update existing `require_roles()` function to use new system

**File:** `backend/app/models/user.py` (extend existing)

**Subtasks:**
- [ ] Add metadata column (JSONB) for storing user-specific config
- [ ] Add @property for easy metadata access
- [ ] Update seed data to include metadata for branch managers

**Testing:**
- [ ] Create test users with different roles
- [ ] Test require_permission() with each role
- [ ] Test wildcard permission matching
- [ ] Test require_branch_access() with branch managers
- [ ] Test permission denial raises 403

---

### Task 1.4: Seed Default Data

**File:** `database/seed_bicycle_system.sql`

**Subtasks:**
- [ ] Create 10+ branches
  - [ ] Add realistic addresses and contact info
  - [ ] Set allows_bicycle_sales = TRUE
  - [ ] Set bicycle_display_order
  - [ ] Add operating_hours
  - [ ] Add public_description

- [ ] Create bicycle hire purchase loan product
  - [ ] id: 'BICYCLE_HP'
  - [ ] name: 'Bicycle Hire Purchase'
  - [ ] interest_rate: 12.0
  - [ ] term_months: 36
  - [ ] repayment_frequency: 'MONTHLY'

- [ ] Create default users for each role
  - [ ] admin user
  - [ ] branch_manager users (one per branch)
  - [ ] sales_agent users
  - [ ] inventory_manager users
  - [ ] finance_officer users
  - [ ] customer_service users
  - [ ] auditor user

- [ ] Create sample bicycles (20+)
  - [ ] Mix of NEW and USED
  - [ ] Various brands (Honda, Yamaha, Bajaj, TVS)
  - [ ] Different price ranges
  - [ ] Distribute across branches
  - [ ] All AVAILABLE status

**Testing:**
- [ ] Run seed script
- [ ] Verify branches created
- [ ] Verify users created with correct roles
- [ ] Verify bicycles created
- [ ] Verify loan product created
- [ ] Test login with each user type

---

## 🏗️ Phase 2: Public API & Core Business Logic

### Task 2.1: Create Public Bicycle Catalog API

**File:** `backend/app/routers/public_bicycles.py`

**Subtasks:**
- [ ] Create router with prefix="/public"
- [ ] Implement `GET /public/bicycles`
  - [ ] Add query parameters: condition, branch_id, min_price, max_price, brand, search
  - [ ] Add pagination: offset, limit
  - [ ] Filter only AVAILABLE bicycles
  - [ ] Apply all query filters
  - [ ] Return paginated response with total count
  - [ ] Use bicycle_to_public_dict() for serialization

- [ ] Implement `GET /public/bicycles/{bicycle_id}`
  - [ ] Fetch bicycle by ID
  - [ ] Verify bicycle is AVAILABLE
  - [ ] Return 404 if not found or not available
  - [ ] Return detailed bicycle info with all images

- [ ] Implement `GET /public/branches`
  - [ ] Filter only branches with allows_bicycle_sales=TRUE
  - [ ] Order by bicycle_display_order
  - [ ] Return branch list with public info

- [ ] Implement `GET /public/branches/{branch_id}`
  - [ ] Fetch branch by ID
  - [ ] Verify allows_bicycle_sales=TRUE
  - [ ] Return 404 if not found
  - [ ] Return detailed branch info

- [ ] Create helper functions
  - [ ] `bicycle_to_public_dict(bicycle, include_details=False)`
  - [ ] `branch_to_public_dict(branch, include_details=False)`

**Testing:**
- [ ] Test GET /public/bicycles without filters
- [ ] Test with each filter parameter
- [ ] Test pagination
- [ ] Test search functionality
- [ ] Test GET /public/bicycles/{id}
- [ ] Test GET /public/branches
- [ ] Test GET /public/branches/{id}
- [ ] Verify RESERVED/SOLD bicycles are hidden
- [ ] Verify disabled branches are hidden

---

### Task 2.2: Create Application Submission API

**File:** `backend/app/routers/bicycle_applications.py`

**Subtasks:**
- [ ] Create router with prefix="/v1/bicycle-applications"

- [ ] Implement `POST /v1/bicycle-applications` (public, no auth)
  - [ ] Create Pydantic ApplicationCreate schema
  - [ ] Check idempotency key
  - [ ] Validate bicycle exists and is AVAILABLE
  - [ ] Generate application ID
  - [ ] Set status to PENDING
  - [ ] Save application to database
  - [ ] Mark bicycle as RESERVED
  - [ ] Send notification email/SMS
  - [ ] Return application ID and status

- [ ] Implement `GET /v1/bicycle-applications` (staff only)
  - [ ] Add require_permission("applications:read") dependency
  - [ ] Add filters: status, branch_id
  - [ ] Add pagination: offset, limit
  - [ ] Filter by user's branch if branch_manager
  - [ ] Order by submitted_at DESC
  - [ ] Return paginated applications list
  - [ ] Include bicycle and branch relationships

- [ ] Implement `GET /v1/bicycle-applications/{application_id}` (staff only)
  - [ ] Add require_permission("applications:read") dependency
  - [ ] Fetch application by ID
  - [ ] Check branch access
  - [ ] Return 404 if not found
  - [ ] Include all relationships (bicycle, branch, loan)

- [ ] Implement `POST /v1/bicycle-applications/{id}?command=approve` (staff only)
  - [ ] Add require_permission("applications:approve") dependency
  - [ ] Verify application status is PENDING
  - [ ] Get or create client from application data
  - [ ] Create loan with bicycle as collateral
  - [ ] Update application status to CONVERTED_TO_LOAN
  - [ ] Link application to loan
  - [ ] Set reviewed_by and reviewed_at
  - [ ] Return loan ID

- [ ] Implement `POST /v1/bicycle-applications/{id}?command=reject` (staff only)
  - [ ] Add require_permission("applications:approve") dependency
  - [ ] Add notes parameter (required)
  - [ ] Update application status to REJECTED
  - [ ] Save rejection notes
  - [ ] Set reviewed_by and reviewed_at
  - [ ] Release bicycle reservation (set to AVAILABLE)
  - [ ] Send notification to customer
  - [ ] Return rejection confirmation

**Testing:**
- [ ] Test public application submission
- [ ] Test idempotency key prevents duplicates
- [ ] Test validation errors (invalid bicycle, etc.)
- [ ] Test bicycle reservation on submit
- [ ] Test staff list applications
- [ ] Test branch filtering for branch managers
- [ ] Test approve workflow
- [ ] Test reject workflow
- [ ] Test bicycle status changes

---

### Task 2.3: Implement Business Logic Services

**File:** `backend/app/services/bicycle_service.py`

**Subtasks:**
- [ ] Create `get_or_create_client_from_application(db, application)`
  - [ ] Search for existing client by NIP number
  - [ ] If found, update details
  - [ ] If not found, create new client
  - [ ] Map application fields to client fields
  - [ ] Return client object

- [ ] Create `create_loan_from_application(db, application, user)`
  - [ ] Fetch bicycle hire purchase loan product
  - [ ] Calculate principal (hire_purchase_price - down_payment)
  - [ ] Create loan with calculated values
  - [ ] Set loan status to PENDING
  - [ ] Link bicycle as collateral
  - [ ] Return loan object

- [ ] Create `reserve_bicycle(db, bicycle_id)`
  - [ ] Fetch bicycle
  - [ ] Verify status is AVAILABLE
  - [ ] Set status to RESERVED
  - [ ] Return success

- [ ] Create `release_bicycle_reservation(db, bicycle_id)`
  - [ ] Fetch bicycle
  - [ ] Verify status is RESERVED
  - [ ] Set status to AVAILABLE
  - [ ] Return success

- [ ] Create `mark_bicycle_sold(db, bicycle_id, loan_id)`
  - [ ] Fetch bicycle
  - [ ] Set status to SOLD
  - [ ] Link to loan as collateral
  - [ ] Return success

- [ ] Create `generate_application_id()` helper
  - [ ] Use format: APP-{timestamp}-{random}
  - [ ] Ensure uniqueness

**Testing:**
- [ ] Test get_or_create_client with new customer
- [ ] Test get_or_create_client with existing customer
- [ ] Test create_loan_from_application
- [ ] Test reserve_bicycle
- [ ] Test release_bicycle_reservation
- [ ] Test mark_bicycle_sold
- [ ] Test ID generation uniqueness

---

### Task 2.4: Add Notification System

**File:** `backend/app/services/notification_service.py`

**Subtasks:**
- [ ] Create email templates
  - [ ] Application submitted confirmation (customer)
  - [ ] New application alert (branch staff)
  - [ ] Application approved (customer)
  - [ ] Application rejected (customer)

- [ ] Implement `send_application_submitted_email(application)`
  - [ ] Format customer email with application details
  - [ ] Include application ID
  - [ ] Include estimated processing time
  - [ ] Send using SMTP or email service

- [ ] Implement `send_new_application_notification(application)`
  - [ ] Get branch staff emails
  - [ ] Format notification with customer info
  - [ ] Include link to review application
  - [ ] Send to all relevant staff

- [ ] Implement `send_application_approved_email(application)`
  - [ ] Format approval confirmation
  - [ ] Include next steps
  - [ ] Include branch contact info
  - [ ] Send to customer

- [ ] Implement `send_application_rejected_email(application)`
  - [ ] Format rejection notice
  - [ ] Include reason (notes)
  - [ ] Include contact info for questions
  - [ ] Send to customer

- [ ] Configure email settings
  - [ ] Add SMTP settings to config
  - [ ] Add email templates directory
  - [ ] Add from address configuration

**Optional: SMS Notifications**
- [ ] Integrate SMS service (Twilio, etc.)
- [ ] Implement SMS variants of notifications
- [ ] Add phone number validation

**Testing:**
- [ ] Test email sending (use mailtrap.io for dev)
- [ ] Test all email templates render correctly
- [ ] Test notifications triggered at right times
- [ ] Test error handling if email fails

---

## 🏗️ Phase 3: Staff Bicycle Inventory Management

### Task 3.1: Create Bicycle Inventory API

**File:** `backend/app/routers/bicycles.py`

**Subtasks:**
- [ ] Create router with prefix="/v1/bicycles"

- [ ] Implement `GET /v1/bicycles` (staff only)
  - [ ] Add require_permission("bicycles:read") dependency
  - [ ] Add filters: condition, status, branch_id, brand, search
  - [ ] Add pagination: offset, limit
  - [ ] Filter by user's branch if branch_manager
  - [ ] Show all statuses (not just AVAILABLE)
  - [ ] Order by created_at DESC
  - [ ] Return paginated bicycles list

- [ ] Implement `GET /v1/bicycles/{bicycle_id}` (staff only)
  - [ ] Add require_permission("bicycles:read") dependency
  - [ ] Fetch bicycle by ID
  - [ ] Check branch access
  - [ ] Return 404 if not found
  - [ ] Include all details and relationships

- [ ] Implement `POST /v1/bicycles` (staff only)
  - [ ] Add require_permission("bicycles:write") dependency
  - [ ] Create Pydantic BicycleCreate schema
  - [ ] Validate branch_id
  - [ ] Check branch access
  - [ ] Generate bicycle ID
  - [ ] Set default status to AVAILABLE
  - [ ] Save to database
  - [ ] Return created bicycle

- [ ] Implement `PUT /v1/bicycles/{bicycle_id}` (staff only)
  - [ ] Add require_permission("bicycles:write") dependency
  - [ ] Create Pydantic BicycleUpdate schema
  - [ ] Fetch existing bicycle
  - [ ] Check branch access
  - [ ] Update fields
  - [ ] Set updated_at
  - [ ] Save to database
  - [ ] Return updated bicycle

- [ ] Implement `DELETE /v1/bicycles/{bicycle_id}` (staff only)
  - [ ] Add require_permission("bicycles:delete") dependency
  - [ ] Fetch bicycle
  - [ ] Check branch access
  - [ ] Check if bicycle has active applications
  - [ ] Soft delete (set status to INACTIVE or delete flag)
  - [ ] Return success

- [ ] Implement `PATCH /v1/bicycles/{bicycle_id}/status` (staff only)
  - [ ] Add require_permission("bicycles:write") dependency
  - [ ] Add status parameter
  - [ ] Validate status transition
  - [ ] Update bicycle status
  - [ ] Return updated bicycle

**Testing:**
- [ ] Test list bicycles
- [ ] Test filters work correctly
- [ ] Test branch filtering for branch managers
- [ ] Test create bicycle
- [ ] Test update bicycle
- [ ] Test delete bicycle
- [ ] Test status update
- [ ] Test validation errors

---

### Task 3.2: Implement Image Upload

**File:** `backend/app/routers/bicycles.py` (extend)

**Subtasks:**
- [ ] Implement `POST /v1/bicycles/{bicycle_id}/images`
  - [ ] Add require_permission("bicycles:write") dependency
  - [ ] Accept multiple file uploads
  - [ ] Validate file types (jpg, png, webp)
  - [ ] Validate file sizes (max 5MB per image)
  - [ ] Check branch access
  - [ ] Upload files to storage
  - [ ] Generate thumbnails
  - [ ] Save URLs to bicycle.image_urls
  - [ ] Set thumbnail_url if first image
  - [ ] Return uploaded URLs

- [ ] Implement `DELETE /v1/bicycles/{bicycle_id}/images/{image_url}`
  - [ ] Add require_permission("bicycles:write") dependency
  - [ ] Remove URL from bicycle.image_urls
  - [ ] Delete file from storage
  - [ ] If thumbnail, set new thumbnail
  - [ ] Return success

**File:** `backend/app/services/storage_service.py`

**Subtasks:**
- [ ] Choose storage backend (local, S3, Cloudinary)
  - [ ] Add configuration for chosen backend
  - [ ] Add storage credentials to .env

- [ ] Implement `upload_file(file, path)` function
  - [ ] Generate unique filename
  - [ ] Upload to storage
  - [ ] Return public URL

- [ ] Implement `delete_file(url)` function
  - [ ] Parse URL to get file path
  - [ ] Delete from storage
  - [ ] Return success

- [ ] Implement `generate_thumbnail(file, size=(300, 300))` function
  - [ ] Use Pillow to resize image
  - [ ] Maintain aspect ratio
  - [ ] Optimize for web
  - [ ] Upload thumbnail
  - [ ] Return thumbnail URL

**Configuration:**
- [ ] Add LOCAL_STORAGE_PATH to config
- [ ] Add S3_BUCKET, S3_REGION, S3_ACCESS_KEY (if using S3)
- [ ] Add CLOUDINARY_URL (if using Cloudinary)
- [ ] Add MAX_FILE_SIZE to config
- [ ] Add ALLOWED_IMAGE_TYPES to config

**Testing:**
- [ ] Test single image upload
- [ ] Test multiple images upload
- [ ] Test file type validation
- [ ] Test file size validation
- [ ] Test thumbnail generation
- [ ] Test image deletion
- [ ] Test storage backend works

---

### Task 3.3: Implement Bulk Import

**File:** `backend/app/routers/bicycles.py` (extend)

**Subtasks:**
- [ ] Implement `POST /v1/bicycles/bulk-import`
  - [ ] Add require_permission("bicycles:write") dependency
  - [ ] Accept CSV file upload
  - [ ] Parse CSV file
  - [ ] Validate each row
  - [ ] Check for duplicates (license plate)
  - [ ] Create bicycles in batch
  - [ ] Return import summary (success/errors)

- [ ] Create CSV template
  - [ ] Define required columns
  - [ ] Define optional columns
  - [ ] Add example data
  - [ ] Document format

- [ ] Implement validation
  - [ ] Validate required fields
  - [ ] Validate data types
  - [ ] Validate enums (condition, status)
  - [ ] Validate branch_id exists
  - [ ] Collect all errors before failing

- [ ] Implement error reporting
  - [ ] Return row number for each error
  - [ ] Return validation message
  - [ ] Allow partial success option

**Testing:**
- [ ] Create test CSV file
- [ ] Test successful bulk import
- [ ] Test validation errors
- [ ] Test duplicate detection
- [ ] Test partial success handling
- [ ] Test large file performance

---

### Task 3.4: Extend Branch Management

**File:** `backend/app/routers/reference.py` (extend existing)

**Subtasks:**
- [ ] Update `PUT /v1/offices/{office_id}` endpoint
  - [ ] Add new bicycle-specific fields to update schema
  - [ ] Allow updating allows_bicycle_sales
  - [ ] Allow updating bicycle_display_order
  - [ ] Allow updating map_coordinates
  - [ ] Allow updating operating_hours
  - [ ] Allow updating public_description

- [ ] Update `GET /v1/offices` endpoint
  - [ ] Include bicycle-specific fields in response

- [ ] Update `GET /v1/offices/{office_id}` endpoint
  - [ ] Include bicycle-specific fields in response

**Testing:**
- [ ] Test updating bicycle fields on branch
- [ ] Test branch list includes new fields
- [ ] Test branch detail includes new fields

---

### Task 3.5: Create Reporting Endpoints

**File:** `backend/app/routers/reports.py` (extend existing)

**Subtasks:**
- [ ] Implement `GET /v1/reports/bicycle-inventory`
  - [ ] Add require_permission("reports:view") dependency
  - [ ] Add filters: branch_id, condition, status
  - [ ] Group by branch and status
  - [ ] Calculate totals by status
  - [ ] Calculate total value
  - [ ] Return summary data

- [ ] Implement `GET /v1/reports/application-funnel`
  - [ ] Add require_permission("reports:view") dependency
  - [ ] Add date range filters
  - [ ] Count applications by status
  - [ ] Calculate conversion rates
  - [ ] Return funnel data

- [ ] Implement `GET /v1/reports/branch-performance`
  - [ ] Add require_permission("reports:view") dependency
  - [ ] Add date range filters
  - [ ] Count applications per branch
  - [ ] Count conversions per branch
  - [ ] Calculate conversion rate
  - [ ] Calculate total sales value
  - [ ] Return branch performance data

**Testing:**
- [ ] Test inventory report
- [ ] Test application funnel report
- [ ] Test branch performance report
- [ ] Test date range filtering
- [ ] Test permission enforcement

---

## 🏗️ Phase 4: Public Website Frontend

### Task 4.1: Create Public Layout

**File:** `frontend/src/app/(public)/layout.tsx`

**Subtasks:**
- [ ] Create (public) route group directory
- [ ] Create layout component
- [ ] Design public header
  - [ ] Logo/branding
  - [ ] Navigation: Home, Bicycles, Branches, Apply
  - [ ] No user menu (public site)
- [ ] Design footer
  - [ ] Branch contact info
  - [ ] Social media links
  - [ ] Copyright notice
- [ ] Add Tailwind styling
- [ ] Make responsive (mobile-first)

**File:** `frontend/src/components/public/PublicHeader.tsx`

**Subtasks:**
- [ ] Create header component
- [ ] Add navigation links
- [ ] Add mobile menu (hamburger)
- [ ] Add "Apply Now" CTA button
- [ ] Style with Tailwind
- [ ] Add active link highlighting

**File:** `frontend/src/components/public/PublicFooter.tsx`

**Subtasks:**
- [ ] Create footer component
- [ ] Add quick links section
- [ ] Add contact info section
- [ ] Add social media icons
- [ ] Style with Tailwind

**Testing:**
- [ ] Test layout renders correctly
- [ ] Test navigation links work
- [ ] Test mobile menu works
- [ ] Test footer displays correctly
- [ ] Test responsive design

---

### Task 4.2: Build Public Home Page

**File:** `frontend/src/app/(public)/page.tsx`

**Subtasks:**
- [ ] Create page component (server component)
- [ ] Fetch featured bicycles (8 items)
- [ ] Design hero section
  - [ ] Headline
  - [ ] Subheadline
  - [ ] CTA buttons (Browse, Apply)
  - [ ] Background image or gradient
- [ ] Design featured bicycles section
  - [ ] Section title
  - [ ] 4-column grid on desktop
  - [ ] Use BicycleCard component
- [ ] Design "How It Works" section
  - [ ] 4 step cards
  - [ ] Icon for each step
  - [ ] Title and description
- [ ] Design "Why Choose Us" section
  - [ ] Benefits list
  - [ ] Trust indicators
- [ ] Add call-to-action section
  - [ ] "Ready to Apply?" CTA
  - [ ] Button to application form

**File:** `frontend/src/components/public/BicycleCard.tsx`

**Subtasks:**
- [ ] Create card component
- [ ] Display bicycle image (thumbnail)
- [ ] Display title
- [ ] Display brand and year
- [ ] Display cash price
- [ ] Display "From X/month" estimate
- [ ] Display NEW/USED badge
- [ ] Display branch name
- [ ] Add hover effect
- [ ] Link to bicycle detail page
- [ ] Style with Tailwind

**Testing:**
- [ ] Test home page renders
- [ ] Test featured bicycles display
- [ ] Test all sections display correctly
- [ ] Test CTA buttons work
- [ ] Test responsive layout
- [ ] Test bicycle cards link correctly

---

### Task 4.3: Build Bicycle Catalog Page

**File:** `frontend/src/app/(public)/bicycles/page.tsx`

**Subtasks:**
- [ ] Create page component (server component)
- [ ] Read query parameters for filters
- [ ] Fetch bicycles with filters from API
- [ ] Display filters sidebar (or top bar on mobile)
- [ ] Display bicycle grid
- [ ] Implement pagination
- [ ] Show loading state
- [ ] Show empty state if no bicycles

**File:** `frontend/src/components/public/BicycleFilters.tsx`

**Subtasks:**
- [ ] Create filters component (client component)
- [ ] Add condition filter (New/Used/All)
- [ ] Add branch filter (dropdown)
- [ ] Add price range filter (min/max inputs)
- [ ] Add brand filter (dropdown or checkboxes)
- [ ] Add search input
- [ ] Add "Clear filters" button
- [ ] Update URL query params on filter change
- [ ] Style with Tailwind

**File:** `frontend/src/components/public/BicycleGrid.tsx`

**Subtasks:**
- [ ] Create grid component
- [ ] Accept bicycles array prop
- [ ] Display in responsive grid
- [ ] Use BicycleCard component
- [ ] Show count (X bicycles found)

**File:** `frontend/src/components/public/Pagination.tsx`

**Subtasks:**
- [ ] Create pagination component
- [ ] Accept total, offset, limit props
- [ ] Calculate total pages
- [ ] Display page numbers
- [ ] Add prev/next buttons
- [ ] Update URL on page change
- [ ] Style with Tailwind

**Testing:**
- [ ] Test catalog page loads
- [ ] Test filters work
- [ ] Test search works
- [ ] Test pagination works
- [ ] Test URL updates with filters
- [ ] Test responsive layout
- [ ] Test empty state

---

### Task 4.4: Build Bicycle Detail Page

**File:** `frontend/src/app/(public)/bicycles/[id]/page.tsx`

**Subtasks:**
- [ ] Create page component (server component)
- [ ] Fetch bicycle by ID from API
- [ ] Handle 404 if not found
- [ ] Display bicycle details
- [ ] Add breadcrumbs (Home > Bicycles > [Title])
- [ ] Pre-populate application form link

**Layout sections:**
- [ ] Image section (left/top)
  - [ ] Main image display
  - [ ] Thumbnail gallery
  - [ ] Image carousel/lightbox

- [ ] Details section (right/bottom)
  - [ ] Title and brand
  - [ ] Year, condition badge
  - [ ] License plate
  - [ ] Mileage (if used)
  - [ ] Branch location
  - [ ] Description

- [ ] Pricing section
  - [ ] Cash price (prominent)
  - [ ] Hire purchase price
  - [ ] Duty amount
  - [ ] Registration fee

- [ ] Finance calculator section
  - [ ] Use FinanceCalculator component

- [ ] CTA section
  - [ ] "Apply for this bicycle" button
  - [ ] Branch contact info

**File:** `frontend/src/components/public/FinanceCalculator.tsx`

**Subtasks:**
- [ ] Create calculator component (client component)
- [ ] Accept hirePurchasePrice prop
- [ ] Add tenure selector (12/24/36/48 months)
- [ ] Add down payment input
- [ ] Calculate financed amount
- [ ] Calculate estimated monthly payment
- [ ] Display calculation breakdown
- [ ] Add disclaimer text
- [ ] Style with Tailwind

**File:** `frontend/src/components/public/ImageGallery.tsx`

**Subtasks:**
- [ ] Create gallery component
- [ ] Display main image large
- [ ] Display thumbnails below
- [ ] Click thumbnail to change main image
- [ ] Add zoom on click (optional)
- [ ] Add next/prev arrows
- [ ] Make responsive

**Testing:**
- [ ] Test detail page loads
- [ ] Test 404 handling
- [ ] Test image gallery works
- [ ] Test finance calculator works
- [ ] Test calculations are correct
- [ ] Test apply button pre-fills form
- [ ] Test responsive layout

---

### Task 4.5: Build Application Form

**File:** `frontend/src/app/(public)/apply/page.tsx`

**Subtasks:**
- [ ] Create page component (client component)
- [ ] Read query params (bikeId, branchId)
- [ ] Fetch available bicycles
- [ ] Fetch available branches
- [ ] Create form state management
- [ ] Implement form submission
- [ ] Show success message after submit
- [ ] Show error message if submission fails

**Form sections:**
- [ ] Bicycle selection
  - [ ] Bicycle dropdown (pre-selected if from detail page)
  - [ ] Branch dropdown (pre-selected if from detail page)
  - [ ] Tenure selector (12/24/36/48 months)
  - [ ] Down payment input

- [ ] Customer details
  - [ ] Full name (required)
  - [ ] Phone number (required)
  - [ ] Email (optional)
  - [ ] NIP number (required, with validation)

- [ ] Address
  - [ ] Address line 1 (required)
  - [ ] Address line 2 (optional)
  - [ ] City (required)

- [ ] Employment
  - [ ] Employer name (optional)
  - [ ] Monthly income (optional, but recommended)

- [ ] Terms and conditions
  - [ ] Checkbox to accept T&C
  - [ ] Link to T&C document

- [ ] Submit button
  - [ ] Disabled until form valid
  - [ ] Show loading state
  - [ ] Submit to API

**File:** `frontend/src/components/public/ApplicationForm.tsx`

**Subtasks:**
- [ ] Create form component
- [ ] Implement form validation
  - [ ] Required field validation
  - [ ] Email format validation
  - [ ] Phone format validation
  - [ ] NIP format validation
  - [ ] Numeric validation for income
- [ ] Show validation errors inline
- [ ] Implement progressive disclosure (multi-step form optional)
- [ ] Style with Tailwind
- [ ] Make responsive

**File:** `frontend/src/components/public/ApplicationSuccess.tsx`

**Subtasks:**
- [ ] Create success message component
- [ ] Display confirmation message
- [ ] Display application ID
- [ ] Display next steps
- [ ] Display branch contact info
- [ ] Add "Apply for another bicycle" button
- [ ] Add "Back to home" button

**Testing:**
- [ ] Test form renders
- [ ] Test pre-filled values work
- [ ] Test validation works
- [ ] Test required fields enforced
- [ ] Test form submission
- [ ] Test success message displays
- [ ] Test error handling
- [ ] Test responsive layout

---

### Task 4.6: Build Branches Page

**File:** `frontend/src/app/(public)/branches/page.tsx`

**Subtasks:**
- [ ] Create page component (server component)
- [ ] Fetch all branches from API
- [ ] Display branches in grid
- [ ] Use BranchCard component

**File:** `frontend/src/components/public/BranchCard.tsx`

**Subtasks:**
- [ ] Create card component
- [ ] Display branch name
- [ ] Display address
- [ ] Display phone number
- [ ] Display operating hours
- [ ] Display description
- [ ] Add "View on map" link
- [ ] Add "View bicycles at this branch" link
- [ ] Style with Tailwind

**Optional: Map integration**
- [ ] Integrate Google Maps or Mapbox
- [ ] Show all branches on map
- [ ] Add markers for each branch
- [ ] Click marker to show branch info

**Testing:**
- [ ] Test branches page loads
- [ ] Test all branches display
- [ ] Test branch cards show correct info
- [ ] Test links work
- [ ] Test map integration (if implemented)

---

## 🏗️ Phase 5: Staff Application Management Frontend

### Task 5.1: Create Applications List Page

**File:** `frontend/src/app/(authenticated)/applications/page.tsx`

**Subtasks:**
- [ ] Create page component (server component)
- [ ] Fetch applications from API
- [ ] Read query params for filters
- [ ] Display applications table
- [ ] Add status filter buttons
- [ ] Add search input
- [ ] Add pagination
- [ ] Show loading state
- [ ] Show empty state

**File:** `frontend/src/components/staff/ApplicationsTable.tsx`

**Subtasks:**
- [ ] Create table component
- [ ] Define table columns
  - [ ] Application ID
  - [ ] Customer name
  - [ ] Bicycle
  - [ ] Branch
  - [ ] Submitted date
  - [ ] Status badge
  - [ ] Actions (View/Review)
- [ ] Make table sortable
- [ ] Add row click to navigate to detail
- [ ] Style with Tailwind
- [ ] Make responsive (card view on mobile)

**File:** `frontend/src/components/staff/ApplicationStatusBadge.tsx`

**Subtasks:**
- [ ] Create badge component
- [ ] Style each status differently
  - [ ] PENDING: yellow
  - [ ] UNDER_REVIEW: blue
  - [ ] APPROVED: green
  - [ ] REJECTED: red
  - [ ] CONVERTED_TO_LOAN: purple
- [ ] Style with Tailwind

**File:** `frontend/src/components/staff/ApplicationFilters.tsx`

**Subtasks:**
- [ ] Create filters component (client component)
- [ ] Add status filter (buttons or dropdown)
- [ ] Add branch filter (dropdown)
- [ ] Add date range filter
- [ ] Add search input
- [ ] Update URL query params on change
- [ ] Style with Tailwind

**Testing:**
- [ ] Test applications list loads
- [ ] Test filters work
- [ ] Test search works
- [ ] Test sorting works
- [ ] Test pagination works
- [ ] Test row click navigation
- [ ] Test status badges display correctly
- [ ] Test branch filtering for branch managers

---

### Task 5.2: Create Application Detail Page

**File:** `frontend/src/app/(authenticated)/applications/[id]/page.tsx`

**Subtasks:**
- [ ] Create page component (server component)
- [ ] Fetch application by ID
- [ ] Handle 404 if not found
- [ ] Display application details
- [ ] Add breadcrumbs
- [ ] Show review actions if user has permission

**Layout sections:**
- [ ] Customer information card
  - [ ] Full name
  - [ ] Phone, email
  - [ ] NIP number
  - [ ] Address
  - [ ] Employer and income

- [ ] Bicycle information card
  - [ ] Bicycle details
  - [ ] Photos
  - [ ] Pricing
  - [ ] Link to bicycle detail

- [ ] Financial details card
  - [ ] Tenure
  - [ ] Down payment
  - [ ] Financed amount
  - [ ] Estimated monthly payment

- [ ] Application timeline
  - [ ] Submitted date
  - [ ] Reviewed date (if applicable)
  - [ ] Reviewed by (if applicable)
  - [ ] Status changes

- [ ] Review actions panel (sidebar)
  - [ ] Approve button
  - [ ] Reject button (with notes input)
  - [ ] Status display
  - [ ] Notes display

**File:** `frontend/src/components/staff/CustomerInfoCard.tsx`

**Subtasks:**
- [ ] Create card component
- [ ] Display customer details in sections
- [ ] Make fields copyable (click to copy)
- [ ] Style with Tailwind

**File:** `frontend/src/components/staff/BicycleInfoCard.tsx`

**Subtasks:**
- [ ] Create card component
- [ ] Display bicycle details
- [ ] Show thumbnail
- [ ] Add link to bicycle page
- [ ] Style with Tailwind

**File:** `frontend/src/components/staff/FinanceDetailsCard.tsx`

**Subtasks:**
- [ ] Create card component
- [ ] Display finance breakdown
- [ ] Calculate and show totals
- [ ] Style with Tailwind

**File:** `frontend/src/components/staff/ApplicationReviewPanel.tsx`

**Subtasks:**
- [ ] Create panel component (client component)
- [ ] Check user permissions
- [ ] Show approve button if has permission
- [ ] Show reject button with notes input
- [ ] Implement approve action
  - [ ] Call API endpoint
  - [ ] Show loading state
  - [ ] Show success message
  - [ ] Refresh page data
- [ ] Implement reject action
  - [ ] Validate notes provided
  - [ ] Call API endpoint
  - [ ] Show loading state
  - [ ] Show success message
  - [ ] Refresh page data
- [ ] Show confirmation dialogs
- [ ] Style with Tailwind

**Testing:**
- [ ] Test detail page loads
- [ ] Test 404 handling
- [ ] Test all cards display correctly
- [ ] Test approve button works
- [ ] Test reject button works
- [ ] Test validation for reject notes
- [ ] Test confirmation dialogs
- [ ] Test permission-based UI hiding
- [ ] Test success/error messages

---

### Task 5.3: Add Real-Time Updates (Optional)

**File:** `backend/app/websocket.py`

**Subtasks:**
- [ ] Create WebSocket endpoint
- [ ] Implement connection manager
- [ ] Broadcast new application events
- [ ] Broadcast status change events
- [ ] Add authentication to WebSocket

**File:** `frontend/src/lib/websocket.ts`

**Subtasks:**
- [ ] Create WebSocket client
- [ ] Handle connection/reconnection
- [ ] Listen for application events
- [ ] Emit events to components

**File:** `frontend/src/app/(authenticated)/applications/page.tsx` (update)

**Subtasks:**
- [ ] Connect to WebSocket
- [ ] Listen for new application events
- [ ] Refresh table on event
- [ ] Show notification toast
- [ ] Disconnect on unmount

**Testing:**
- [ ] Test WebSocket connection
- [ ] Test new application notification
- [ ] Test table auto-refresh
- [ ] Test reconnection on disconnect
- [ ] Test multiple clients

---

## 🏗️ Phase 6: Staff Inventory Management Frontend

### Task 6.1: Create Bicycle Inventory List Page

**File:** `frontend/src/app/(authenticated)/inventory/page.tsx`

**Subtasks:**
- [ ] Create page component (server component)
- [ ] Fetch bicycles from API
- [ ] Read query params for filters
- [ ] Display bicycles table
- [ ] Add "Add Bicycle" button
- [ ] Add filters section
- [ ] Add search input
- [ ] Add pagination
- [ ] Show loading state
- [ ] Show empty state

**File:** `frontend/src/components/staff/BicycleInventoryTable.tsx`

**Subtasks:**
- [ ] Create table component
- [ ] Define table columns
  - [ ] Thumbnail
  - [ ] Title
  - [ ] Brand/Model
  - [ ] License plate
  - [ ] Condition
  - [ ] Branch
  - [ ] Status
  - [ ] Cash price
  - [ ] Actions (View/Edit/Delete)
- [ ] Make table sortable
- [ ] Add row click to navigate to detail
- [ ] Add quick status change dropdown
- [ ] Style with Tailwind
- [ ] Make responsive

**File:** `frontend/src/components/staff/BicycleStatusBadge.tsx`

**Subtasks:**
- [ ] Create badge component
- [ ] Style each status differently
  - [ ] AVAILABLE: green
  - [ ] RESERVED: yellow
  - [ ] SOLD: gray
  - [ ] MAINTENANCE: orange
- [ ] Style with Tailwind

**File:** `frontend/src/components/staff/BicycleFilters.tsx`

**Subtasks:**
- [ ] Create filters component (client component)
- [ ] Add condition filter
- [ ] Add status filter
- [ ] Add branch filter
- [ ] Add brand filter
- [ ] Add price range filter
- [ ] Add search input
- [ ] Update URL query params on change
- [ ] Style with Tailwind

**Testing:**
- [ ] Test inventory list loads
- [ ] Test filters work
- [ ] Test search works
- [ ] Test sorting works
- [ ] Test pagination works
- [ ] Test quick status change
- [ ] Test add bicycle button navigation
- [ ] Test branch filtering for branch managers

---

### Task 6.2: Create Add/Edit Bicycle Form

**File:** `frontend/src/app/(authenticated)/inventory/new/page.tsx`

**Subtasks:**
- [ ] Create page component (client component)
- [ ] Fetch branches list
- [ ] Create form state
- [ ] Implement form submission
- [ ] Navigate to detail page on success

**File:** `frontend/src/app/(authenticated)/inventory/[id]/edit/page.tsx`

**Subtasks:**
- [ ] Create page component (client component)
- [ ] Fetch bicycle by ID
- [ ] Fetch branches list
- [ ] Pre-populate form with bicycle data
- [ ] Implement form update submission
- [ ] Navigate to detail page on success

**File:** `frontend/src/components/staff/BicycleForm.tsx`

**Subtasks:**
- [ ] Create form component
- [ ] Add all bicycle fields
  - [ ] Title (required)
  - [ ] Brand (required)
  - [ ] Model (required)
  - [ ] Year (required, numeric)
  - [ ] Condition (required, radio: New/Used)
  - [ ] License plate (required, unique validation)
  - [ ] Frame number
  - [ ] Engine number (for motorcycles)
  - [ ] Mileage (for used, numeric)
  - [ ] Description (textarea)
  - [ ] Branch (required, dropdown)
  - [ ] Purchase price (required, numeric)
  - [ ] Cash price (required, numeric)
  - [ ] Hire purchase price (required, numeric)
  - [ ] Duty amount (numeric)
  - [ ] Registration fee (numeric)
  - [ ] Status (dropdown)
- [ ] Implement validation
  - [ ] Required fields
  - [ ] Numeric fields
  - [ ] Format validation
  - [ ] Hire purchase price >= cash price
- [ ] Show validation errors
- [ ] Style with Tailwind
- [ ] Make responsive

**Testing:**
- [ ] Test add form renders
- [ ] Test edit form pre-populates
- [ ] Test validation works
- [ ] Test form submission (add)
- [ ] Test form submission (edit)
- [ ] Test error handling
- [ ] Test branch permission enforcement
- [ ] Test navigation after submit

---

### Task 6.3: Create Bicycle Detail Page (Staff View)

**File:** `frontend/src/app/(authenticated)/inventory/[id]/page.tsx`

**Subtasks:**
- [ ] Create page component (server component)
- [ ] Fetch bicycle by ID
- [ ] Handle 404 if not found
- [ ] Display bicycle details
- [ ] Add breadcrumbs
- [ ] Add action buttons (Edit, Delete, Change Status)
- [ ] Show related applications

**Layout sections:**
- [ ] Bicycle information
  - [ ] All specifications
  - [ ] Status badge
  - [ ] Branch info
  - [ ] Created/updated dates

- [ ] Images section
  - [ ] Image gallery
  - [ ] Upload new images button
  - [ ] Delete image buttons

- [ ] Pricing section
  - [ ] All pricing fields
  - [ ] Calculated margins

- [ ] Related data
  - [ ] Applications for this bicycle
  - [ ] Loan if sold

**File:** `frontend/src/components/staff/ImageUploadWidget.tsx`

**Subtasks:**
- [ ] Create upload widget component (client component)
- [ ] Accept multiple file selection
- [ ] Show file preview before upload
- [ ] Validate file types and sizes
- [ ] Upload files to API
- [ ] Show upload progress
- [ ] Show success/error messages
- [ ] Refresh bicycle data on success
- [ ] Style with Tailwind

**File:** `frontend/src/components/staff/ImageManager.tsx`

**Subtasks:**
- [ ] Create image manager component
- [ ] Display current images
- [ ] Add upload button
- [ ] Add delete button per image
- [ ] Set thumbnail button
- [ ] Reorder images (drag & drop optional)
- [ ] Style with Tailwind

**Testing:**
- [ ] Test detail page loads
- [ ] Test 404 handling
- [ ] Test all sections display
- [ ] Test edit button navigation
- [ ] Test image upload
- [ ] Test image delete
- [ ] Test related applications display
- [ ] Test permission-based UI hiding

---

### Task 6.4: Implement Bulk Operations

**File:** `frontend/src/app/(authenticated)/inventory/import/page.tsx`

**Subtasks:**
- [ ] Create import page component (client component)
- [ ] Add file upload input (CSV)
- [ ] Download CSV template button
- [ ] Parse CSV on client (optional preview)
- [ ] Upload CSV to API
- [ ] Show import progress
- [ ] Show import results (success/errors)
- [ ] Display errors with row numbers
- [ ] Link to created bicycles

**File:** `frontend/src/components/staff/BulkStatusUpdate.tsx`

**Subtasks:**
- [ ] Create bulk update component (client component)
- [ ] Accept selected bicycle IDs
- [ ] Show status selector
- [ ] Confirm bulk update
- [ ] Call API for each bicycle
- [ ] Show progress
- [ ] Show results
- [ ] Refresh table on completion

**File:** `frontend/src/components/staff/BulkPriceUpdate.tsx`

**Subtasks:**
- [ ] Create bulk price update component
- [ ] Accept selected bicycle IDs
- [ ] Show price adjustment options
  - [ ] Fixed amount
  - [ ] Percentage increase/decrease
- [ ] Preview changes
- [ ] Confirm bulk update
- [ ] Call API for each bicycle
- [ ] Show results

**Testing:**
- [ ] Test CSV template download
- [ ] Test CSV upload
- [ ] Test validation errors display
- [ ] Test successful import
- [ ] Test bulk status update
- [ ] Test bulk price update
- [ ] Test progress indicators

---

### Task 6.5: Create Branch Management UI

**File:** `frontend/src/app/(authenticated)/branches/page.tsx`

**Subtasks:**
- [ ] Create page component (server component)
- [ ] Fetch branches from API
- [ ] Display branches table/list
- [ ] Add "Add Branch" button
- [ ] Add edit buttons per branch

**File:** `frontend/src/components/staff/BranchForm.tsx`

**Subtasks:**
- [ ] Create form component (client component)
- [ ] Add branch fields
  - [ ] Name (required)
  - [ ] Code (required)
  - [ ] Address (required)
  - [ ] Phone (required)
  - [ ] Email
  - [ ] Allows bicycle sales (checkbox)
  - [ ] Display order (numeric)
  - [ ] Operating hours (textarea)
  - [ ] Public description (textarea)
  - [ ] Map coordinates (optional, lat/lng inputs)
- [ ] Implement validation
- [ ] Implement submission
- [ ] Style with Tailwind

**Testing:**
- [ ] Test branches page loads
- [ ] Test add branch
- [ ] Test edit branch
- [ ] Test validation
- [ ] Test form submission
- [ ] Test admin-only access

---

## 🏗️ Phase 7: Integration & Polish

### Task 7.1: Link Applications to Loans

**File:** `backend/app/routers/bicycle_applications.py` (update)

**Subtasks:**
- [ ] Update approve endpoint to create collateral
- [ ] Link bicycle to loan as collateral
- [ ] Set collateral type to VEHICLE
- [ ] Set collateral value to bicycle hire_purchase_price
- [ ] Store bicycle_id in collateral details (JSONB)

**File:** `backend/app/routers/loans.py` (extend existing)

**Subtasks:**
- [ ] Update loan disbursement endpoint
- [ ] On disburse, update bicycle status to SOLD
- [ ] Create transaction record for bicycle sale
- [ ] Link collateral to loan

**File:** `frontend/src/app/(authenticated)/applications/[id]/page.tsx` (update)

**Subtasks:**
- [ ] Show linked loan ID if converted
- [ ] Add link to loan detail page
- [ ] Show loan status

**Testing:**
- [ ] Test approve creates loan
- [ ] Test loan is linked to application
- [ ] Test bicycle is linked as collateral
- [ ] Test disburse updates bicycle status
- [ ] Test UI shows linked loan

---

### Task 7.2: Add Dashboard Widgets

**File:** `frontend/src/app/(authenticated)/dashboard/page.tsx` (extend existing)

**Subtasks:**
- [ ] Add application pipeline widget
- [ ] Add bicycle inventory widget
- [ ] Add branch performance widget

**File:** `frontend/src/components/staff/ApplicationPipelineWidget.tsx`

**Subtasks:**
- [ ] Create widget component
- [ ] Fetch application counts by status
- [ ] Display as funnel or bar chart
- [ ] Show conversion rates
- [ ] Link to applications page
- [ ] Style with Tailwind

**File:** `frontend/src/components/staff/InventoryStatusWidget.tsx`

**Subtasks:**
- [ ] Create widget component
- [ ] Fetch bicycle counts by status
- [ ] Display as donut chart or bars
- [ ] Show total inventory value
- [ ] Link to inventory page
- [ ] Style with Tailwind

**File:** `frontend/src/components/staff/BranchPerformanceWidget.tsx`

**Subtasks:**
- [ ] Create widget component
- [ ] Fetch branch performance data
- [ ] Display top performing branches
- [ ] Show conversion rates
- [ ] Link to branch page
- [ ] Style with Tailwind

**Optional: Chart Library**
- [ ] Choose chart library (recharts, chart.js, visx)
- [ ] Install and configure
- [ ] Create chart components

**Testing:**
- [ ] Test widgets load data
- [ ] Test charts display correctly
- [ ] Test links work
- [ ] Test responsive layout
- [ ] Test permission-based display

---

### Task 7.3: Implement Search

**File:** `backend/app/routers/search.py` (new)

**Subtasks:**
- [ ] Create search router
- [ ] Implement `GET /v1/search?q={query}`
  - [ ] Search bicycles by title, brand, model, license plate
  - [ ] Search applications by customer name, NIP, phone
  - [ ] Search clients by name, NIP
  - [ ] Return combined results with type
- [ ] Add relevance scoring
- [ ] Add pagination
- [ ] Add filters (type: bicycle/application/client)

**File:** `frontend/src/components/staff/GlobalSearch.tsx`

**Subtasks:**
- [ ] Create search component (client component)
- [ ] Add search input in header
- [ ] Implement autocomplete dropdown
- [ ] Show results grouped by type
- [ ] Navigate on result click
- [ ] Implement keyboard navigation
- [ ] Style with Tailwind

**Optional: Elasticsearch Integration**
- [ ] Install Elasticsearch
- [ ] Create indexes for bicycles, applications, clients
- [ ] Sync data to Elasticsearch
- [ ] Update search endpoint to use Elasticsearch
- [ ] Implement advanced search features

**Testing:**
- [ ] Test search finds bicycles
- [ ] Test search finds applications
- [ ] Test search finds clients
- [ ] Test autocomplete works
- [ ] Test navigation works
- [ ] Test keyboard navigation

---

### Task 7.4: Add Analytics

**File:** `frontend/src/app/(public)/layout.tsx` (update)

**Subtasks:**
- [ ] Add Google Analytics script
- [ ] Set up GA4 measurement ID
- [ ] Track page views
- [ ] Track custom events (application submissions)

**File:** `frontend/src/lib/analytics.ts`

**Subtasks:**
- [ ] Create analytics helper functions
- [ ] Implement `trackEvent(eventName, properties)`
- [ ] Implement `trackApplicationSubmission(applicationId)`
- [ ] Implement `trackBicycleView(bicycleId)`
- [ ] Implement `trackConversion(loanId)`

**File:** `backend/app/routers/analytics.py` (new)

**Subtasks:**
- [ ] Create analytics router
- [ ] Implement `GET /v1/analytics/funnel`
  - [ ] Calculate conversion rates
  - [ ] Group by date, branch
- [ ] Implement `GET /v1/analytics/bicycle-views`
  - [ ] Track bicycle page views
  - [ ] Most viewed bicycles
- [ ] Implement `GET /v1/analytics/user-activity`
  - [ ] Track staff activity
  - [ ] Active users by role

**Testing:**
- [ ] Test GA tracking works
- [ ] Test events fire correctly
- [ ] Test analytics endpoints return data
- [ ] Test dashboard displays analytics

---

## 🏗️ Phase 8: Testing & Deployment

### Task 8.1: Write Backend Tests

**File:** `backend/tests/test_bicycles.py`

**Subtasks:**
- [ ] Test list bicycles endpoint
- [ ] Test create bicycle endpoint
- [ ] Test update bicycle endpoint
- [ ] Test delete bicycle endpoint
- [ ] Test image upload endpoint
- [ ] Test validation errors
- [ ] Test permissions (different roles)

**File:** `backend/tests/test_applications.py`

**Subtasks:**
- [ ] Test submit application (public)
- [ ] Test list applications (staff)
- [ ] Test approve application
- [ ] Test reject application
- [ ] Test permissions (different roles)
- [ ] Test branch filtering for branch managers

**File:** `backend/tests/test_rbac.py`

**Subtasks:**
- [ ] Test require_permission function
- [ ] Test each role's permissions
- [ ] Test wildcard permissions
- [ ] Test branch access control
- [ ] Test permission denial raises 403

**File:** `backend/tests/test_services.py`

**Subtasks:**
- [ ] Test get_or_create_client
- [ ] Test create_loan_from_application
- [ ] Test reserve_bicycle
- [ ] Test release_bicycle_reservation

**Testing:**
- [ ] Run all tests: `pytest`
- [ ] Check test coverage: `pytest --cov`
- [ ] Aim for >80% coverage

---

### Task 8.2: Write Frontend Tests

**File:** `frontend/src/components/public/__tests__/BicycleCard.test.tsx`

**Subtasks:**
- [ ] Test component renders
- [ ] Test props display correctly
- [ ] Test link navigation
- [ ] Test hover effects

**File:** `frontend/src/components/public/__tests__/FinanceCalculator.test.tsx`

**Subtasks:**
- [ ] Test calculations are correct
- [ ] Test tenure selection updates
- [ ] Test down payment updates
- [ ] Test displays correctly

**File:** `frontend/src/components/staff/__tests__/ApplicationReviewPanel.test.tsx`

**Subtasks:**
- [ ] Test approve button works
- [ ] Test reject button requires notes
- [ ] Test API calls made correctly
- [ ] Test success/error states

**E2E Tests (Playwright/Cypress):**
- [ ] Test customer application flow
  - [ ] Browse bicycles
  - [ ] View bicycle detail
  - [ ] Fill application form
  - [ ] Submit application
- [ ] Test staff approval flow
  - [ ] Login as sales agent
  - [ ] View applications list
  - [ ] Review application
  - [ ] Approve application
  - [ ] Verify loan created
- [ ] Test inventory management flow
  - [ ] Login as inventory manager
  - [ ] Add new bicycle
  - [ ] Upload images
  - [ ] Update bicycle
  - [ ] Change status

**Testing:**
- [ ] Run component tests: `npm test`
- [ ] Run E2E tests: `npx playwright test`
- [ ] Check test coverage

---

### Task 8.3: Performance Optimization

**Database:**
- [ ] Review and optimize slow queries
- [ ] Add missing indexes
- [ ] Enable query caching where appropriate
- [ ] Configure connection pooling

**Backend:**
- [ ] Add response caching for public endpoints
- [ ] Enable gzip compression
- [ ] Optimize image resize operations
- [ ] Add rate limiting
- [ ] Enable API response caching

**Frontend:**
- [ ] Optimize images
  - [ ] Use Next.js Image component
  - [ ] Implement lazy loading
  - [ ] Generate WebP versions
- [ ] Code splitting
  - [ ] Dynamic imports for heavy components
  - [ ] Route-based splitting
- [ ] Enable caching
  - [ ] API response caching
  - [ ] Static asset caching
- [ ] Optimize fonts
  - [ ] Self-host fonts
  - [ ] Use font-display: swap

**CDN Setup:**
- [ ] Configure CDN for static assets
- [ ] Configure CDN for images
- [ ] Set cache headers
- [ ] Enable CDN compression

**Testing:**
- [ ] Run Lighthouse audit
- [ ] Test page load times
- [ ] Test API response times
- [ ] Optimize to achieve:
  - [ ] LCP < 2.5s
  - [ ] FID < 100ms
  - [ ] CLS < 0.1

---

### Task 8.4: Security Audit

**Backend Security:**
- [ ] SQL injection testing
  - [ ] Test all query parameters
  - [ ] Test search inputs
- [ ] Authentication testing
  - [ ] Test JWT validation
  - [ ] Test token expiration
  - [ ] Test refresh token flow
- [ ] Authorization testing
  - [ ] Test RBAC permissions
  - [ ] Test branch access control
  - [ ] Test privilege escalation attempts
- [ ] Input validation
  - [ ] Test file upload validation
  - [ ] Test field length limits
  - [ ] Test special character handling
- [ ] Rate limiting
  - [ ] Test API rate limits
  - [ ] Test login rate limits

**Frontend Security:**
- [ ] XSS testing
  - [ ] Test user input sanitization
  - [ ] Test URL parameter handling
- [ ] CSRF protection
  - [ ] Verify CSRF tokens
- [ ] Secure headers
  - [ ] CSP headers
  - [ ] X-Frame-Options
  - [ ] X-Content-Type-Options

**Sensitive Data:**
- [ ] Ensure passwords are hashed (upgrade from SHA256 to bcrypt)
- [ ] Ensure NIP numbers are encrypted at rest
- [ ] Ensure sensitive data not in logs
- [ ] Ensure JWT keys are securely stored

**Penetration Testing:**
- [ ] Run OWASP ZAP scan
- [ ] Run Burp Suite scan
- [ ] Manual testing of critical flows
- [ ] Fix all High/Critical findings

**Testing:**
- [ ] Run security audit tools
- [ ] Fix all identified vulnerabilities
- [ ] Re-test after fixes
- [ ] Document security measures

---

### Task 8.5: Deployment

**Infrastructure Setup:**
- [ ] Provision servers (or use cloud platform)
  - [ ] Backend server (VM or container)
  - [ ] Frontend server (Vercel/Netlify or VM)
  - [ ] Database server (managed PostgreSQL)
  - [ ] Storage server (S3 or equivalent)
- [ ] Configure networking
  - [ ] Set up DNS
  - [ ] Configure SSL certificates
  - [ ] Set up load balancer (if needed)
- [ ] Configure monitoring
  - [ ] Set up error tracking (Sentry)
  - [ ] Set up logging (CloudWatch, Datadog)
  - [ ] Set up uptime monitoring
  - [ ] Set up performance monitoring

**CI/CD Pipeline:**
- [ ] Set up GitHub Actions (or equivalent)
- [ ] Create staging deployment workflow
  - [ ] Run tests
  - [ ] Deploy backend to staging
  - [ ] Deploy frontend to staging
  - [ ] Run smoke tests
- [ ] Create production deployment workflow
  - [ ] Require manual approval
  - [ ] Deploy backend to production
  - [ ] Deploy frontend to production
  - [ ] Run smoke tests
- [ ] Set up database migrations in CI
- [ ] Set up rollback procedure

**Environment Configuration:**
- [ ] Set up staging environment
  - [ ] Staging database
  - [ ] Staging API URL
  - [ ] Test data
- [ ] Set up production environment
  - [ ] Production database
  - [ ] Production API URL
  - [ ] Backup strategy
- [ ] Configure environment variables
  - [ ] Database URLs
  - [ ] JWT secrets
  - [ ] Storage credentials
  - [ ] Email settings
  - [ ] Analytics IDs

**Database:**
- [ ] Run migrations on staging
- [ ] Run migrations on production
- [ ] Seed initial data (branches, loan products, admin user)
- [ ] Set up backup strategy
  - [ ] Daily automated backups
  - [ ] Backup retention policy
  - [ ] Test restore procedure

**Monitoring & Alerts:**
- [ ] Set up error alerts
- [ ] Set up performance alerts
- [ ] Set up downtime alerts
- [ ] Set up disk space alerts
- [ ] Set up database connection alerts

**Testing:**
- [ ] Test staging deployment
- [ ] Run UAT on staging
- [ ] Test production deployment
- [ ] Run smoke tests on production
- [ ] Monitor errors and performance

---

## 📝 Implementation Checklist Summary

### Sprint 1: Database & Backend Foundation ✅
- [ ] Migration file created and tested
- [ ] SQLAlchemy models created
- [ ] RBAC system extended
- [ ] Default data seeded

### Sprint 2: Public API & Core Business Logic ✅
- [ ] Public bicycle catalog API working
- [ ] Application submission API working
- [ ] Business logic services implemented
- [ ] Notification system working

### Sprint 3: Staff Bicycle Inventory Management ✅
- [ ] Bicycle inventory API complete
- [ ] Image upload working
- [ ] Bulk import working
- [ ] Branch management extended
- [ ] Reporting endpoints working

### Sprint 4: Public Website Frontend ✅
- [ ] Public layout complete
- [ ] Home page live
- [ ] Bicycle catalog working
- [ ] Bicycle detail page working
- [ ] Application form working
- [ ] Branches page working

### Sprint 5: Staff Application Management Frontend ✅
- [ ] Applications list working
- [ ] Application detail and review working
- [ ] Real-time updates working (optional)
- [ ] Role-based UI working

### Sprint 6: Staff Inventory Management Frontend ✅
- [ ] Bicycle inventory list working
- [ ] Add/edit bicycle forms working
- [ ] Bicycle detail page working
- [ ] Image management working
- [ ] Bulk operations working
- [ ] Branch management UI working

### Sprint 7: Integration & Polish ✅
- [ ] Applications linked to loans
- [ ] Dashboard widgets working
- [ ] Search implemented
- [ ] Analytics implemented

### Sprint 8: Testing & Deployment ✅
- [ ] Backend tests written and passing
- [ ] Frontend tests written and passing
- [ ] Performance optimized
- [ ] Security audit complete
- [ ] Deployed to production

---

## 🎯 Success Metrics

### Technical Metrics
- [ ] Test coverage >80%
- [ ] Lighthouse score >90
- [ ] API response time <200ms (p95)
- [ ] Page load time <2s
- [ ] Zero critical security vulnerabilities

### Business Metrics
- [ ] Application submission rate
- [ ] Application approval rate
- [ ] Time to approval <48 hours
- [ ] Conversion rate (application → loan)
- [ ] Customer satisfaction score

---

## 📚 Resources

### Documentation to Create
- [ ] API documentation (OpenAPI/Swagger)
- [ ] User manual (staff)
- [ ] User guide (customers)
- [ ] Deployment guide
- [ ] Troubleshooting guide

### Training Materials
- [ ] Staff training videos
- [ ] Role-specific guides
- [ ] FAQ document
- [ ] Contact support procedures

---

## 🚀 Post-Launch Tasks

### Week 1 After Launch
- [ ] Monitor error rates
- [ ] Monitor performance
- [ ] Collect user feedback
- [ ] Fix critical bugs
- [ ] Optimize slow queries

### Month 1 After Launch
- [ ] Analyze usage patterns
- [ ] Review conversion funnel
- [ ] Implement user feedback
- [ ] Add minor feature improvements
- [ ] Update documentation

### Ongoing
- [ ] Regular security updates
- [ ] Dependency updates
- [ ] Performance monitoring
- [ ] Feature requests review
- [ ] User support

---

**Last Updated:** 2025-11-18
**Status:** Draft - Ready for Implementation
**Estimated Timeline:** 8 weeks (with 1-2 developers)
