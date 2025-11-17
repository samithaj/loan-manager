from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Depends, status, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import secrets
from datetime import datetime
import csv
import io

from ..db import SessionLocal
from ..models.bicycle import Bicycle, BicycleStatus, BicycleCondition
from ..models.reference import Office
from ..rbac import require_permission, get_current_user, ROLE_BRANCH_MANAGER, require_branch_access


router = APIRouter(prefix="/v1", tags=["bicycles"])


# ============================================================================
# Pydantic Models
# ============================================================================

class BicycleOut(BaseModel):
    """Full bicycle information for staff"""
    id: str
    title: str
    brand: str
    model: str
    year: int
    condition: str
    license_plate: Optional[str] = None
    frame_number: Optional[str] = None
    engine_number: Optional[str] = None
    purchase_price: float
    cash_price: float
    hire_purchase_price: float
    duty_amount: float
    registration_fee: float
    mileage_km: Optional[int] = None
    description: Optional[str] = None
    branch_id: str
    status: str
    image_urls: List[str] = []
    thumbnail_url: Optional[str] = None
    created_at: str
    updated_at: str


class BicycleListResponse(BaseModel):
    """Paginated bicycle list"""
    items: List[BicycleOut]
    total: int
    offset: int
    limit: int


class BicycleCreateIn(BaseModel):
    """Create bicycle request"""
    title: str = Field(..., min_length=5, max_length=200)
    brand: str = Field(..., min_length=2, max_length=100)
    model: str = Field(..., min_length=2, max_length=100)
    year: int = Field(..., ge=1990, le=2030)
    condition: str = Field(..., pattern="^(NEW|USED)$")
    license_plate: Optional[str] = Field(None, max_length=50)
    frame_number: Optional[str] = Field(None, max_length=100)
    engine_number: Optional[str] = Field(None, max_length=100)
    purchase_price: float = Field(..., gt=0)
    cash_price: float = Field(..., gt=0)
    hire_purchase_price: float = Field(..., gt=0)
    duty_amount: float = Field(0, ge=0)
    registration_fee: float = Field(0, ge=0)
    mileage_km: Optional[int] = Field(None, ge=0)
    description: Optional[str] = Field(None, max_length=2000)
    branch_id: str
    status: Optional[str] = Field("AVAILABLE", pattern="^(AVAILABLE|RESERVED|SOLD|MAINTENANCE)$")


class BicycleUpdateIn(BaseModel):
    """Update bicycle request"""
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    brand: Optional[str] = Field(None, min_length=2, max_length=100)
    model: Optional[str] = Field(None, min_length=2, max_length=100)
    year: Optional[int] = Field(None, ge=1990, le=2030)
    condition: Optional[str] = Field(None, pattern="^(NEW|USED)$")
    license_plate: Optional[str] = Field(None, max_length=50)
    frame_number: Optional[str] = Field(None, max_length=100)
    engine_number: Optional[str] = Field(None, max_length=100)
    purchase_price: Optional[float] = Field(None, gt=0)
    cash_price: Optional[float] = Field(None, gt=0)
    hire_purchase_price: Optional[float] = Field(None, gt=0)
    duty_amount: Optional[float] = Field(None, ge=0)
    registration_fee: Optional[float] = Field(None, ge=0)
    mileage_km: Optional[int] = Field(None, ge=0)
    description: Optional[str] = Field(None, max_length=2000)
    branch_id: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(AVAILABLE|RESERVED|SOLD|MAINTENANCE)$")


class BicycleStatusUpdateIn(BaseModel):
    """Update bicycle status"""
    status: str = Field(..., pattern="^(AVAILABLE|RESERVED|SOLD|MAINTENANCE)$")


class BulkImportResponse(BaseModel):
    """Bulk import result"""
    success: bool
    total_rows: int
    imported: int
    errors: List[dict]


class ImageUploadResponse(BaseModel):
    """Image upload result"""
    success: bool
    image_url: str
    thumbnail_url: Optional[str] = None


# ============================================================================
# Helper Functions
# ============================================================================

def generate_bicycle_id() -> str:
    """Generate unique bicycle ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = secrets.token_hex(4).upper()
    return f"BK-{timestamp}-{random_suffix}"


def bicycle_to_out(bicycle: Bicycle) -> BicycleOut:
    """Convert Bicycle model to BicycleOut"""
    return BicycleOut(
        id=bicycle.id,
        title=bicycle.title,
        brand=bicycle.brand,
        model=bicycle.model,
        year=bicycle.year,
        condition=bicycle.condition,
        license_plate=bicycle.license_plate,
        frame_number=bicycle.frame_number,
        engine_number=bicycle.engine_number,
        purchase_price=float(bicycle.purchase_price),
        cash_price=float(bicycle.cash_price),
        hire_purchase_price=float(bicycle.hire_purchase_price),
        duty_amount=float(bicycle.duty_amount),
        registration_fee=float(bicycle.registration_fee),
        mileage_km=bicycle.mileage_km,
        description=bicycle.description,
        branch_id=bicycle.branch_id,
        status=bicycle.status,
        image_urls=bicycle.image_urls or [],
        thumbnail_url=bicycle.thumbnail_url,
        created_at=bicycle.created_at.isoformat(),
        updated_at=bicycle.updated_at.isoformat(),
    )


# ============================================================================
# CRUD Endpoints
# ============================================================================

@router.get("/bicycles", response_model=BicycleListResponse)
async def list_bicycles(
    condition: Optional[str] = Query(None, description="Filter by condition: NEW or USED"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    branch_id: Optional[str] = Query(None, description="Filter by branch"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    search: Optional[str] = Query(None, description="Search in title, brand, model, license plate"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(require_permission("bicycles:read"))
):
    """
    List all bicycles (STAFF ONLY).

    Branch managers can only see bicycles in their assigned branch.
    Shows all statuses (not just AVAILABLE).
    """
    async with SessionLocal() as session:  # type: AsyncSession
        # Build query
        stmt = select(Bicycle)

        # Apply filters
        filters = []

        if condition:
            filters.append(Bicycle.condition == condition.upper())

        if status_filter:
            filters.append(Bicycle.status == status_filter.upper())

        # Branch filtering
        if branch_id:
            filters.append(Bicycle.branch_id == branch_id)
        elif ROLE_BRANCH_MANAGER in user.get("roles", []):
            # Branch managers can only see their branch's bicycles
            user_branch_id = user.get("metadata", {}).get("branch_id")
            if user_branch_id:
                filters.append(Bicycle.branch_id == user_branch_id)

        if brand:
            filters.append(Bicycle.brand.ilike(f"%{brand}%"))

        if search:
            search_pattern = f"%{search}%"
            filters.append(
                or_(
                    Bicycle.title.ilike(search_pattern),
                    Bicycle.brand.ilike(search_pattern),
                    Bicycle.model.ilike(search_pattern),
                    Bicycle.license_plate.ilike(search_pattern),
                )
            )

        if filters:
            stmt = stmt.where(and_(*filters))

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await session.scalar(count_stmt) or 0

        # Apply pagination and ordering
        stmt = stmt.order_by(desc(Bicycle.created_at)).offset(offset).limit(limit)

        # Execute query
        result = await session.execute(stmt)
        bicycles = result.scalars().all()

        # Convert to response format
        items = [bicycle_to_out(b) for b in bicycles]

        return BicycleListResponse(
            items=items,
            total=total,
            offset=offset,
            limit=limit,
        )


@router.get("/bicycles/{bicycle_id}", response_model=BicycleOut)
async def get_bicycle(
    bicycle_id: str,
    user: dict = Depends(require_permission("bicycles:read"))
):
    """
    Get bicycle details (STAFF ONLY).

    Branch managers can only access bicycles in their assigned branch.
    """
    async with SessionLocal() as session:  # type: AsyncSession
        bicycle = await session.get(Bicycle, bicycle_id)

        if not bicycle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BICYCLE_NOT_FOUND", "message": "Bicycle not found"}
            )

        # Check branch access for branch managers
        if ROLE_BRANCH_MANAGER in user.get("roles", []):
            user_branch_id = user.get("metadata", {}).get("branch_id")
            if user_branch_id and bicycle.branch_id != user_branch_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "ACCESS_DENIED", "message": f"You can only access bicycles in branch {user_branch_id}"}
                )

        return bicycle_to_out(bicycle)


@router.post("/bicycles", response_model=BicycleOut, status_code=201)
async def create_bicycle(
    payload: BicycleCreateIn,
    user: dict = Depends(require_permission("bicycles:write"))
):
    """
    Create a new bicycle (STAFF ONLY).

    Branch managers can only create bicycles in their assigned branch.
    """
    async with SessionLocal() as session:  # type: AsyncSession
        # Validate branch exists
        branch = await session.get(Office, payload.branch_id)
        if not branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BRANCH_NOT_FOUND", "message": "Branch not found"}
            )

        # Check branch access for branch managers
        if ROLE_BRANCH_MANAGER in user.get("roles", []):
            user_branch_id = user.get("metadata", {}).get("branch_id")
            if user_branch_id and payload.branch_id != user_branch_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "ACCESS_DENIED", "message": f"You can only create bicycles in branch {user_branch_id}"}
                )

        # Check license plate uniqueness
        if payload.license_plate:
            stmt = select(Bicycle).where(Bicycle.license_plate == payload.license_plate)
            existing = (await session.execute(stmt)).scalar_one_or_none()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"code": "LICENSE_PLATE_EXISTS", "message": "License plate already exists"}
                )

        # Validate hire purchase price >= cash price
        if payload.hire_purchase_price < payload.cash_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_PRICING", "message": "Hire purchase price must be >= cash price"}
            )

        # Generate bicycle ID
        bicycle_id = generate_bicycle_id()

        # Create bicycle
        bicycle = Bicycle(
            id=bicycle_id,
            title=payload.title,
            brand=payload.brand,
            model=payload.model,
            year=payload.year,
            condition=payload.condition,
            license_plate=payload.license_plate,
            frame_number=payload.frame_number,
            engine_number=payload.engine_number,
            purchase_price=payload.purchase_price,
            cash_price=payload.cash_price,
            hire_purchase_price=payload.hire_purchase_price,
            duty_amount=payload.duty_amount,
            registration_fee=payload.registration_fee,
            mileage_km=payload.mileage_km,
            description=payload.description,
            branch_id=payload.branch_id,
            status=payload.status or BicycleStatus.AVAILABLE.value,
        )

        session.add(bicycle)
        await session.commit()
        await session.refresh(bicycle)

        return bicycle_to_out(bicycle)


@router.put("/bicycles/{bicycle_id}", response_model=BicycleOut)
async def update_bicycle(
    bicycle_id: str,
    payload: BicycleUpdateIn,
    user: dict = Depends(require_permission("bicycles:write"))
):
    """
    Update bicycle details (STAFF ONLY).

    Branch managers can only update bicycles in their assigned branch.
    """
    async with SessionLocal() as session:  # type: AsyncSession
        bicycle = await session.get(Bicycle, bicycle_id)

        if not bicycle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BICYCLE_NOT_FOUND", "message": "Bicycle not found"}
            )

        # Check branch access for branch managers (current branch)
        if ROLE_BRANCH_MANAGER in user.get("roles", []):
            user_branch_id = user.get("metadata", {}).get("branch_id")
            if user_branch_id and bicycle.branch_id != user_branch_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "ACCESS_DENIED", "message": f"You can only update bicycles in branch {user_branch_id}"}
                )

            # Also prevent moving to another branch
            if payload.branch_id and payload.branch_id != user_branch_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "ACCESS_DENIED", "message": "You cannot move bicycles to another branch"}
                )

        # Update fields
        update_data = payload.model_dump(exclude_unset=True)

        # Validate license plate uniqueness if changed
        if "license_plate" in update_data and update_data["license_plate"] != bicycle.license_plate:
            stmt = select(Bicycle).where(Bicycle.license_plate == update_data["license_plate"])
            existing = (await session.execute(stmt)).scalar_one_or_none()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"code": "LICENSE_PLATE_EXISTS", "message": "License plate already exists"}
                )

        # Validate pricing if both are being updated
        cash_price = update_data.get("cash_price", bicycle.cash_price)
        hire_purchase_price = update_data.get("hire_purchase_price", bicycle.hire_purchase_price)
        if hire_purchase_price < cash_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_PRICING", "message": "Hire purchase price must be >= cash price"}
            )

        # Apply updates
        for field, value in update_data.items():
            setattr(bicycle, field, value)

        await session.commit()
        await session.refresh(bicycle)

        return bicycle_to_out(bicycle)


@router.delete("/bicycles/{bicycle_id}", status_code=204)
async def delete_bicycle(
    bicycle_id: str,
    user: dict = Depends(require_permission("bicycles:delete"))
):
    """
    Delete a bicycle (STAFF ONLY).

    Branch managers can only delete bicycles in their assigned branch.
    Cannot delete bicycles with active applications.
    """
    async with SessionLocal() as session:  # type: AsyncSession
        bicycle = await session.get(Bicycle, bicycle_id)

        if not bicycle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BICYCLE_NOT_FOUND", "message": "Bicycle not found"}
            )

        # Check branch access for branch managers
        if ROLE_BRANCH_MANAGER in user.get("roles", []):
            user_branch_id = user.get("metadata", {}).get("branch_id")
            if user_branch_id and bicycle.branch_id != user_branch_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "ACCESS_DENIED", "message": f"You can only delete bicycles in branch {user_branch_id}"}
                )

        # Check for active applications
        from ..models.bicycle_application import BicycleApplication
        stmt = select(func.count()).select_from(BicycleApplication).where(
            and_(
                BicycleApplication.bicycle_id == bicycle_id,
                BicycleApplication.status.in_(["PENDING", "UNDER_REVIEW", "APPROVED"])
            )
        )
        active_applications = await session.scalar(stmt) or 0

        if active_applications > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "HAS_ACTIVE_APPLICATIONS", "message": f"Cannot delete bicycle with {active_applications} active applications"}
            )

        # Soft delete by setting status to MAINTENANCE (or hard delete)
        # For now, we'll hard delete if no applications exist
        await session.delete(bicycle)
        await session.commit()


@router.patch("/bicycles/{bicycle_id}/status", response_model=BicycleOut)
async def update_bicycle_status(
    bicycle_id: str,
    payload: BicycleStatusUpdateIn,
    user: dict = Depends(require_permission("bicycles:write"))
):
    """
    Update bicycle status (STAFF ONLY).

    Allows quick status changes without full update.
    """
    async with SessionLocal() as session:  # type: AsyncSession
        bicycle = await session.get(Bicycle, bicycle_id)

        if not bicycle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BICYCLE_NOT_FOUND", "message": "Bicycle not found"}
            )

        # Check branch access for branch managers
        if ROLE_BRANCH_MANAGER in user.get("roles", []):
            user_branch_id = user.get("metadata", {}).get("branch_id")
            if user_branch_id and bicycle.branch_id != user_branch_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "ACCESS_DENIED", "message": f"You can only update bicycles in branch {user_branch_id}"}
                )

        # Update status
        bicycle.status = payload.status

        await session.commit()
        await session.refresh(bicycle)

        return bicycle_to_out(bicycle)


# ============================================================================
# Image Upload Endpoints
# ============================================================================

@router.post("/bicycles/{bicycle_id}/images", response_model=ImageUploadResponse)
async def upload_bicycle_image(
    bicycle_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(require_permission("bicycles:write"))
):
    """
    Upload an image for a bicycle (STAFF ONLY).

    Accepts: JPG, PNG, WEBP (max 5MB)
    Automatically generates thumbnail.
    """
    from ..services.storage_service import upload_bicycle_image, validate_image_file

    async with SessionLocal() as session:  # type: AsyncSession
        bicycle = await session.get(Bicycle, bicycle_id)

        if not bicycle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BICYCLE_NOT_FOUND", "message": "Bicycle not found"}
            )

        # Check branch access for branch managers
        if ROLE_BRANCH_MANAGER in user.get("roles", []):
            user_branch_id = user.get("metadata", {}).get("branch_id")
            if user_branch_id and bicycle.branch_id != user_branch_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "ACCESS_DENIED", "message": f"You can only upload images for bicycles in branch {user_branch_id}"}
                )

        # Validate file
        try:
            await validate_image_file(file)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_FILE", "message": str(e)}
            )

        # Upload image and generate thumbnail
        try:
            image_url, thumbnail_url = await upload_bicycle_image(file, bicycle_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "UPLOAD_FAILED", "message": f"Failed to upload image: {str(e)}"}
            )

        # Add to bicycle image_urls
        current_urls = bicycle.image_urls or []
        current_urls.append(image_url)
        bicycle.image_urls = current_urls

        # Set as thumbnail if first image
        if not bicycle.thumbnail_url:
            bicycle.thumbnail_url = thumbnail_url

        await session.commit()

        return ImageUploadResponse(
            success=True,
            image_url=image_url,
            thumbnail_url=thumbnail_url,
        )


@router.delete("/bicycles/{bicycle_id}/images")
async def delete_bicycle_image(
    bicycle_id: str,
    image_url: str = Query(..., description="Image URL to delete"),
    user: dict = Depends(require_permission("bicycles:write"))
):
    """
    Delete an image from a bicycle (STAFF ONLY).
    """
    from ..services.storage_service import delete_bicycle_image

    async with SessionLocal() as session:  # type: AsyncSession
        bicycle = await session.get(Bicycle, bicycle_id)

        if not bicycle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "BICYCLE_NOT_FOUND", "message": "Bicycle not found"}
            )

        # Check branch access for branch managers
        if ROLE_BRANCH_MANAGER in user.get("roles", []):
            user_branch_id = user.get("metadata", {}).get("branch_id")
            if user_branch_id and bicycle.branch_id != user_branch_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"code": "ACCESS_DENIED", "message": f"You can only delete images for bicycles in branch {user_branch_id}"}
                )

        # Remove from bicycle image_urls
        current_urls = bicycle.image_urls or []
        if image_url not in current_urls:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "IMAGE_NOT_FOUND", "message": "Image URL not found in bicycle"}
            )

        current_urls.remove(image_url)
        bicycle.image_urls = current_urls

        # Update thumbnail if deleting current thumbnail
        if bicycle.thumbnail_url == image_url:
            bicycle.thumbnail_url = current_urls[0] if current_urls else None

        # Delete file from storage
        try:
            await delete_bicycle_image(image_url)
        except Exception as e:
            # Log but don't fail the request
            from loguru import logger
            logger.error(f"Failed to delete image from storage: {e}")

        await session.commit()

        return {"success": True, "message": "Image deleted successfully"}


# ============================================================================
# Bulk Import Endpoint
# ============================================================================

@router.post("/bicycles/bulk-import", response_model=BulkImportResponse)
async def bulk_import_bicycles(
    file: UploadFile = File(...),
    user: dict = Depends(require_permission("bicycles:write"))
):
    """
    Bulk import bicycles from CSV file (STAFF ONLY).

    CSV Format:
    title,brand,model,year,condition,license_plate,frame_number,engine_number,
    purchase_price,cash_price,hire_purchase_price,duty_amount,registration_fee,
    mileage_km,description,branch_id,status

    Branch managers can only import for their assigned branch.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_FILE_TYPE", "message": "File must be a CSV"}
        )

    # Read CSV content
    content = await file.read()
    csv_content = content.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(csv_content))

    async with SessionLocal() as session:  # type: AsyncSession
        imported = 0
        errors = []
        total_rows = 0

        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header is row 1)
            total_rows += 1

            try:
                # Validate required fields
                required_fields = ['title', 'brand', 'model', 'year', 'condition',
                                 'purchase_price', 'cash_price', 'hire_purchase_price', 'branch_id']

                for field in required_fields:
                    if not row.get(field):
                        raise ValueError(f"Missing required field: {field}")

                # Check branch access for branch managers
                branch_id = row['branch_id']
                if ROLE_BRANCH_MANAGER in user.get("roles", []):
                    user_branch_id = user.get("metadata", {}).get("branch_id")
                    if user_branch_id and branch_id != user_branch_id:
                        raise ValueError(f"You can only import bicycles for branch {user_branch_id}")

                # Validate branch exists
                branch = await session.get(Office, branch_id)
                if not branch:
                    raise ValueError(f"Branch not found: {branch_id}")

                # Check license plate uniqueness
                license_plate = row.get('license_plate')
                if license_plate:
                    stmt = select(Bicycle).where(Bicycle.license_plate == license_plate)
                    existing = (await session.execute(stmt)).scalar_one_or_none()
                    if existing:
                        raise ValueError(f"License plate already exists: {license_plate}")

                # Create bicycle
                bicycle_id = generate_bicycle_id()

                bicycle = Bicycle(
                    id=bicycle_id,
                    title=row['title'],
                    brand=row['brand'],
                    model=row['model'],
                    year=int(row['year']),
                    condition=row['condition'].upper(),
                    license_plate=license_plate,
                    frame_number=row.get('frame_number'),
                    engine_number=row.get('engine_number'),
                    purchase_price=float(row['purchase_price']),
                    cash_price=float(row['cash_price']),
                    hire_purchase_price=float(row['hire_purchase_price']),
                    duty_amount=float(row.get('duty_amount', 0)),
                    registration_fee=float(row.get('registration_fee', 0)),
                    mileage_km=int(row['mileage_km']) if row.get('mileage_km') else None,
                    description=row.get('description'),
                    branch_id=branch_id,
                    status=row.get('status', 'AVAILABLE').upper(),
                )

                session.add(bicycle)
                imported += 1

            except Exception as e:
                errors.append({
                    "row": row_num,
                    "data": row,
                    "error": str(e)
                })

        # Commit all successful imports
        if imported > 0:
            await session.commit()

        return BulkImportResponse(
            success=len(errors) == 0,
            total_rows=total_rows,
            imported=imported,
            errors=errors[:10],  # Limit to first 10 errors
        )
