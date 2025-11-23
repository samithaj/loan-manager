"""Commission API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..rbac import require_permission
from ..services.commission_calculation_service import CommissionCalculationService
from ..schemas.commission_schemas import (
    CommissionRuleCreate,
    CommissionRuleUpdate,
    CommissionRuleResponse,
    CommissionRuleListResponse,
    CommissionCalculationRequest,
    CommissionBatchCalculationRequest,
    CommissionAutoGenerateRequest,
    EmployeeCommissionResult,
    BatchCommissionResult,
)

router = APIRouter(prefix="/v1/commissions", tags=["Commissions"])


@router.get(
    "/rules",
    response_model=CommissionRuleListResponse,
    dependencies=[Depends(require_permission("view:commission_rules"))]
)
async def list_commission_rules(
    commission_type: str | None = None,
    is_active: bool | None = None,
    branch_id: str | None = None,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """List commission rules with optional filters"""
    skip = (page - 1) * page_size
    rules, total = await CommissionCalculationService.list_rules(
        db,
        commission_type=commission_type,
        is_active=is_active,
        branch_id=branch_id,
        skip=skip,
        limit=page_size
    )

    return {
        "items": [CommissionRuleResponse.model_validate(r) for r in rules],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post(
    "/rules",
    response_model=CommissionRuleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("create:commission_rules"))]
)
async def create_commission_rule(
    rule: CommissionRuleCreate,
    current_user: dict = Depends(require_permission("create:commission_rules")),
    db: AsyncSession = Depends(get_db)
):
    """Create a new commission rule"""
    created_rule = await CommissionCalculationService.create_rule(
        db, rule, created_by=current_user["username"]
    )

    return CommissionRuleResponse.model_validate(created_rule)


@router.get(
    "/rules/{rule_id}",
    response_model=CommissionRuleResponse,
    dependencies=[Depends(require_permission("view:commission_rules"))]
)
async def get_commission_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific commission rule by ID"""
    rule = await CommissionCalculationService.get_rule(db, rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commission rule not found"
        )

    return CommissionRuleResponse.model_validate(rule)


@router.put(
    "/rules/{rule_id}",
    response_model=CommissionRuleResponse,
    dependencies=[Depends(require_permission("edit:commission_rules"))]
)
async def update_commission_rule(
    rule_id: str,
    rule_data: CommissionRuleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a commission rule"""
    rule = await CommissionCalculationService.update_rule(db, rule_id, rule_data)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commission rule not found"
        )

    return CommissionRuleResponse.model_validate(rule)


@router.delete(
    "/rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("delete:commission_rules"))]
)
async def delete_commission_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a commission rule"""
    success = await CommissionCalculationService.delete_rule(db, rule_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commission rule not found"
        )

    return None


@router.post(
    "/calculate",
    response_model=EmployeeCommissionResult,
    dependencies=[Depends(require_permission("calculate:commissions"))]
)
async def calculate_commission(
    request: CommissionCalculationRequest,
    current_user: dict = Depends(require_permission("calculate:commissions")),
    db: AsyncSession = Depends(get_db)
):
    """Calculate commission for a single employee"""
    # Get employee role from current user context
    # In a real implementation, this would fetch from Employee model
    employee_role = current_user.get("role", "SALES_AGENT")

    result = await CommissionCalculationService.calculate_single_commission(
        db, request, employee_role=employee_role
    )

    return EmployeeCommissionResult(**result)


@router.post(
    "/calculate-batch",
    response_model=BatchCommissionResult,
    dependencies=[Depends(require_permission("calculate:commissions"))]
)
async def calculate_batch_commissions(
    request: CommissionBatchCalculationRequest,
    current_user: dict = Depends(require_permission("calculate:commissions")),
    db: AsyncSession = Depends(get_db)
):
    """Calculate commissions for multiple employees"""
    # In a real implementation, fetch employee roles from Employee model
    # For now, use placeholder mapping
    employee_roles = {emp_id: "SALES_AGENT" for emp_id in request.employee_ids}

    result = await CommissionCalculationService.calculate_batch_commissions(
        db, request, employee_roles=employee_roles
    )

    return BatchCommissionResult(**result)


@router.post(
    "/auto-generate",
    dependencies=[Depends(require_permission("create:commissions"))]
)
async def auto_generate_commissions(
    request: CommissionAutoGenerateRequest,
    current_user: dict = Depends(require_permission("create:commissions")),
    db: AsyncSession = Depends(get_db)
):
    """Auto-generate commission payments for a sale"""
    # In a real implementation, fetch employee roles from Employee model
    employee_roles = {emp_id: "SALES_AGENT" for emp_id in request.employee_ids}

    result = await CommissionCalculationService.auto_generate_commissions_for_sale(
        db=db,
        sale_id=request.sale_id,
        sale_amount=request.sale_amount,
        cost_amount=request.cost_amount,
        employee_ids=request.employee_ids,
        employee_roles=employee_roles,
        branch_id=request.branch_id,
        vehicle_condition=request.vehicle_condition,
        created_by=current_user["username"]
    )

    return {
        "success": True,
        "commissions_created": result["commissions_created"],
        "commission_ids": result["commission_ids"],
        "total_amount": result["total_amount"],
        "details": result["details"]
    }
