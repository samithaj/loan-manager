# Phase 1: Database Schema Extensions - Implementation Summary

## Overview

This document summarizes the implementation of **Phase 1: Database Schema Extensions** for the Bicycle Hire Purchase System integration into the existing Loan Manager application.

## Completed Tasks ✅

### 1. Database Migration (Task 1.1)

**File:** `database/migrations/0004_bicycle_hire_purchase.sql`

Created comprehensive migration file with:

#### Bicycles Table
- **Primary Key:** `id` (TEXT)
- **Basic Information:** title, brand, model, year, condition (NEW/USED)
- **Identification:** license_plate (unique), frame_number, engine_number
- **Pricing:** purchase_price, cash_price, hire_purchase_price, duty_amount, registration_fee
- **Details:** mileage_km, description
- **Branch Assignment:** branch_id (FK to offices)
- **Status:** AVAILABLE, RESERVED, SOLD, MAINTENANCE
- **Media:** image_urls (JSONB), thumbnail_url
- **Timestamps:** created_at, updated_at (with auto-update trigger)

#### Bicycle Applications Table
- **Primary Key:** `id` (TEXT)
- **Customer Info:** full_name, phone, email, nip_number
- **Address:** address_line1, address_line2, city
- **Employment:** employer_name, monthly_income
- **Application Details:** bicycle_id (FK), branch_id (FK), tenure_months, down_payment
- **Status Tracking:** status (PENDING/UNDER_REVIEW/APPROVED/REJECTED/CONVERTED_TO_LOAN)
- **Workflow:** notes, loan_id (FK to loans), submitted_at, reviewed_by (FK to users), reviewed_at

#### Indexes Created
- `idx_bicycles_branch` - Fast branch-based queries
- `idx_bicycles_status` - Filter by availability status
- `idx_bicycles_condition` - Filter by NEW/USED
- `idx_bicycles_license_plate` - Unique license plate lookups
- `idx_bicycle_applications_status` - Application status filtering
- `idx_bicycle_applications_branch` - Branch-scoped applications
- `idx_bicycle_applications_submitted_at` - Time-based sorting
- `idx_bicycle_applications_bicycle` - Application-bicycle joins

#### Offices Table Extensions
Added bicycle-specific fields:
- `allows_bicycle_sales` (BOOLEAN) - Enable/disable bicycle sales per branch
- `bicycle_display_order` (INTEGER) - Control public website ordering
- `map_coordinates` (JSONB) - Lat/lng for maps integration
- `operating_hours` (TEXT) - Display hours to customers
- `public_description` (TEXT) - Branch marketing copy

#### Users Table Extension
- `metadata` (JSONB) - Store user-specific configuration (e.g., branch_id for branch managers)

#### Default Data
- Bicycle Hire Purchase loan product (id: 'BICYCLE_HP', 12% interest, 36 months)

---

### 2. SQLAlchemy Models (Task 1.2)

#### File: `backend/app/models/bicycle.py`

**Enumerations:**
- `BicycleCondition` - NEW, USED
- `BicycleStatus` - AVAILABLE, RESERVED, SOLD, MAINTENANCE

**Bicycle Model Class:**
- Full SQLAlchemy ORM mapping with Mapped types
- Type-safe column definitions matching database schema
- Check constraints for condition and status validation
- Index definitions

**Helper Methods:**
- `to_dict()` - Full serialization with all fields
- `to_public_dict()` - Public-facing serialization (excludes internal fields like purchase_price)
- `calculate_monthly_payment(tenure_months, down_payment)` - Finance calculator

---

#### File: `backend/app/models/bicycle_application.py`

**Enumeration:**
- `ApplicationStatus` - PENDING, UNDER_REVIEW, APPROVED, REJECTED, CONVERTED_TO_LOAN

**BicycleApplication Model Class:**
- Full SQLAlchemy ORM mapping
- Foreign key relationships to bicycles, offices, loans, users
- Check constraints for status and tenure validation

**Helper Methods:**
- `to_dict()` - Full serialization
- `can_approve()` - Business logic validation
- `can_reject()` - Business logic validation
- `can_convert_to_loan()` - Workflow state validation

---

#### File: `backend/app/models/reference.py` (Extended)

**Office Model Extensions:**
- Added bicycle-specific fields with proper types
- `to_public_dict()` - Public-facing branch information

---

#### File: `backend/app/models/user.py` (Extended)

**User Model Extensions:**
- Added `metadata` column (JSONB)
- Added `user_metadata` property for easy access

---

### 3. RBAC System Extensions (Task 1.3)

**File:** `backend/app/rbac.py`

#### New Role Constants
```python
ROLE_ADMIN = "admin"
ROLE_BRANCH_MANAGER = "branch_manager"
ROLE_SALES_AGENT = "sales_agent"
ROLE_INVENTORY_MANAGER = "inventory_manager"
ROLE_FINANCE_OFFICER = "finance_officer"
ROLE_CUSTOMER_SERVICE = "customer_service"
ROLE_AUDITOR = "auditor"
```

#### Role Permissions Mapping
Comprehensive permission system with resource:action format:

- **Admin:** `["*"]` - Full system access
- **Branch Manager:** bicycles, applications, loans (full CRUD within their branch)
- **Sales Agent:** applications, clients, loans (read/write)
- **Inventory Manager:** bicycles, documents (full CRUD)
- **Finance Officer:** loans, applications approval
- **Customer Service:** applications, clients (read/write)
- **Auditor:** `["*.read"]` - Read-only access to all resources

#### New Functions

**`require_permission(permission: str)`**
- Granular permission checking
- Supports exact match (e.g., "bicycles:read")
- Supports wildcard matching:
  - `resource:*` matches all actions on resource
  - `*.action` matches action on all resources
  - `*` matches everything
- Returns user if authorized, raises 403 if not

**`require_branch_access(branch_id, user, db)`**
- Branch-scoped access control
- Admin: access to all branches
- Branch Manager: access only to assigned branch (from metadata)
- Other roles: access to all branches
- Raises 403 with clear message if denied

**Enhanced `get_current_user()`**
- Now extracts and includes metadata from JWT token
- Stores metadata in request.state.principal

---

### 4. Seed Data (Task 1.4)

**File:** `database/seed_bicycle_system.sql`

#### 10 Branches Created
Realistic Indonesian branches with:
- Branch codes (BR001-BR010)
- Geographic distribution: Jakarta, Surabaya, Bandung, Medan, Semarang, Makassar, Denpasar, Palembang, Yogyakarta, Malang
- Operating hours
- Public descriptions
- Map coordinates (lat/lng)
- All enabled for bicycle sales

#### 15 Users Created
- 1 Admin user
- 5 Branch Managers (assigned to specific branches via metadata)
- 2 Sales Agents
- 2 Inventory Managers
- 2 Finance Officers
- 2 Customer Service Representatives
- 1 Auditor

**Note:** All users have password "password123" (SHA256 hashed). In production, upgrade to bcrypt.

#### 20 Sample Bicycles
**10 New Bicycles:**
- Honda Supra X 125 FI
- Yamaha NMAX 155
- Bajaj Pulsar NS160
- TVS Apache RTR 160 4V
- Honda Vario 160
- Yamaha Aerox 155
- Honda BeAT Street
- Yamaha Mio M3 125
- Honda ADV 160
- Yamaha Lexi 125

**10 Used Bicycles:**
- Various models from 2019-2022
- Realistic mileage
- Competitive pricing
- Good condition descriptions

All bicycles distributed across branches and in AVAILABLE status.

---

### 5. Makefile Update

**File:** `Makefile`

Updated the `db` target to run all migrations in order:
```makefile
db:
	psql "$$DATABASE_URL" -f database/migrations/0001_init.sql
	psql "$$DATABASE_URL" -f database/migrations/0002_idempotency.sql
	psql "$$DATABASE_URL" -f database/migrations/0003_webhooks.sql
	psql "$$DATABASE_URL" -f database/migrations/0004_bicycle_hire_purchase.sql
	psql "$$DATABASE_URL" -f database/seed.sql
	psql "$$DATABASE_URL" -f database/seed_bicycle_system.sql
```

---

## Testing Instructions

To test the implementation:

```bash
# 1. Set DATABASE_URL environment variable
export DATABASE_URL="postgresql://postgres@localhost:5432/loan_manager"

# 2. Run migrations and seed data
make db

# 3. Verify tables created
psql "$DATABASE_URL" -c "\dt"

# 4. Verify bicycles data
psql "$DATABASE_URL" -c "SELECT id, title, brand, status, branch_id FROM bicycles LIMIT 5;"

# 5. Verify applications table
psql "$DATABASE_URL" -c "\d bicycle_applications"

# 6. Verify users with roles
psql "$DATABASE_URL" -c "SELECT username, roles_csv FROM users;"

# 7. Verify indexes
psql "$DATABASE_URL" -c "\di bicycles"
psql "$DATABASE_URL" -c "\di bicycle_applications"
```

---

## Database Schema Validation

### Check Constraints
```sql
-- Verify bicycle condition constraint
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'bicycles'::regclass
AND conname LIKE 'check%';

-- Verify application status constraint
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'bicycle_applications'::regclass
AND conname LIKE 'check%';
```

### Foreign Key Constraints
```sql
-- Verify foreign keys
SELECT tc.constraint_name, tc.table_name, kcu.column_name,
       ccu.table_name AS foreign_table_name,
       ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name IN ('bicycles', 'bicycle_applications');
```

---

## Python Model Testing

```python
# Test in Python shell
from backend.app.models.bicycle import Bicycle, BicycleCondition, BicycleStatus
from backend.app.models.bicycle_application import BicycleApplication, ApplicationStatus
from backend.app.models.reference import Office
from backend.app.models.user import User

# Test enum values
assert BicycleCondition.NEW.value == "NEW"
assert BicycleStatus.AVAILABLE.value == "AVAILABLE"
assert ApplicationStatus.PENDING.value == "PENDING"

# Test model instantiation (requires database session)
# ... add session-based tests
```

---

## RBAC Testing

```python
# Test permission checking
from backend.app.rbac import require_permission, require_branch_access, ROLE_PERMISSIONS

# Test role permissions
assert "bicycles:read" in ROLE_PERMISSIONS["inventory_manager"]
assert "*" in ROLE_PERMISSIONS["admin"]
assert "*.read" in ROLE_PERMISSIONS["auditor"]

# Test with mock user
mock_user = {
    "username": "test_manager",
    "roles": ["branch_manager"],
    "metadata": {"branch_id": "BR001"}
}

# Test permission check (would need to mock Depends)
# ...
```

---

## Next Steps (Phase 2)

With Phase 1 complete, you can now proceed to Phase 2: Public API & Core Business Logic

**Priority Tasks:**
1. Create public bicycle catalog API (`/public/bicycles`)
2. Create application submission API (`/v1/bicycle-applications`)
3. Implement business logic services (client creation, loan conversion)
4. Add notification system (email/SMS)

**Required Files:**
- `backend/app/routers/public_bicycles.py`
- `backend/app/routers/bicycle_applications.py`
- `backend/app/services/bicycle_service.py`
- `backend/app/services/notification_service.py`

---

## Files Created/Modified

### Created Files:
1. `database/migrations/0004_bicycle_hire_purchase.sql` - Database schema
2. `database/seed_bicycle_system.sql` - Seed data
3. `backend/app/models/bicycle.py` - Bicycle ORM model
4. `backend/app/models/bicycle_application.py` - Application ORM model
5. `PHASE1_IMPLEMENTATION.md` - This summary document

### Modified Files:
1. `backend/app/models/reference.py` - Extended Office model
2. `backend/app/models/user.py` - Extended User model with metadata
3. `backend/app/rbac.py` - Enhanced RBAC with new roles and permissions
4. `Makefile` - Updated db target to run new migrations

---

## Notes and Considerations

### Security
- **Password Hashing:** Current seed data uses SHA256. **Upgrade to bcrypt** for production.
- **NIP Encryption:** Consider encrypting NIP numbers at rest for PII protection.
- **JWT Security:** Ensure JWT keys are securely stored and rotated.

### Performance
- All critical indexes are in place
- Consider adding composite indexes if query patterns show need
- JSONB columns (image_urls, metadata, map_coordinates) support GIN indexing if needed

### Scalability
- Image storage URLs are stored in JSONB array - consider dedicated image service
- Branch-scoped queries use indexed branch_id for performance
- Application status changes are tracked with timestamps

### Data Integrity
- Check constraints enforce valid enum values
- Foreign key constraints maintain referential integrity
- Unique constraint on license_plate prevents duplicates
- Tenure validation ensures only 12/24/36/48 month terms

---

## Support

For questions or issues with Phase 1 implementation:
1. Review this document
2. Check database migration logs
3. Verify all tables and indexes were created
4. Test model imports in Python shell
5. Review TODO.md for Phase 2 requirements

---

**Implementation Date:** 2025-11-17
**Status:** ✅ Complete and Ready for Phase 2
**Database Version:** 0004
