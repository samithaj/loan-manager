from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date
from typing import Optional, Dict, Any
import secrets

from ..db import get_db
from ..models.hr_bonus import (
    SalesTarget, PerformanceMetric, BonusRule, BonusTier, BonusPayment,
    TargetType, BonusRuleType, BonusPaymentStatus
)
from ..models.bicycle_application import BicycleApplication, ApplicationStatus
from ..models.bicycle import Bicycle
from ..models.user import User
from ..rbac import require_permission, get_current_user, ROLE_ADMIN, ROLE_BRANCH_MANAGER


router = APIRouter(prefix="/v1/bonuses", tags=["hr-bonuses"])


# ============================================================================
# Pydantic Models
# ============================================================================

class SalesTargetCreateIn(BaseModel):
    """Create sales target"""
    user_id: str
    target_type: str = Field(..., description="MONTHLY, QUARTERLY, or YEARLY")
    period_start: date
    period_end: date
    target_loans: int = Field(0, ge=0)
    target_loan_amount: float = Field(0, ge=0)
    target_bicycles: int = Field(0, ge=0)
    target_bicycle_revenue: float = Field(0, ge=0)


class SalesTargetOut(BaseModel):
    """Sales target response"""
    id: str
    user_id: str
    target_type: str
    period_start: str
    period_end: str
    target_loans: int
    target_loan_amount: float
    target_bicycles: int
    target_bicycle_revenue: float
    created_by: Optional[str] = None
    created_at: str
    updated_at: str


class PerformanceMetricOut(BaseModel):
    """Performance metric response"""
    id: str
    user_id: str
    period_start: str
    period_end: str
    actual_loans: int
    actual_loan_amount: float
    actual_bicycles: int
    actual_bicycle_revenue: float
    achievement_percentage: float
    calculated_at: str


class BonusRuleCreateIn(BaseModel):
    """Create bonus rule"""
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    rule_type: str = Field(..., description="FIXED, PERCENTAGE, TIERED, or COMMISSION")
    applies_to_roles: list[str] = Field(..., min_items=1)
    min_achievement_percentage: float = Field(0, ge=0, le=999)
    base_amount: Optional[float] = Field(None, ge=0)
    percentage_rate: Optional[float] = Field(None, ge=0, le=100)
    commission_rate: Optional[float] = Field(None, ge=0, le=100)
    effective_from: date
    effective_to: Optional[date] = None


class BonusRuleOut(BaseModel):
    """Bonus rule response"""
    id: str
    name: str
    description: Optional[str] = None
    rule_type: str
    applies_to_roles: list[str]
    min_achievement_percentage: float
    base_amount: Optional[float] = None
    percentage_rate: Optional[float] = None
    commission_rate: Optional[float] = None
    is_active: bool
    effective_from: str
    effective_to: Optional[str] = None


class BonusTierCreateIn(BaseModel):
    """Create bonus tier"""
    tier_order: int = Field(..., ge=1)
    achievement_from: float = Field(..., ge=0, le=999)
    achievement_to: float = Field(..., ge=0, le=999)
    bonus_amount: Optional[float] = Field(None, ge=0)
    bonus_percentage: Optional[float] = Field(None, ge=0, le=100)


class BonusTierOut(BaseModel):
    """Bonus tier response"""
    id: str
    bonus_rule_id: str
    tier_order: int
    achievement_from: float
    achievement_to: float
    bonus_amount: Optional[float] = None
    bonus_percentage: Optional[float] = None


class BonusPaymentOut(BaseModel):
    """Bonus payment response"""
    id: str
    user_id: str
    bonus_rule_id: Optional[str] = None
    period_start: str
    period_end: str
    target_amount: Optional[float] = None
    actual_amount: Optional[float] = None
    achievement_percentage: Optional[float] = None
    bonus_amount: float
    calculation_details: Optional[Dict[str, Any]] = None
    status: str
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    paid_at: Optional[str] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None
    created_at: str
    updated_at: str


class BonusPaymentListResponse(BaseModel):
    """Paginated bonus payment list"""
    items: list[BonusPaymentOut]
    total: int
    offset: int
    limit: int


class BonusActionIn(BaseModel):
    """Approve/Reject bonus payment"""
    notes: Optional[str] = Field(None, max_length=1000)
    payment_reference: Optional[str] = Field(None, max_length=500)


# ============================================================================
# Helper Functions
# ============================================================================

async def get_db_session():
    """Get database session"""
    async with get_db() as session:
        yield session


async def calculate_user_performance(
    session: AsyncSession,
    user_id: str,
    period_start: date,
    period_end: date
) -> dict:
    """
    Calculate actual performance metrics for a user in a period
    """
    # Get bicycle applications converted to loans by this user in the period
    stmt = select(BicycleApplication, Bicycle).join(
        Bicycle, BicycleApplication.bicycle_id == Bicycle.id
    ).where(
        and_(
            BicycleApplication.status == ApplicationStatus.CONVERTED_TO_LOAN.value,
            BicycleApplication.reviewed_by == user_id,
            BicycleApplication.reviewed_at.between(period_start, period_end)
        )
    )

    result = await session.execute(stmt)
    applications = result.all()

    actual_bicycles = len(applications)
    actual_bicycle_revenue = sum(
        float(bicycle.hire_purchase_price) for _, bicycle in applications
    )

    # TODO: Add loan metrics when we have loan assignment tracking
    actual_loans = 0
    actual_loan_amount = 0.0

    return {
        "actual_loans": actual_loans,
        "actual_loan_amount": actual_loan_amount,
        "actual_bicycles": actual_bicycles,
        "actual_bicycle_revenue": actual_bicycle_revenue
    }


async def calculate_bonus_for_user(
    session: AsyncSession,
    user_id: str,
    user_roles: list[str],
    period_start: date,
    period_end: date
) -> Optional[dict]:
    """
    Calculate bonus for a user based on performance and applicable rules
    Returns: dict with bonus details or None if not eligible
    """
    # Get sales target
    target_stmt = select(SalesTarget).where(
        and_(
            SalesTarget.user_id == user_id,
            SalesTarget.period_start == period_start,
            SalesTarget.period_end == period_end
        )
    )
    target_result = await session.execute(target_stmt)
    target = target_result.scalar_one_or_none()

    # Calculate actual performance
    performance = await calculate_user_performance(session, user_id, period_start, period_end)

    # Calculate achievement percentage
    achievement_percentage = 0.0
    if target:
        # Calculate based on primary metric (bicycle revenue for now)
        if target.target_bicycle_revenue > 0:
            achievement_percentage = (performance["actual_bicycle_revenue"] / float(target.target_bicycle_revenue)) * 100
        elif target.target_bicycles > 0:
            achievement_percentage = (performance["actual_bicycles"] / target.target_bicycles) * 100

    # Find applicable bonus rules
    rule_stmt = select(BonusRule).where(
        and_(
            BonusRule.is_active == True,
            BonusRule.effective_from <= period_end,
            or_(
                BonusRule.effective_to.is_(None),
                BonusRule.effective_to >= period_start
            )
        )
    )
    rule_result = await session.execute(rule_stmt)
    all_rules = rule_result.scalars().all()

    # Filter rules that apply to user's roles
    applicable_rules = [
        rule for rule in all_rules
        if any(role in rule.applies_to_roles for role in user_roles)
        and achievement_percentage >= float(rule.min_achievement_percentage)
    ]

    if not applicable_rules:
        return None

    # Calculate bonus based on rule type
    total_bonus = 0.0
    calculation_details = {
        "achievement_percentage": achievement_percentage,
        "performance": performance,
        "rules_applied": []
    }

    for rule in applicable_rules:
        rule_bonus = 0.0

        if rule.rule_type == BonusRuleType.FIXED.value:
            rule_bonus = float(rule.base_amount) if rule.base_amount else 0

        elif rule.rule_type == BonusRuleType.PERCENTAGE.value:
            if rule.percentage_rate and target:
                base = float(target.target_bicycle_revenue)
                rule_bonus = base * (float(rule.percentage_rate) / 100)

        elif rule.rule_type == BonusRuleType.COMMISSION.value:
            if rule.commission_rate:
                rule_bonus = performance["actual_bicycle_revenue"] * (float(rule.commission_rate) / 100)

        elif rule.rule_type == BonusRuleType.TIERED.value:
            # Get tiers for this rule
            tier_stmt = select(BonusTier).where(
                BonusTier.bonus_rule_id == rule.id
            ).order_by(BonusTier.tier_order)
            tier_result = await session.execute(tier_stmt)
            tiers = tier_result.scalars().all()

            # Find applicable tier
            for tier in tiers:
                if float(tier.achievement_from) <= achievement_percentage <= float(tier.achievement_to):
                    if tier.bonus_amount:
                        rule_bonus = float(tier.bonus_amount)
                    elif tier.bonus_percentage and target:
                        base = float(target.target_bicycle_revenue)
                        rule_bonus = base * (float(tier.bonus_percentage) / 100)
                    break

        total_bonus += rule_bonus
        calculation_details["rules_applied"].append({
            "rule_id": rule.id,
            "rule_name": rule.name,
            "rule_type": rule.rule_type,
            "bonus_amount": rule_bonus
        })

    return {
        "bonus_amount": total_bonus,
        "target_amount": float(target.target_bicycle_revenue) if target else None,
        "actual_amount": performance["actual_bicycle_revenue"],
        "achievement_percentage": achievement_percentage,
        "calculation_details": calculation_details
    }


# ============================================================================
# Sales Target Endpoints
# ============================================================================

@router.post("/targets", response_model=SalesTargetOut, status_code=status.HTTP_201_CREATED)
async def create_sales_target(
    data: SalesTargetCreateIn,
    current_user: User = Depends(require_permission("bonuses:write")),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Create sales target for a user

    Permissions: bonuses:write (admin, branch_manager, finance_officer)
    """
    if data.period_start >= data.period_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Period start must be before period end"
        )

    target_id = f"ST-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"

    target = SalesTarget(
        id=target_id,
        user_id=data.user_id,
        target_type=data.target_type,
        period_start=data.period_start,
        period_end=data.period_end,
        target_loans=data.target_loans,
        target_loan_amount=data.target_loan_amount,
        target_bicycles=data.target_bicycles,
        target_bicycle_revenue=data.target_bicycle_revenue,
        created_by=str(current_user.id)
    )

    session.add(target)
    await session.commit()
    await session.refresh(target)

    return SalesTargetOut(**target.to_dict())


@router.get("/targets", response_model=list[SalesTargetOut])
async def list_sales_targets(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    period_start: Optional[date] = Query(None, description="Filter by period start"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    List sales targets

    Permissions:
    - Users can view their own targets
    - Admin/managers can view all targets
    """
    stmt = select(SalesTarget)

    # Filter by user
    if user_id:
        if user_id != str(current_user.id):
            try:
                await require_permission("bonuses:read")(current_user)
            except HTTPException:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view your own sales targets"
                )
        stmt = stmt.where(SalesTarget.user_id == user_id)
    else:
        stmt = stmt.where(SalesTarget.user_id == str(current_user.id))

    if period_start:
        stmt = stmt.where(SalesTarget.period_start == period_start)

    stmt = stmt.order_by(desc(SalesTarget.period_start))

    result = await session.execute(stmt)
    targets = result.scalars().all()

    return [SalesTargetOut(**target.to_dict()) for target in targets]


# ============================================================================
# Performance Metrics Endpoints
# ============================================================================

@router.post("/metrics/calculate", response_model=PerformanceMetricOut)
async def calculate_performance_metrics(
    user_id: str = Query(..., description="User ID"),
    period_start: date = Query(..., description="Period start date"),
    period_end: date = Query(..., description="Period end date"),
    current_user: User = Depends(require_permission("bonuses:write")),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Calculate and save performance metrics for a user

    Permissions: bonuses:write (admin, branch_manager, finance_officer)
    """
    if period_start >= period_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Period start must be before period end"
        )

    # Calculate performance
    performance = await calculate_user_performance(session, user_id, period_start, period_end)

    # Get target to calculate achievement percentage
    target_stmt = select(SalesTarget).where(
        and_(
            SalesTarget.user_id == user_id,
            SalesTarget.period_start == period_start,
            SalesTarget.period_end == period_end
        )
    )
    target_result = await session.execute(target_stmt)
    target = target_result.scalar_one_or_none()

    achievement_percentage = 0.0
    if target and target.target_bicycle_revenue > 0:
        achievement_percentage = (performance["actual_bicycle_revenue"] / float(target.target_bicycle_revenue)) * 100

    # Create or update performance metric
    metric_stmt = select(PerformanceMetric).where(
        and_(
            PerformanceMetric.user_id == user_id,
            PerformanceMetric.period_start == period_start,
            PerformanceMetric.period_end == period_end
        )
    )
    metric_result = await session.execute(metric_stmt)
    metric = metric_result.scalar_one_or_none()

    if metric:
        # Update existing
        metric.actual_loans = performance["actual_loans"]
        metric.actual_loan_amount = performance["actual_loan_amount"]
        metric.actual_bicycles = performance["actual_bicycles"]
        metric.actual_bicycle_revenue = performance["actual_bicycle_revenue"]
        metric.achievement_percentage = achievement_percentage
        metric.calculated_at = datetime.utcnow()
    else:
        # Create new
        metric_id = f"PM-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
        metric = PerformanceMetric(
            id=metric_id,
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            actual_loans=performance["actual_loans"],
            actual_loan_amount=performance["actual_loan_amount"],
            actual_bicycles=performance["actual_bicycles"],
            actual_bicycle_revenue=performance["actual_bicycle_revenue"],
            achievement_percentage=achievement_percentage
        )
        session.add(metric)

    await session.commit()
    await session.refresh(metric)

    return PerformanceMetricOut(**metric.to_dict())


@router.get("/metrics", response_model=list[PerformanceMetricOut])
async def list_performance_metrics(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    period_start: Optional[date] = Query(None, description="Filter by period start"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    List performance metrics

    Permissions:
    - Users can view their own metrics
    - Admin/managers can view all metrics
    """
    stmt = select(PerformanceMetric)

    # Filter by user
    if user_id:
        if user_id != str(current_user.id):
            try:
                await require_permission("bonuses:read")(current_user)
            except HTTPException:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view your own performance metrics"
                )
        stmt = stmt.where(PerformanceMetric.user_id == user_id)
    else:
        stmt = stmt.where(PerformanceMetric.user_id == str(current_user.id))

    if period_start:
        stmt = stmt.where(PerformanceMetric.period_start == period_start)

    stmt = stmt.order_by(desc(PerformanceMetric.period_start))

    result = await session.execute(stmt)
    metrics = result.scalars().all()

    return [PerformanceMetricOut(**metric.to_dict()) for metric in metrics]


# ============================================================================
# Bonus Rules Endpoints
# ============================================================================

@router.post("/rules", response_model=BonusRuleOut, status_code=status.HTTP_201_CREATED)
async def create_bonus_rule(
    data: BonusRuleCreateIn,
    current_user: User = Depends(require_permission("bonuses:write")),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Create bonus rule

    Permissions: bonuses:write (admin, branch_manager, finance_officer)
    """
    rule_id = f"BR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"

    rule = BonusRule(
        id=rule_id,
        name=data.name,
        description=data.description,
        rule_type=data.rule_type,
        applies_to_roles=data.applies_to_roles,
        min_achievement_percentage=data.min_achievement_percentage,
        base_amount=data.base_amount,
        percentage_rate=data.percentage_rate,
        commission_rate=data.commission_rate,
        effective_from=data.effective_from,
        effective_to=data.effective_to,
        is_active=True
    )

    session.add(rule)
    await session.commit()
    await session.refresh(rule)

    return BonusRuleOut(**rule.to_dict())


@router.get("/rules", response_model=list[BonusRuleOut])
async def list_bonus_rules(
    active_only: bool = Query(True, description="Filter active rules only"),
    current_user: User = Depends(require_permission("bonuses:read")),
    session: AsyncSession = Depends(get_db_session)
):
    """
    List bonus rules

    Permissions: bonuses:read
    """
    stmt = select(BonusRule).order_by(BonusRule.name)

    if active_only:
        stmt = stmt.where(BonusRule.is_active == True)

    result = await session.execute(stmt)
    rules = result.scalars().all()

    return [BonusRuleOut(**rule.to_dict()) for rule in rules]


@router.post("/rules/{rule_id}/tiers", response_model=BonusTierOut, status_code=status.HTTP_201_CREATED)
async def create_bonus_tier(
    rule_id: str,
    data: BonusTierCreateIn,
    current_user: User = Depends(require_permission("bonuses:write")),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Create bonus tier for a tiered rule

    Permissions: bonuses:write
    """
    # Verify rule exists and is tiered
    rule_stmt = select(BonusRule).where(BonusRule.id == rule_id)
    rule_result = await session.execute(rule_stmt)
    rule = rule_result.scalar_one_or_none()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bonus rule {rule_id} not found"
        )

    if rule.rule_type != BonusRuleType.TIERED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tiers can only be added to TIERED bonus rules"
        )

    tier_id = f"BT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"

    tier = BonusTier(
        id=tier_id,
        bonus_rule_id=rule_id,
        tier_order=data.tier_order,
        achievement_from=data.achievement_from,
        achievement_to=data.achievement_to,
        bonus_amount=data.bonus_amount,
        bonus_percentage=data.bonus_percentage
    )

    session.add(tier)
    await session.commit()
    await session.refresh(tier)

    return BonusTierOut(**tier.to_dict())


@router.get("/rules/{rule_id}/tiers", response_model=list[BonusTierOut])
async def list_bonus_tiers(
    rule_id: str,
    current_user: User = Depends(require_permission("bonuses:read")),
    session: AsyncSession = Depends(get_db_session)
):
    """
    List bonus tiers for a rule

    Permissions: bonuses:read
    """
    stmt = select(BonusTier).where(
        BonusTier.bonus_rule_id == rule_id
    ).order_by(BonusTier.tier_order)

    result = await session.execute(stmt)
    tiers = result.scalars().all()

    return [BonusTierOut(**tier.to_dict()) for tier in tiers]


# ============================================================================
# Bonus Payment Endpoints
# ============================================================================

@router.post("/payments/generate", response_model=BonusPaymentOut, status_code=status.HTTP_201_CREATED)
async def generate_bonus_payment(
    user_id: str = Query(..., description="User ID"),
    period_start: date = Query(..., description="Period start date"),
    period_end: date = Query(..., description="Period end date"),
    current_user: User = Depends(require_permission("bonuses:write")),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Generate bonus payment for a user based on performance

    Permissions: bonuses:write (admin, branch_manager, finance_officer)
    """
    # Get user roles (simplified - would need to query users table)
    # For now, assume user_roles are available in metadata
    user_roles = ["sales_agent", "branch_manager"]  # TODO: Get from user record

    # Calculate bonus
    bonus_data = await calculate_bonus_for_user(
        session, user_id, user_roles, period_start, period_end
    )

    if not bonus_data or bonus_data["bonus_amount"] <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not eligible for bonus or bonus amount is zero"
        )

    # Create bonus payment
    payment_id = f"BP-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"

    payment = BonusPayment(
        id=payment_id,
        user_id=user_id,
        period_start=period_start,
        period_end=period_end,
        target_amount=bonus_data.get("target_amount"),
        actual_amount=bonus_data.get("actual_amount"),
        achievement_percentage=bonus_data.get("achievement_percentage"),
        bonus_amount=bonus_data["bonus_amount"],
        calculation_details=bonus_data.get("calculation_details"),
        status=BonusPaymentStatus.PENDING.value
    )

    session.add(payment)
    await session.commit()
    await session.refresh(payment)

    return BonusPaymentOut(**payment.to_dict())


@router.get("/payments", response_model=BonusPaymentListResponse)
async def list_bonus_payments(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    period_start: Optional[date] = Query(None, description="Filter by period start"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    List bonus payments

    Permissions:
    - Users can view their own payments
    - Admin/managers can view all payments
    """
    stmt = select(BonusPayment)

    # Filter by user
    if user_id:
        if user_id != str(current_user.id):
            try:
                await require_permission("bonuses:read")(current_user)
            except HTTPException:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view your own bonus payments"
                )
        stmt = stmt.where(BonusPayment.user_id == user_id)
    else:
        stmt = stmt.where(BonusPayment.user_id == str(current_user.id))

    if status:
        stmt = stmt.where(BonusPayment.status == status)

    if period_start:
        stmt = stmt.where(BonusPayment.period_start == period_start)

    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await session.execute(count_stmt)
    total = count_result.scalar() or 0

    # Get paginated results
    stmt = stmt.order_by(desc(BonusPayment.created_at)).offset(offset).limit(limit)
    result = await session.execute(stmt)
    payments = result.scalars().all()

    items = [BonusPaymentOut(**payment.to_dict()) for payment in payments]

    return BonusPaymentListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit
    )


@router.post("/payments/{payment_id}/approve", response_model=BonusPaymentOut)
async def approve_bonus_payment(
    payment_id: str,
    data: BonusActionIn,
    current_user: User = Depends(require_permission("bonuses:approve")),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Approve bonus payment

    Permissions: bonuses:approve (admin, branch_manager, finance_officer)
    """
    stmt = select(BonusPayment).where(BonusPayment.id == payment_id)
    result = await session.execute(stmt)
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bonus payment {payment_id} not found"
        )

    if not payment.can_approve():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve payment in {payment.status} status"
        )

    payment.status = BonusPaymentStatus.APPROVED.value
    payment.approved_by = str(current_user.id)
    payment.approved_at = datetime.utcnow()
    payment.notes = data.notes

    await session.commit()
    await session.refresh(payment)

    return BonusPaymentOut(**payment.to_dict())


@router.post("/payments/{payment_id}/pay", response_model=BonusPaymentOut)
async def mark_bonus_payment_as_paid(
    payment_id: str,
    data: BonusActionIn,
    current_user: User = Depends(require_permission("bonuses:approve")),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Mark bonus payment as paid

    Permissions: bonuses:approve (admin, branch_manager, finance_officer)
    """
    stmt = select(BonusPayment).where(BonusPayment.id == payment_id)
    result = await session.execute(stmt)
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bonus payment {payment_id} not found"
        )

    if not payment.can_pay():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot mark payment as paid in {payment.status} status. Must be APPROVED first."
        )

    payment.status = BonusPaymentStatus.PAID.value
    payment.paid_at = datetime.utcnow()
    payment.payment_reference = data.payment_reference
    if data.notes:
        payment.notes = (payment.notes or "") + "\n" + data.notes

    await session.commit()
    await session.refresh(payment)

    return BonusPaymentOut(**payment.to_dict())
