"""Commission calculation service - Formula-based commission engine"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import Optional
from datetime import datetime
import uuid

from ..models.commission_rule import CommissionRule, CommissionType, FormulaType
from ..models.hr_bonus import BonusPayment
from ..schemas.commission_schemas import (
    CommissionRuleCreate,
    CommissionRuleUpdate,
    CommissionCalculationRequest,
    CommissionBatchCalculationRequest,
    EmployeeCommissionResult,
)


class CommissionCalculationService:
    """Service for commission rules and calculations"""

    # ============= CommissionRule CRUD =============

    @staticmethod
    async def get_rule(db: AsyncSession, rule_id: str) -> Optional[CommissionRule]:
        """Get commission rule by ID"""
        result = await db.execute(
            select(CommissionRule).where(CommissionRule.id == rule_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_rules(
        db: AsyncSession,
        commission_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        branch_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[CommissionRule], int]:
        """List commission rules with filters"""
        # Build query conditions
        conditions = []
        if commission_type:
            conditions.append(CommissionRule.commission_type == commission_type)
        if is_active is not None:
            conditions.append(CommissionRule.is_active == is_active)
        if branch_id:
            conditions.append(
                or_(
                    CommissionRule.branch_id == branch_id,
                    CommissionRule.branch_id.is_(None)
                )
            )

        # Get total count
        count_query = select(func.count(CommissionRule.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        # Get rules
        query = select(CommissionRule).order_by(
            CommissionRule.priority.desc(),
            CommissionRule.created_at.desc()
        )
        if conditions:
            query = query.where(and_(*conditions))
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        rules = result.scalars().all()

        return list(rules), total

    @staticmethod
    async def create_rule(
        db: AsyncSession,
        rule_data: CommissionRuleCreate,
        created_by: str
    ) -> CommissionRule:
        """Create commission rule"""
        rule = CommissionRule(
            id=str(uuid.uuid4()),
            **rule_data.model_dump(),
            created_by=created_by
        )
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        return rule

    @staticmethod
    async def update_rule(
        db: AsyncSession,
        rule_id: str,
        rule_data: CommissionRuleUpdate
    ) -> Optional[CommissionRule]:
        """Update commission rule"""
        rule = await CommissionCalculationService.get_rule(db, rule_id)
        if not rule:
            return None

        # Update fields
        update_data = rule_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(rule, field, value)

        await db.commit()
        await db.refresh(rule)
        return rule

    @staticmethod
    async def delete_rule(db: AsyncSession, rule_id: str) -> bool:
        """Delete commission rule"""
        rule = await CommissionCalculationService.get_rule(db, rule_id)
        if not rule:
            return False

        await db.delete(rule)
        await db.commit()
        return True

    # ============= Commission Calculation =============

    @staticmethod
    async def find_applicable_rule(
        db: AsyncSession,
        commission_type: str,
        employee_role: str,
        branch_id: Optional[str] = None,
        vehicle_condition: Optional[str] = None,
        transaction_date: Optional[datetime] = None
    ) -> Optional[CommissionRule]:
        """
        Find the most applicable commission rule based on criteria
        Returns the highest priority matching rule
        """
        check_date = transaction_date or datetime.utcnow()

        # Build query conditions
        conditions = [
            CommissionRule.commission_type == commission_type,
            CommissionRule.is_active == True,
        ]

        # Role must be in applicable_roles (JSONB array contains check)
        conditions.append(
            CommissionRule.applicable_roles.contains([employee_role])
        )

        # Branch filter (null means applies to all branches)
        if branch_id:
            conditions.append(
                or_(
                    CommissionRule.branch_id == branch_id,
                    CommissionRule.branch_id.is_(None)
                )
            )

        # Vehicle condition filter (null means applies to all)
        if vehicle_condition:
            conditions.append(
                or_(
                    CommissionRule.vehicle_condition == vehicle_condition,
                    CommissionRule.vehicle_condition.is_(None)
                )
            )

        # Effective date range
        conditions.append(
            or_(
                CommissionRule.effective_from.is_(None),
                CommissionRule.effective_from <= check_date
            )
        )
        conditions.append(
            or_(
                CommissionRule.effective_until.is_(None),
                CommissionRule.effective_until >= check_date
            )
        )

        # Query with priority ordering
        query = select(CommissionRule).where(and_(*conditions)).order_by(
            CommissionRule.priority.desc(),
            CommissionRule.created_at.desc()
        ).limit(1)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def calculate_commission_for_employee(
        db: AsyncSession,
        employee_id: str,
        employee_role: str,
        sale_amount: float,
        cost_amount: float,
        commission_type: str,
        unit_count: int = 1,
        branch_id: Optional[str] = None,
        vehicle_condition: Optional[str] = None,
        transaction_date: Optional[datetime] = None
    ) -> dict:
        """
        Calculate commission for a single employee
        Returns dict with commission amount and applied rule details
        """
        # Find applicable rule
        rule = await CommissionCalculationService.find_applicable_rule(
            db=db,
            commission_type=commission_type,
            employee_role=employee_role,
            branch_id=branch_id,
            vehicle_condition=vehicle_condition,
            transaction_date=transaction_date
        )

        if not rule:
            return {
                "commission_amount": 0.0,
                "applied_rule_id": None,
                "applied_rule_name": None,
                "formula_type": None,
                "calculation_details": {"message": "No applicable commission rule found"}
            }

        # Calculate commission using rule
        commission_amount = rule.calculate_commission(
            sale_amount=sale_amount,
            cost_amount=cost_amount,
            unit_count=unit_count
        )

        profit_amount = sale_amount - cost_amount

        return {
            "commission_amount": commission_amount,
            "applied_rule_id": rule.id,
            "applied_rule_name": rule.rule_name,
            "formula_type": rule.formula_type,
            "calculation_details": {
                "sale_amount": sale_amount,
                "cost_amount": cost_amount,
                "profit_amount": profit_amount,
                "unit_count": unit_count,
                "flat_amount": float(rule.flat_amount) if rule.flat_amount else None,
                "percentage_rate": float(rule.percentage_rate) if rule.percentage_rate else None,
                "tier_basis": rule.tier_basis,
                "min_commission": float(rule.min_commission) if rule.min_commission else None,
                "max_commission": float(rule.max_commission) if rule.max_commission else None,
            }
        }

    @staticmethod
    async def calculate_single_commission(
        db: AsyncSession,
        request: CommissionCalculationRequest,
        employee_role: str
    ) -> dict:
        """Calculate commission for single employee (from API request)"""
        return await CommissionCalculationService.calculate_commission_for_employee(
            db=db,
            employee_id=request.employee_id,
            employee_role=employee_role,
            sale_amount=request.sale_amount,
            cost_amount=request.cost_amount,
            commission_type=request.commission_type.value,
            unit_count=request.unit_count,
            branch_id=request.branch_id,
            vehicle_condition=request.vehicle_condition,
            transaction_date=request.transaction_date
        )

    @staticmethod
    async def calculate_batch_commissions(
        db: AsyncSession,
        request: CommissionBatchCalculationRequest,
        employee_roles: dict[str, str]  # employee_id -> role mapping
    ) -> dict:
        """Calculate commissions for multiple employees"""
        results = []
        total_commission = 0.0

        for employee_id in request.employee_ids:
            employee_role = employee_roles.get(employee_id)
            if not employee_role:
                # Skip if role not found
                results.append({
                    "employee_id": employee_id,
                    "commission_amount": 0.0,
                    "applied_rule_id": None,
                    "applied_rule_name": None,
                    "formula_type": None,
                    "error": "Employee role not found"
                })
                continue

            calc_result = await CommissionCalculationService.calculate_commission_for_employee(
                db=db,
                employee_id=employee_id,
                employee_role=employee_role,
                sale_amount=request.sale_amount,
                cost_amount=request.cost_amount,
                commission_type=request.commission_type.value,
                unit_count=request.unit_count,
                branch_id=request.branch_id,
                vehicle_condition=request.vehicle_condition,
                transaction_date=request.transaction_date
            )

            results.append({
                "employee_id": employee_id,
                "commission_amount": calc_result["commission_amount"],
                "applied_rule_id": calc_result["applied_rule_id"],
                "applied_rule_name": calc_result["applied_rule_name"],
                "formula_type": calc_result["formula_type"],
            })

            total_commission += calc_result["commission_amount"]

        return {
            "results": results,
            "total_commission": total_commission,
            "calculation_date": datetime.utcnow()
        }

    @staticmethod
    async def auto_generate_commissions_for_sale(
        db: AsyncSession,
        sale_id: str,
        sale_amount: float,
        cost_amount: float,
        employee_ids: list[str],
        employee_roles: dict[str, str],
        branch_id: str,
        vehicle_condition: str,
        created_by: str
    ) -> dict:
        """
        Auto-generate commission payments for a sale
        Creates BonusPayment records for each employee
        """
        results = []
        commission_ids = []
        total_amount = 0.0

        for employee_id in employee_ids:
            employee_role = employee_roles.get(employee_id)
            if not employee_role:
                continue

            # Calculate commission
            calc_result = await CommissionCalculationService.calculate_commission_for_employee(
                db=db,
                employee_id=employee_id,
                employee_role=employee_role,
                sale_amount=sale_amount,
                cost_amount=cost_amount,
                commission_type=CommissionType.BIKE_SALE.value,
                unit_count=1,
                branch_id=branch_id,
                vehicle_condition=vehicle_condition,
                transaction_date=datetime.utcnow()
            )

            commission_amount = calc_result["commission_amount"]
            if commission_amount > 0:
                # Create BonusPayment record
                bonus = BonusPayment(
                    id=str(uuid.uuid4()),
                    employee_id=employee_id,
                    branch_id=branch_id,
                    amount=commission_amount,
                    payment_date=datetime.utcnow().date(),
                    bonus_type="COMMISSION",
                    description=f"Sales commission for sale {sale_id[:8]}",
                    status="PENDING",
                    bicycle_sale_id=sale_id
                )
                db.add(bonus)
                commission_ids.append(bonus.id)
                total_amount += commission_amount

                results.append({
                    "employee_id": employee_id,
                    "commission_amount": commission_amount,
                    "applied_rule_id": calc_result["applied_rule_id"],
                    "applied_rule_name": calc_result["applied_rule_name"],
                    "formula_type": calc_result["formula_type"],
                })

        await db.commit()

        return {
            "commissions_created": len(commission_ids),
            "commission_ids": commission_ids,
            "total_amount": total_amount,
            "details": results
        }
