"""
Commission Service

Handles calculation and tracking of bike sale commissions.
Integrates with existing HR bonus system for commission payments.

Commission Rules:
- Configurable buyer/seller branch split (default 40/60)
- Base can be PROFIT or SALE_PRICE
- Only applies when profit > 0 (if PROFIT base)
- Garage incentive (when bike has repairs)
- Sales officer individual commission
- Creates bonus_payment records for tracking
"""

from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets

from ..models import (
    BicycleSale, Bicycle, BonusRule, BonusPayment, RepairJob
)
from typing import Optional
from uuid import UUID


class CommissionService:
    """Service for managing bike sale commissions"""

    @staticmethod
    async def calculate_bike_sale_commission(
        db: AsyncSession,
        sale_id: str
    ) -> list[BonusPayment]:
        """
        Calculate and create commission payments for bike sale.
        Uses active bike commission rules from bonus_rules table.

        Args:
            db: Database session
            sale_id: BicycleSale ID

        Returns:
            List of BonusPayment objects created (buyer and/or seller commissions)
        """
        # Get sale
        result = await db.execute(
            select(BicycleSale).where(BicycleSale.id == sale_id)
        )
        sale = result.scalar_one()

        # Get bike
        result = await db.execute(
            select(Bicycle).where(Bicycle.id == sale.bicycle_id)
        )
        bike = result.scalar_one()

        # Get applicable commission rule
        result = await db.execute(
            select(BonusRule)
            .where(
                BonusRule.applies_to_bike_sales == True,
                BonusRule.is_active == True,
                BonusRule.effective_from <= sale.sale_date
            )
            .order_by(BonusRule.effective_from.desc())
        )
        rule_result = result.first()

        if not rule_result:
            # No commission rule found, skip commission creation
            return []

        rule = rule_result[0]

        # Calculate commission base
        if rule.commission_base == "SALE_PRICE":
            commission_base = Decimal(str(sale.selling_price))
        else:  # PROFIT
            if not sale.profit_or_loss or sale.profit_or_loss <= 0:
                # No profit, no commission
                return []
            commission_base = Decimal(str(sale.profit_or_loss))

        # Get all commission percentages
        buyer_percent = Decimal(str(rule.buyer_branch_percent or 40))
        seller_percent = Decimal(str(rule.seller_branch_percent or 60))
        garage_percent = Decimal(str(rule.garage_percent or 0))
        sales_officer_percent = Decimal(str(rule.sales_officer_percent or 0))
        garage_commission_type = rule.garage_commission_type or "PERCENTAGE"

        # Calculate branch commissions
        buyer_commission = commission_base * (buyer_percent / Decimal(100))
        seller_commission = commission_base * (seller_percent / Decimal(100))

        # Determine branches
        # Buyer branch: where bike was originally purchased/held
        buyer_branch_id = bike.branch_id  # Original branch from procurement
        # Seller branch: where bike was sold
        seller_branch_id = sale.selling_branch_id

        # Create bonus payments
        payments = []

        # Calculate period (first and last day of sale month)
        sale_month_start = date(sale.sale_date.year, sale.sale_date.month, 1)
        # Get last day of month
        if sale.sale_date.month == 12:
            sale_month_end = date(sale.sale_date.year + 1, 1, 1)
        else:
            sale_month_end = date(sale.sale_date.year, sale.sale_date.month + 1, 1)
        # Subtract one day to get last day of current month
        from datetime import timedelta
        sale_month_end = sale_month_end - timedelta(days=1)

        # Buyer commission
        buyer_payment_id = f"BP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
        buyer_payment = BonusPayment(
            id=buyer_payment_id,
            user_id="00000000-0000-0000-0000-000000000000",  # System/branch level commission
            bonus_rule_id=rule.id,
            period_start=sale_month_start,
            period_end=sale_month_end,
            bonus_amount=buyer_commission,
            calculation_details={
                "type": "bike_sale_commission",
                "commission_type": "BUYER",
                "bike_id": bike.id,
                "bike_no": bike.license_plate,
                "sale_id": sale_id,
                "commission_base": rule.commission_base,
                "base_amount": float(commission_base),
                "commission_percent": float(buyer_percent),
                "branch_id": buyer_branch_id,
            },
            status="PENDING",
            bicycle_sale_id=sale_id,
            commission_type="BUYER",
        )
        db.add(buyer_payment)
        payments.append(buyer_payment)

        # Seller commission (only if different branch)
        if seller_branch_id != buyer_branch_id:
            seller_payment_id = f"BP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
            seller_payment = BonusPayment(
                id=seller_payment_id,
                user_id="00000000-0000-0000-0000-000000000000",  # System/branch level commission
                bonus_rule_id=rule.id,
                period_start=sale_month_start,
                period_end=sale_month_end,
                bonus_amount=seller_commission,
                calculation_details={
                    "type": "bike_sale_commission",
                    "commission_type": "SELLER",
                    "bike_id": bike.id,
                    "bike_no": bike.license_plate,
                    "sale_id": sale_id,
                    "commission_base": rule.commission_base,
                    "base_amount": float(commission_base),
                    "commission_percent": float(seller_percent),
                    "branch_id": seller_branch_id,
                },
                status="PENDING",
                bicycle_sale_id=sale_id,
                commission_type="SELLER",
            )
            db.add(seller_payment)
            payments.append(seller_payment)
        else:
            # Same branch bought and sold, combine commissions
            buyer_payment.bonus_amount = buyer_commission + seller_commission
            buyer_payment.calculation_details["combined_commission"] = True
            buyer_payment.calculation_details["total_percent"] = float(buyer_percent + seller_percent)

        # ==================================================================
        # GARAGE INCENTIVE COMMISSION
        # ==================================================================
        # Check if bike has any repair jobs (garage did work on it)
        garage_branch_id = await CommissionService._get_garage_branch_for_bike(db, bike.id)

        if garage_branch_id and garage_percent > 0 and garage_commission_type != "NONE":
            if garage_commission_type == "PERCENTAGE":
                garage_commission = commission_base * (garage_percent / Decimal(100))
            elif garage_commission_type == "FIXED":
                garage_commission = garage_percent  # Fixed amount
            else:
                garage_commission = Decimal(0)

            if garage_commission > 0:
                garage_payment_id = f"BP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
                garage_payment = BonusPayment(
                    id=garage_payment_id,
                    user_id="00000000-0000-0000-0000-000000000000",  # System/branch level commission
                    bonus_rule_id=rule.id,
                    period_start=sale_month_start,
                    period_end=sale_month_end,
                    bonus_amount=garage_commission,
                    calculation_details={
                        "type": "bike_sale_commission",
                        "commission_type": "GARAGE",
                        "bike_id": bike.id,
                        "bike_no": bike.license_plate,
                        "sale_id": sale_id,
                        "commission_base": rule.commission_base,
                        "base_amount": float(commission_base),
                        "commission_percent": float(garage_percent) if garage_commission_type == "PERCENTAGE" else None,
                        "commission_type_desc": garage_commission_type,
                        "garage_branch_id": garage_branch_id,
                    },
                    status="PENDING",
                    bicycle_sale_id=sale_id,
                    commission_type="GARAGE",
                    garage_branch_id=garage_branch_id,
                )
                db.add(garage_payment)
                payments.append(garage_payment)

        # ==================================================================
        # SALES OFFICER INDIVIDUAL COMMISSION
        # ==================================================================
        # sold_by field contains user ID or username
        sales_officer_id = await CommissionService._resolve_sales_officer_id(db, sale.sold_by)

        if sales_officer_id and sales_officer_percent > 0:
            sales_officer_commission = commission_base * (sales_officer_percent / Decimal(100))

            officer_payment_id = f"BP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
            officer_payment = BonusPayment(
                id=officer_payment_id,
                user_id=sales_officer_id,  # Individual user commission
                bonus_rule_id=rule.id,
                period_start=sale_month_start,
                period_end=sale_month_end,
                bonus_amount=sales_officer_commission,
                calculation_details={
                    "type": "bike_sale_commission",
                    "commission_type": "SALES_OFFICER",
                    "bike_id": bike.id,
                    "bike_no": bike.license_plate,
                    "sale_id": sale_id,
                    "commission_base": rule.commission_base,
                    "base_amount": float(commission_base),
                    "commission_percent": float(sales_officer_percent),
                    "sales_officer_id": str(sales_officer_id),
                },
                status="PENDING",
                bicycle_sale_id=sale_id,
                commission_type="SALES_OFFICER",
                sales_officer_id=sales_officer_id,
            )
            db.add(officer_payment)
            payments.append(officer_payment)

        return payments

    @staticmethod
    async def _get_garage_branch_for_bike(
        db: AsyncSession,
        bicycle_id: str
    ) -> Optional[str]:
        """
        Get the garage/workshop branch that performed repairs on the bike.
        Returns the branch_id of the most recent completed repair job.

        Args:
            db: Database session
            bicycle_id: Bicycle ID

        Returns:
            Branch ID or None if no repairs found
        """
        try:
            result = await db.execute(
                select(RepairJob)
                .where(
                    RepairJob.bicycle_id == bicycle_id,
                    RepairJob.status == "COMPLETED"
                )
                .order_by(RepairJob.updated_at.desc())
                .limit(1)
            )
            repair_job = result.scalar_one_or_none()

            return repair_job.branch_id if repair_job else None
        except Exception:
            # If RepairJob table doesn't exist or any error, return None
            return None

    @staticmethod
    async def _resolve_sales_officer_id(
        db: AsyncSession,
        sold_by: str
    ) -> Optional[str]:
        """
        Resolve sales officer ID from sold_by field.
        The sold_by field might contain user ID or username.

        Args:
            db: Database session
            sold_by: sold_by field value (could be UUID string or username)

        Returns:
            User UUID string or None
        """
        from ..models import User

        # First try as UUID
        try:
            uuid_obj = UUID(sold_by)
            # Verify user exists
            result = await db.execute(
                select(User).where(User.id == uuid_obj)
            )
            user = result.scalar_one_or_none()
            return str(uuid_obj) if user else None
        except (ValueError, AttributeError):
            pass

        # Try as username
        try:
            result = await db.execute(
                select(User).where(User.username == sold_by)
            )
            user = result.scalar_one_or_none()
            return str(user.id) if user else None
        except Exception:
            return None

    @staticmethod
    async def get_branch_commission_report(
        db: AsyncSession,
        branch_id: str,
        start_date: date,
        end_date: date
    ) -> dict:
        """
        Get commission summary for branch in date range.

        Args:
            db: Database session
            branch_id: Branch ID
            start_date: Report start date
            end_date: Report end date

        Returns:
            Dictionary with commission breakdown
        """
        # Get all bike sale commissions for the branch in date range
        result = await db.execute(
            select(BonusPayment)
            .where(
                BonusPayment.bicycle_sale_id.isnot(None),
                BonusPayment.period_start >= start_date,
                BonusPayment.period_end <= end_date
            )
        )
        all_payments = list(result.scalars().all())

        # Filter by branch_id in calculation_details
        payments = [
            p for p in all_payments
            if p.calculation_details and p.calculation_details.get("branch_id") == branch_id
        ]

        buyer_commission = sum(
            p.bonus_amount for p in payments if p.commission_type == "BUYER"
        )
        seller_commission = sum(
            p.bonus_amount for p in payments if p.commission_type == "SELLER"
        )
        total_commission = buyer_commission + seller_commission

        # Get unique sales
        unique_sales = set(p.bicycle_sale_id for p in payments)

        return {
            "branch_id": branch_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "buyer_commission": float(buyer_commission),
            "seller_commission": float(seller_commission),
            "total_commission": float(total_commission),
            "sale_count": len(unique_sales),
            "payment_count": len(payments),
        }

    @staticmethod
    async def get_sale_commissions(
        db: AsyncSession,
        sale_id: str
    ) -> list[BonusPayment]:
        """
        Get all commission payments for a specific sale.

        Args:
            db: Database session
            sale_id: BicycleSale ID

        Returns:
            List of BonusPayment objects
        """
        result = await db.execute(
            select(BonusPayment)
            .where(BonusPayment.bicycle_sale_id == sale_id)
            .order_by(BonusPayment.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def approve_commission(
        db: AsyncSession,
        payment_id: str,
        approved_by: str
    ) -> BonusPayment:
        """
        Approve a commission payment.

        Args:
            db: Database session
            payment_id: BonusPayment ID
            approved_by: User ID of approver

        Returns:
            Updated BonusPayment object

        Raises:
            ValueError: If payment cannot be approved
        """
        result = await db.execute(
            select(BonusPayment).where(BonusPayment.id == payment_id)
        )
        payment = result.scalar_one()

        if not payment.can_approve():
            raise ValueError(f"Commission payment {payment_id} cannot be approved (status: {payment.status})")

        payment.status = "APPROVED"
        payment.approved_by = approved_by
        payment.approved_at = datetime.utcnow()

        return payment

    @staticmethod
    async def pay_commission(
        db: AsyncSession,
        payment_id: str,
        payment_reference: str = None
    ) -> BonusPayment:
        """
        Mark a commission payment as paid.

        Args:
            db: Database session
            payment_id: BonusPayment ID
            payment_reference: Payment reference/transaction ID

        Returns:
            Updated BonusPayment object

        Raises:
            ValueError: If payment cannot be marked as paid
        """
        result = await db.execute(
            select(BonusPayment).where(BonusPayment.id == payment_id)
        )
        payment = result.scalar_one()

        if not payment.can_pay():
            raise ValueError(f"Commission payment {payment_id} cannot be paid (status: {payment.status})")

        payment.status = "PAID"
        payment.paid_at = datetime.utcnow()
        payment.payment_reference = payment_reference

        return payment
