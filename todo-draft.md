# Bicycle Hire Purchase System - Integration Plan

## 📋 Executive Summary

This document contains the complete integration plan for adding a **Bicycle Hire Purchase System** to the existing Loan Manager application. The plan leverages the existing FastAPI backend, PostgreSQL database, JWT authentication, and RBAC system.

### System Overview

**Current System:**
- Backend: FastAPI + SQLAlchemy async ORM
- Frontend: Next.js 15 + React Server Components
- Database: PostgreSQL with asyncpg
- Auth: JWT with HttpOnly cookies + RBAC
- Infrastructure: Existing loan management, client management, reference data

**New Features:**
- Public bicycle catalog (no authentication)
- Customer application portal
- Staff bicycle inventory management
- Application review workflow
- Multi-branch support with branch-scoped access control
- Enhanced RBAC for 6+ user roles

---

## 🎯 Core Features

### Public Website
1. Home page with featured bicycles
2. Bicycle catalog with filters (condition, branch, price, brand)
3. Bicycle detail page with finance calculator
4. Application form for hire purchase
5. Branch listing page

### Staff Back-Office
1. Application management (list, review, approve/reject)
2. Bicycle inventory management (CRUD, images, bulk operations)
3. Branch management
4. Role-based access control
5. Dashboard with widgets
6. Reporting and analytics

---

## 🏗️ Phase 1: Database Schema Extensions

### New Tables

#### 1. `bicycles` Table
- Stores bicycle inventory
- Links to branches
- Tracks status (AVAILABLE, RESERVED, SOLD, MAINTENANCE)
- Stores pricing (purchase, cash, hire purchase)
- Stores images as JSONB array

#### 2. `bicycle_applications` Table
- Customer application data
- Links to bicycle and branch
- Tracks application status workflow
- Links to created loan when approved

#### 3. Extended `offices` Table
- New fields for bicycle sales configuration
- Map coordinates for public display
- Operating hours and public description

---

## 🔐 Phase 2: Enhanced RBAC System

### New User Roles

    ADMIN = "admin"              # Full system access
      USER = "user"                # Basic staff access

      # New bicycle hire purchase roles
      BRANCH_MANAGER = "branch_manager"      # Manages single branch
      SALES_AGENT = "sales_agent"            # Reviews applications, creates loans
      INVENTORY_MANAGER = "inventory_manager"  # Manages bicycle inventory
      FINANCE_OFFICER = "finance_officer"    # Approves loans, manages payments
      CUSTOMER_SERVICE = "customer_service"  # Views applications, communicates with customers
      AUDITOR = "auditor"                    # Read-only access to all data

      # Public (no auth required for catalog browsing)
      PUBLIC = "public"

  # Role hierarchy and permissions
  ROLE_PERMISSIONS = {
      UserRole.ADMIN: ["*"],  # All permissions

      UserRole.BRANCH_MANAGER: [
          "bicycles:read", "bicycles:write", "bicycles:delete",
          "applications:read", "applications:write", "applications:approve",
          "loans:read", "loans:create",
          "branches:read",  # Can only view, not modify
          "reports:branch",
      ],

      UserRole.SALES_AGENT: [
          "bicycles:read",
          "applications:read", "applications:write", "applications:review",
          "loans:read", "loans:create",
          "clients:read", "clients:write",
          "branches:read",
      ],

      UserRole.INVENTORY_MANAGER: [
          "bicycles:read", "bicycles:write",
          "documents:read", "documents:write",  # For bicycle photos
          "branches:read",
      ],

      UserRole.FINANCE_OFFICER: [
          "loans:read", "loans:approve", "loans:disburse",
          "applications:read",
          "clients:read",
          "reports:financial",
      ],

      UserRole.CUSTOMER_SERVICE: [
          "applications:read", "applications:write",
          "bicycles:read",
          "clients:read", "clients:write",
          "branches:read",
      ],

      UserRole.AUDITOR: [
          "*.read",  # Read-only wildcard
      ],
  }

  2.2 Enhanced Permission Checking

  # backend/app/rbac.py
  def require_permission(permission: str):
      """
      Dependency that checks if user has specific permission.
      Usage: @router.get("/endpoint", dependencies=[Depends(require_permission("bicycles:write"))])
      """
      async def check_permission(user: User = Depends(get_current_user)):
          if "admin" in user.roles:
              return user  # Admins have all permissions

          user_permissions = []
          for role in user.roles:
              user_permissions.extend(ROLE_PERMISSIONS.get(role, []))

          # Check wildcard permissions
          if "*" in user_permissions:
              return user

          # Check exact match
          if permission in user_permissions:
              return user

          # Check wildcard patterns (e.g., "*.read")
          for perm in user_permissions:
              if perm.endswith(".*") and permission.startswith(perm[:-1]):
                  return user
              if perm.endswith(".read") and permission.startswith(perm.split(":")[0]):
                  return user

          raise HTTPException(
              status_code=403,
              detail=f"Permission denied: {permission}"
          )

      return check_permission

  # Branch-scoped access control
  def require_branch_access(branch_id: str, user: User):
      """Check if user has access to specific branch"""
      if "admin" in user.roles:
          return True

      # Branch managers only access their branch
      if "branch_manager" in user.roles:
          if user.metadata.get("branch_id") != branch_id:
              raise HTTPException(403, "Access denied to this branch")

      return True

  ---
  Phase 3: API Endpoints Design

  3.1 Public API Endpoints (No Auth Required)

  # backend/app/routers/public_bicycles.py
  from fastapi import APIRouter, Query, HTTPException
  from typing import Optional

  router = APIRouter(prefix="/public", tags=["Public Bicycle Catalog"])

  @router.get("/bicycles")
  async def list_public_bicycles(
      condition: Optional[str] = None,
      branch_id: Optional[str] = None,
      min_price: Optional[float] = None,
      max_price: Optional[float] = None,
      brand: Optional[str] = None,
      search: Optional[str] = None,
      offset: int = 0,
      limit: int = 20,
      db: AsyncSession = Depends(get_db),
  ):
      """
      Public bicycle catalog for customer browsing.
      No authentication required.
      Only shows AVAILABLE bicycles.
      """
      query = select(Bicycle).where(Bicycle.status == BicycleStatus.AVAILABLE)

      if condition:
          query = query.where(Bicycle.condition == condition)
      if branch_id:
          query = query.where(Bicycle.branch_id == branch_id)
      if min_price:
          query = query.where(Bicycle.cash_price >= min_price)
      if max_price:
          query = query.where(Bicycle.cash_price <= max_price)
      if brand:
          query = query.where(Bicycle.brand.ilike(f"%{brand}%"))
      if search:
          query = query.where(
              or_(
                  Bicycle.title.ilike(f"%{search}%"),
                  Bicycle.brand.ilike(f"%{search}%"),
                  Bicycle.model.ilike(f"%{search}%"),
              )
          )

      total = await db.scalar(select(func.count()).select_from(query.subquery()))
      bicycles = await db.scalars(query.offset(offset).limit(limit))

      return {
          "data": [bicycle_to_public_dict(b) for b in bicycles],
          "total": total,
          "offset": offset,
          "limit": limit,
      }

  @router.get("/bicycles/{bicycle_id}")
  async def get_public_bicycle(
      bicycle_id: str,
      db: AsyncSession = Depends(get_db),
  ):
      """Get detailed bicycle information for public viewing"""
      bicycle = await db.get(Bicycle, bicycle_id)
      if not bicycle or bicycle.status != BicycleStatus.AVAILABLE:
          raise HTTPException(404, "Bicycle not found or not available")

      return bicycle_to_public_dict(bicycle, include_details=True)

  @router.get("/branches")
  async def list_public_branches(db: AsyncSession = Depends(get_db)):
      """List all branches with bicycle sales enabled"""
      branches = await db.scalars(
          select(Office)
          .where(Office.allows_bicycle_sales == True)
          .order_by(Office.bicycle_display_order)
      )

      return {"data": [branch_to_public_dict(b) for b in branches]}

  @router.get("/branches/{branch_id}")
  async def get_public_branch(branch_id: str, db: AsyncSession = Depends(get_db)):
      """Get branch details for public viewing"""
      branch = await db.get(Office, branch_id)
      if not branch or not branch.allows_bicycle_sales:
          raise HTTPException(404, "Branch not found")

      return branch_to_public_dict(branch, include_details=True)

  3.2 Customer Application API

  # backend/app/routers/bicycle_applications.py
  router = APIRouter(prefix="/v1/bicycle-applications", tags=["Bicycle Applications"])

  @router.post("")
  async def submit_application(
      application: ApplicationCreate,
      idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
      db: AsyncSession = Depends(get_db),
  ):
      """
      Submit hire purchase application (public endpoint).
      No authentication required for customer submission.
      """
      # Check idempotency
      if idempotency_key:
          existing = await check_idempotency(db, idempotency_key)
          if existing:
              return existing

      # Validate bicycle is available
      bicycle = await db.get(Bicycle, application.bicycle_id)
      if not bicycle or bicycle.status != BicycleStatus.AVAILABLE:
          raise HTTPException(400, "Bicycle not available")

      # Create application
      new_app = BicycleApplication(
          id=generate_id("APP"),
          **application.dict(),
          status=ApplicationStatus.PENDING,
          submitted_at=datetime.utcnow(),
      )

      db.add(new_app)
      await db.commit()

      # Optionally reserve the bicycle
      bicycle.status = BicycleStatus.RESERVED
      await db.commit()

      # Send notification to branch
      await send_new_application_notification(new_app)

      return {"id": new_app.id, "status": "submitted"}

  @router.get("", dependencies=[Depends(require_permission("applications:read"))])
  async def list_applications(
      status: Optional[str] = None,
      branch_id: Optional[str] = None,
      offset: int = 0,
      limit: int = 50,
      user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
  ):
      """List applications (staff only)"""
      query = select(BicycleApplication)

      # Branch managers only see their branch
      if "branch_manager" in user.roles and "admin" not in user.roles:
          user_branch_id = user.metadata.get("branch_id")
          if user_branch_id:
              query = query.where(BicycleApplication.branch_id == user_branch_id)

      if status:
          query = query.where(BicycleApplication.status == status)
      if branch_id:
          query = query.where(BicycleApplication.branch_id == branch_id)

      query = query.order_by(BicycleApplication.submitted_at.desc())

      total = await db.scalar(select(func.count()).select_from(query.subquery()))
      applications = await db.scalars(query.offset(offset).limit(limit))

      return {"data": list(applications), "total": total}

  @router.get("/{application_id}", dependencies=[Depends(require_permission("applications:read"))])
  async def get_application(
      application_id: str,
      user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
  ):
      """Get application details"""
      app = await db.get(BicycleApplication, application_id)
      if not app:
          raise HTTPException(404, "Application not found")

      # Check branch access
      require_branch_access(app.branch_id, user)

      return app

  @router.post("/{application_id}?command=approve", dependencies=[Depends(require_permission("applications:approve"))])
  async def approve_application(
      application_id: str,
      user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
  ):
      """Approve application and convert to loan"""
      app = await db.get(BicycleApplication, application_id)
      if not app:
          raise HTTPException(404, "Application not found")

      if app.status != ApplicationStatus.PENDING:
          raise HTTPException(400, "Application already processed")

      # Check or create client
      client = await get_or_create_client_from_application(db, app)

      # Create loan
      loan = Loan(
          id=generate_id("LOAN"),
          client_id=client.id,
          product_id="BICYCLE_HP",  # Create a default bicycle hire purchase product
          principal=app.bicycle.hire_purchase_price - app.down_payment,
          interest_rate=12.0,  # Configure this
          term_months=app.tenure_months,
          status=LoanStatus.PENDING,
          disbursement_date=None,
      )

      db.add(loan)

      # Update application
      app.status = ApplicationStatus.CONVERTED_TO_LOAN
      app.loan_id = loan.id
      app.reviewed_by = user.id
      app.reviewed_at = datetime.utcnow()

      await db.commit()

      return {"loan_id": loan.id, "status": "approved"}

  @router.post("/{application_id}?command=reject", dependencies=[Depends(require_permission("applications:approve"))])
  async def reject_application(
      application_id: str,
      notes: str,
      user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
  ):
      """Reject application"""
      app = await db.get(BicycleApplication, application_id)
      if not app:
          raise HTTPException(404, "Application not found")

      app.status = ApplicationStatus.REJECTED
      app.notes = notes
      app.reviewed_by = user.id
      app.reviewed_at = datetime.utcnow()

      # Release bicycle reservation
      bicycle = await db.get(Bicycle, app.bicycle_id)
      if bicycle.status == BicycleStatus.RESERVED:
          bicycle.status = BicycleStatus.AVAILABLE

      await db.commit()

      return {"status": "rejected"}

  3.3 Bicycle Inventory API (Staff Only)

  # backend/app/routers/bicycles.py
  router = APIRouter(prefix="/v1/bicycles", tags=["Bicycle Inventory"])

  @router.get("", dependencies=[Depends(require_permission("bicycles:read"))])
  async def list_bicycles(
      condition: Optional[str] = None,
      status: Optional[str] = None,
      branch_id: Optional[str] = None,
      search: Optional[str] = None,
      offset: int = 0,
      limit: int = 50,
      user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
  ):
      """List bicycles (staff view with all statuses)"""
      # Similar to public endpoint but shows all statuses
      pass

  @router.post("", dependencies=[Depends(require_permission("bicycles:write"))])
  async def create_bicycle(
      bicycle: BicycleCreate,
      user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
  ):
      """Add new bicycle to inventory"""
      # Check branch access
      require_branch_access(bicycle.branch_id, user)

      new_bicycle = Bicycle(
          id=generate_id("BIC"),
          **bicycle.dict(),
          status=BicycleStatus.AVAILABLE,
      )

      db.add(new_bicycle)
      await db.commit()

      return new_bicycle

  @router.put("/{bicycle_id}", dependencies=[Depends(require_permission("bicycles:write"))])
  async def update_bicycle(
      bicycle_id: str,
      bicycle: BicycleUpdate,
      user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
  ):
      """Update bicycle details"""
      pass

  @router.delete("/{bicycle_id}", dependencies=[Depends(require_permission("bicycles:delete"))])
  async def delete_bicycle(bicycle_id: str, user: User, db: AsyncSession):
      """Soft delete bicycle (set to inactive)"""
      pass

  @router.post("/{bicycle_id}/images", dependencies=[Depends(require_permission("bicycles:write"))])
  async def upload_bicycle_images(
      bicycle_id: str,
      files: List[UploadFile],
      user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db),
  ):
      """Upload bicycle images"""
      bicycle = await db.get(Bicycle, bicycle_id)
      if not bicycle:
          raise HTTPException(404, "Bicycle not found")

      # Upload to S3/Cloudinary/local storage
      uploaded_urls = []
      for file in files:
          url = await upload_file(file, f"bicycles/{bicycle_id}")
          uploaded_urls.append(url)

      bicycle.image_urls.extend(uploaded_urls)
      if not bicycle.thumbnail_url and uploaded_urls:
          bicycle.thumbnail_url = uploaded_urls[0]

      await db.commit()

      return {"urls": uploaded_urls}

  ---
  Phase 4: Frontend Architecture

  4.1 Project Structure

  frontend/
  ├── src/
  │   ├── app/
  │   │   ├── (public)/                    # Public routes (no auth)
  │   │   │   ├── layout.tsx               # Public layout with different header
  │   │   │   ├── page.tsx                 # Public home page
  │   │   │   ├── bicycles/
  │   │   │   │   ├── page.tsx             # Bicycle catalog
  │   │   │   │   └── [id]/page.tsx        # Bicycle detail
  │   │   │   ├── apply/
  │   │   │   │   └── page.tsx             # Application form
  │   │   │   └── branches/
  │   │   │       └── page.tsx             # Branch listing
  │   │   │
  │   │   ├── (authenticated)/             # Protected routes (existing)
  │   │   │   ├── layout.tsx               # Staff layout
  │   │   │   ├── dashboard/
  │   │   │   ├── clients/
  │   │   │   ├── loans/
  │   │   │   ├── applications/            # NEW: Bicycle applications
  │   │   │   │   ├── page.tsx             # List applications
  │   │   │   │   └── [id]/page.tsx        # Application detail
  │   │   │   ├── inventory/               # NEW: Bicycle inventory
  │   │   │   │   ├── page.tsx             # List bicycles
  │   │   │   │   ├── [id]/page.tsx        # Bicycle detail
  │   │   │   │   └── [id]/edit/page.tsx   # Edit bicycle
  │   │   │   └── branches/                # NEW: Branch management
  │   │   │       └── page.tsx
  │   │   │
  │   │   ├── layout.tsx                   # Root layout
  │   │   └── login/page.tsx
  │   │
  │   └── components/
  │       ├── public/
  │       │   ├── PublicHeader.tsx         # Public site header
  │       │   ├── BicycleCard.tsx
  │       │   ├── BicycleFilters.tsx
  │       │   ├── FinanceCalculator.tsx
  │       │   ├── ApplicationForm.tsx
  │       │   └── BranchCard.tsx
  │       │
  │       └── staff/
  │           ├── ApplicationsTable.tsx
  │           ├── BicycleInventoryTable.tsx
  │           ├── BicycleForm.tsx
  │           └── ApplicationReviewPanel.tsx

  4.2 Public Site Components

  Public Home Page (app/(public)/page.tsx):
  export default async function PublicHome() {
    // Fetch featured bicycles
    const featured = await fetch(`${API_BASE}/public/bicycles?limit=8`);

    return (
      <div className="space-y-12">
        {/* Hero Section */}
        <section className="bg-gradient-to-r from-emerald-700 to-teal-600 text-white py-20 px-6 rounded-3xl">
          <div className="max-w-4xl mx-auto text-center space-y-6">
            <h1 className="text-5xl font-bold">
              Get Your Dream Bicycle Today
            </h1>
            <p className="text-xl">
              Flexible hire purchase plans across 10+ branches
            </p>
            <div className="flex gap-4 justify-center">
              <Link href="/bicycles" className="px-6 py-3 bg-white text-emerald-700 rounded-lg font-semibold">
                Browse Bicycles
              </Link>
              <Link href="/apply" className="px-6 py-3 border-2 border-white rounded-lg font-semibold">
                Apply Now
              </Link>
            </div>
          </div>
        </section>

        {/* Featured Bicycles */}
        <section>
          <h2 className="text-3xl font-bold mb-6">Featured Bicycles</h2>
          <div className="grid md:grid-cols-4 gap-6">
            {featured.data.map(bicycle => (
              <BicycleCard key={bicycle.id} bicycle={bicycle} />
            ))}
          </div>
        </section>

        {/* How It Works */}
        <section className="bg-slate-50 p-12 rounded-3xl">
          <h2 className="text-3xl font-bold text-center mb-8">How It Works</h2>
          <div className="grid md:grid-cols-4 gap-6">
            <StepCard number="1" title="Browse" description="Find your perfect bicycle" />
            <StepCard number="2" title="Apply" description="Submit your hire purchase application" />
            <StepCard number="3" title="Get Approved" description="Quick approval within 1-2 days" />
            <StepCard number="4" title="Ride Away" description="Pick up from your nearest branch" />
          </div>
        </section>
      </div>
    );
  }

  Application Form (app/(public)/apply/page.tsx):
  "use client";

  export default function ApplyPage() {
    const [submitted, setSubmitted] = useState(false);
    const [bicycles, setBicycles] = useState([]);
    const [branches, setBranches] = useState([]);

    useEffect(() => {
      // Fetch available bicycles and branches
      fetch('/api/public/bicycles').then(r => r.json()).then(setBicycles);
      fetch('/api/public/branches').then(r => r.json()).then(setBranches);
    }, []);

    async function handleSubmit(e) {
      e.preventDefault();
      const formData = new FormData(e.target);

      const response = await fetch('/api/v1/bicycle-applications', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(Object.fromEntries(formData)),
      });

      if (response.ok) {
        setSubmitted(true);
      }
    }

    if (submitted) {
      return <SuccessMessage />;
    }

    return (
      <form onSubmit={handleSubmit} className="max-w-2xl mx-auto space-y-8">
        {/* Form sections from the provided design */}
      </form>
    );
  }

  4.3 Staff Application Management

  Applications List (app/(authenticated)/applications/page.tsx):
  export default async function ApplicationsPage() {
    const { data: applications } = await fetch('/api/v1/bicycle-applications', {
      headers: { Cookie: cookies().toString() }
    }).then(r => r.json());

    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold">Bicycle Applications</h1>
          <div className="flex gap-2">
            <FilterButton status="PENDING" />
            <FilterButton status="UNDER_REVIEW" />
            <FilterButton status="APPROVED" />
          </div>
        </div>

        <ApplicationsTable applications={applications} />
      </div>
    );
  }

  Application Review (app/(authenticated)/applications/[id]/page.tsx):
  export default async function ApplicationDetailPage({ params }) {
    const application = await fetch(`/api/v1/bicycle-applications/${params.id}`);

    return (
      <div className="grid md:grid-cols-3 gap-6">
        {/* Customer Info */}
        <div className="md:col-span-2 space-y-6">
          <CustomerInfoCard application={application} />
          <BicycleInfoCard bicycle={application.bicycle} />
          <FinanceDetailsCard application={application} />
        </div>

        {/* Actions */}
        <div className="space-y-4">
          <ReviewActionsPanel applicationId={application.id} />
          <NotesSection notes={application.notes} />
        </div>
      </div>
    );
  }

  ---
  Phase 5: Implementation Roadmap

∴ Thinking…

  Good, now I need to create the implementation roadmap showing the sprints and steps to complete this integration.

⏺ Now let me create a detailed implementation roadmap for you:

  📋 Implementation Roadmap

  Sprint 1: Database & Backend Foundation (Week 1)

  Tasks:
  1. ✅ Create migration file 0002_bicycle_hire_purchase.sql
    - Add bicycles table
    - Add bicycle_applications table
    - Extend offices table with bicycle fields
    - Add indexes and foreign keys
  2. ✅ Create SQLAlchemy models
    - backend/app/models/bicycle.py
    - backend/app/models/bicycle_application.py
    - Update backend/app/models/reference.py
  3. ✅ Extend RBAC system
    - Add new roles to backend/app/rbac.py
    - Implement require_permission() dependency
    - Add require_branch_access() helper
  4. ✅ Add bicycle loan product
    - Seed default "Bicycle Hire Purchase" loan product
    - Configure standard terms (12/24/36/48 months)

  Deliverable: Backend can store bicycles and applications with proper access control

  ---
  Sprint 2: Public API & Core Business Logic (Week 2)

  Tasks:
  1. ✅ Create public bicycle catalog API
    - backend/app/routers/public_bicycles.py
    - GET /public/bicycles (list with filters)
    - GET /public/bicycles/{id} (detail)
    - GET /public/branches (list)
  2. ✅ Create application submission API
    - backend/app/routers/bicycle_applications.py
    - POST /v1/bicycle-applications (public submission)
    - GET /v1/bicycle-applications (staff list)
    - GET /v1/bicycle-applications/{id} (staff detail)
    - POST /v1/bicycle-applications/{id}?command=approve
    - POST /v1/bicycle-applications/{id}?command=reject
  3. ✅ Implement business logic
    - backend/app/services/bicycle_service.py
    - Auto-create client from application
    - Convert application to loan
    - Handle bicycle reservation/release
  4. ✅ Add notification system
    - Email/SMS notification on application submission
    - Notify sales agents of new applications

  Deliverable: Customers can submit applications; staff can review and approve

  ---
  Sprint 3: Staff Bicycle Inventory Management (Week 3)

  Tasks:
  1. ✅ Create bicycle inventory API
    - backend/app/routers/bicycles.py
    - Full CRUD for bicycles
    - Image upload endpoint
    - Bulk import capability
  2. ✅ Extend branch management
    - Update branch endpoints to support bicycle fields
    - Add branch performance reporting
  3. ✅ Add image storage
    - Integrate with S3/Cloudinary/local filesystem
    - Image optimization and thumbnail generation
    - Support multiple images per bicycle
  4. ✅ Create reporting endpoints
    - Bicycle inventory report
    - Application funnel report
    - Branch performance report

  Deliverable: Staff can manage bicycle inventory with photos

  ---
  Sprint 4: Public Website Frontend (Week 4)

  Tasks:
  1. ✅ Create public layout
    - frontend/src/app/(public)/layout.tsx
    - Public header with navigation
    - Footer with branch info
  2. ✅ Build public pages
    - Home page (/(public)/page.tsx)
    - Bicycle catalog (/(public)/bicycles/page.tsx)
    - Bicycle detail (/(public)/bicycles/[id]/page.tsx)
    - Branch listing (/(public)/branches/page.tsx)
  3. ✅ Create public components
    - BicycleCard - Bicycle preview card
    - BicycleFilters - Search and filter UI
    - FinanceCalculator - Monthly payment calculator
    - BranchCard - Branch information card
  4. ✅ Build application form
    - /(public)/apply/page.tsx
    - Multi-step form with validation
    - Success confirmation page

  Deliverable: Public can browse bicycles and submit applications

  ---
  Sprint 5: Staff Application Management Frontend (Week 5)

  Tasks:
  1. ✅ Create applications pages
    - Application list (/(authenticated)/applications/page.tsx)
    - Application detail (/(authenticated)/applications/[id]/page.tsx)
    - Review and approval UI
  2. ✅ Build staff components
    - ApplicationsTable - Filterable applications table
    - ApplicationReviewPanel - Approve/reject actions
    - CustomerInfoCard - Display customer details
    - ApplicationStatusBadge - Status indicator
  3. ✅ Add real-time updates
    - WebSocket notifications for new applications
    - Auto-refresh application list
  4. ✅ Implement role-based UI
    - Show/hide actions based on user permissions
    - Branch filtering for branch managers

  Deliverable: Staff can review and process applications

  ---
  Sprint 6: Staff Inventory Management Frontend (Week 6)

  Tasks:
  1. ✅ Create inventory pages
    - Bicycle list (/(authenticated)/inventory/page.tsx)
    - Bicycle detail (/(authenticated)/inventory/[id]/page.tsx)
    - Add/edit bicycle form
  2. ✅ Build inventory components
    - BicycleInventoryTable - Full bicycle list with actions
    - BicycleForm - Add/edit bicycle form
    - ImageUploadWidget - Multi-image upload with preview
    - BicycleStatusBadge - Status indicator
  3. ✅ Add bulk operations
    - Import bicycles from CSV
    - Bulk status updates
    - Bulk price updates
  4. ✅ Create branch management UI
    - Branch list and editor
    - Branch configuration (hours, description, etc.)

  Deliverable: Staff can fully manage bicycle inventory

  ---
  Sprint 7: Integration & Polish (Week 7)

  Tasks:
  1. ✅ Link applications to loans
    - Auto-populate loan from approved application
    - Link bicycle to loan as collateral
    - Update bicycle status when loan is disbursed
  2. ✅ Add dashboard widgets
    - Application pipeline widget
    - Inventory status widget
    - Branch performance widget
  3. ✅ Implement search
    - Global search for bicycles
    - Application search by customer name/NIP
    - Elasticsearch integration (optional)
  4. ✅ Add analytics
    - Google Analytics on public site
    - Staff usage analytics
    - Conversion funnel tracking

  Deliverable: Fully integrated bicycle hire purchase workflow

  ---
  Sprint 8: Testing & Deployment (Week 8)

  Tasks:
  1. ✅ Write tests
    - API endpoint tests
    - RBAC permission tests
    - Frontend component tests
    - E2E tests for critical flows
  2. ✅ Performance optimization
    - Database query optimization
    - Image lazy loading
    - API response caching
    - CDN setup for images
  3. ✅ Security audit
    - Penetration testing
    - SQL injection testing
    - XSS testing
    - RBAC verification
  4. ✅ Deploy to production
    - Set up CI/CD pipeline
    - Deploy to staging
    - User acceptance testing
    - Production deployment

  Deliverable: Production-ready bicycle hire purchase system

  ---
  🎯 Quick Start Commands

  Step 1: Create Migration

  cat > database/migrations/0002_bicycle_hire_purchase.sql << 'EOF'
  -- Bicycles table
  CREATE TABLE bicycles (
      id TEXT PRIMARY KEY,
      title TEXT NOT NULL,
      brand TEXT NOT NULL,
      model TEXT NOT NULL,
      year INTEGER NOT NULL,
      condition TEXT CHECK(condition IN ('NEW', 'USED')) NOT NULL,
      license_plate TEXT UNIQUE NOT NULL,
      frame_number TEXT UNIQUE,
      engine_number TEXT,
      mileage_km INTEGER,
      description TEXT,
      branch_id TEXT NOT NULL REFERENCES offices(id),
      purchase_price NUMERIC(15, 2) NOT NULL,
      cash_price NUMERIC(15, 2) NOT NULL,
      hire_purchase_price NUMERIC(15, 2) NOT NULL,
      duty_amount NUMERIC(15, 2),
      registration_fee NUMERIC(15, 2),
      status TEXT CHECK(status IN ('AVAILABLE', 'RESERVED', 'SOLD', 'MAINTENANCE')) DEFAULT 'AVAILABLE',
      image_urls JSONB DEFAULT '[]',
      thumbnail_url TEXT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );

  CREATE INDEX idx_bicycles_branch ON bicycles(branch_id);
  CREATE INDEX idx_bicycles_status ON bicycles(status);
  CREATE INDEX idx_bicycles_condition ON bicycles(condition);
  CREATE INDEX idx_bicycles_license_plate ON bicycles(license_plate);

  -- Bicycle applications table
  CREATE TABLE bicycle_applications (
      id TEXT PRIMARY KEY,
      full_name TEXT NOT NULL,
      phone TEXT NOT NULL,
      email TEXT,
      nip_number TEXT NOT NULL,
      address_line1 TEXT NOT NULL,
      address_line2 TEXT,
      city TEXT NOT NULL,
      employer_name TEXT,
      monthly_income NUMERIC(15, 2),
      bicycle_id TEXT NOT NULL REFERENCES bicycles(id),
      branch_id TEXT NOT NULL REFERENCES offices(id),
      tenure_months INTEGER NOT NULL,
      down_payment NUMERIC(15, 2) DEFAULT 0,
      status TEXT CHECK(status IN ('PENDING', 'UNDER_REVIEW', 'APPROVED', 'REJECTED', 'CONVERTED_TO_LOAN')) DEFAULT 'PENDING',
      notes TEXT,
      loan_id TEXT REFERENCES loans(id),
      submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      reviewed_by TEXT REFERENCES users(id),
      reviewed_at TIMESTAMP
  );

  CREATE INDEX idx_bicycle_applications_status ON bicycle_applications(status);
  CREATE INDEX idx_bicycle_applications_branch ON bicycle_applications(branch_id);
  CREATE INDEX idx_bicycle_applications_submitted_at ON bicycle_applications(submitted_at);

  -- Extend offices table for bicycle sales
  ALTER TABLE offices ADD COLUMN IF NOT EXISTS allows_bicycle_sales BOOLEAN DEFAULT TRUE;
  ALTER TABLE offices ADD COLUMN IF NOT EXISTS bicycle_display_order INTEGER;
  ALTER TABLE offices ADD COLUMN IF NOT EXISTS map_coordinates JSONB;
  ALTER TABLE offices ADD COLUMN IF NOT EXISTS operating_hours TEXT;
  ALTER TABLE offices ADD COLUMN IF NOT EXISTS public_description TEXT;

  -- Create bicycle hire purchase loan product
  INSERT INTO loan_products (id, name, interest_rate, term_months, repayment_frequency)
  VALUES ('BICYCLE_HP', 'Bicycle Hire Purchase', 12.0, 36, 'MONTHLY')
  ON CONFLICT DO NOTHING;
  EOF

  Step 2: Run Migration

  make db

  Step 3: Create Backend Models

  # Create bicycle models
  cat > backend/app/models/bicycle.py << 'EOF'
  # [Copy the bicycle.py model code from Phase 1.1 above]
  EOF

  cat > backend/app/models/bicycle_application.py << 'EOF'
  # [Copy the bicycle_application.py model code from Phase 1.2 above]
  EOF

  Step 4: Create API Routers

  # Create public bicycle API
  cat > backend/app/routers/public_bicycles.py << 'EOF'
  # [Copy the public_bicycles.py code from Phase 3.1 above]
  EOF

  # Create bicycle applications API
  cat > backend/app/routers/bicycle_applications.py << 'EOF'
  # [Copy the bicycle_applications.py code from Phase 3.2 above]
  EOF

  # Create bicycle inventory API
  cat > backend/app/routers/bicycles.py << 'EOF'
  # [Copy the bicycles.py code from Phase 3.3 above]
  EOF

  Step 5: Register Routers

  # backend/app/main.py
  from app.routers import (
      # ... existing routers ...
      public_bicycles,
      bicycle_applications,
      bicycles,
  )

  # Register public routes (no auth)
  app.include_router(public_bicycles.router)

  # Register protected routes
  app.include_router(bicycle_applications.router)
  app.include_router(bicycles.router)

  Step 6: Update Frontend Types

  cd frontend
  npm run typegen

  Step 7: Create Frontend Components

  # Create public components directory
  mkdir -p src/components/public

  # Create public layout
  cat > src/app/\(public\)/layout.tsx << 'EOF'
  # [Frontend code from Phase 4]
  EOF

  ---
  🔐 Default User Roles Setup

  Create default users for testing:

  -- Admin user
  INSERT INTO users (id, username, password_hash, roles_csv)
  VALUES ('admin', 'admin', SHA256('admin123'), 'admin');

  -- Branch manager (Colombo branch)
  INSERT INTO users (id, username, password_hash, roles_csv, metadata)
  VALUES ('branch_mgr_cmb', 'manager.colombo', SHA256('manager123'), 'branch_manager', '{"branch_id": "CMB"}');

  -- Sales agent
  INSERT INTO users (id, username, password_hash, roles_csv)
  VALUES ('sales01', 'sales.agent', SHA256('sales123'), 'sales_agent');

  -- Inventory manager
  INSERT INTO users (id, username, password_hash, roles_csv)
  VALUES ('inventory01', 'inventory', SHA256('inventory123'), 'inventory_manager');

  -- Finance officer
  INSERT INTO users (id, username, password_hash, roles_csv)
  VALUES ('finance01', 'finance', SHA256('finance123'), 'finance_officer');

  ---
  📊 Benefits of This Approach

  1. Reuses Existing System: Leverages your FastAPI backend, authentication, RBAC, and database infrastructure
  2. Minimal Changes: Extends existing models rather than replacing them
  3. Proven Architecture: Uses the same patterns already working in your loan manager
  4. Type Safety: Maintains end-to-end TypeScript types via OpenAPI
  5. Scalable: Can handle multiple branches, products, and user roles
  6. Secure: Inherits JWT auth, RBAC, and audit trail from existing system
  7. Fast Development: Can reuse existing components, API patterns, and utilities

  ---
  Next Steps

  Would you like me to:

  1. Generate the complete migration file ready to run?
  2. Create the full backend models and routers with working code?
  3. Build the public frontend pages with Next.js components?
  4. Set up the staff application management UI?
  5. Create a Docker Compose setup for easy deployment?

  Let me know which part you'd like to start with, and I'll generate the complete, production-ready code!