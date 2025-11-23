"""Analytics Service - KPI calculations and business intelligence"""

from datetime import datetime, timedelta
from typing import Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from ..models.journal_entry import JournalEntry, JournalEntryStatus
from ..models.petty_cash import PettyCashVoucher, PettyCashFloat
from ..models.chart_of_accounts import ChartOfAccounts, AccountCategory
from ..models.commission_rule import CommissionRule


class AnalyticsService:
    """Service for analytics and KPI calculations"""

    @staticmethod
    async def get_executive_dashboard_kpis(
        db: AsyncSession, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None
    ) -> dict:
        """Get executive dashboard KPIs"""
        if not date_from:
            date_from = datetime.now() - timedelta(days=30)
        if not date_to:
            date_to = datetime.now()

        # Get revenue accounts
        revenue_accounts_result = await db.execute(
            select(ChartOfAccounts.id).where(ChartOfAccounts.category == AccountCategory.REVENUE.value)
        )
        revenue_account_ids = [row[0] for row in revenue_accounts_result.all()]

        # Get expense accounts
        expense_accounts_result = await db.execute(
            select(ChartOfAccounts.id).where(ChartOfAccounts.category == AccountCategory.EXPENSE.value)
        )
        expense_account_ids = [row[0] for row in expense_accounts_result.all()]

        # Calculate total revenue (simplified - would need proper journal entry line queries)
        total_revenue = Decimal("0")
        total_expenses = Decimal("0")

        # Get posted journal entries count
        posted_entries_result = await db.execute(
            select(func.count(JournalEntry.id)).where(
                and_(
                    JournalEntry.status == JournalEntryStatus.POSTED.value,
                    JournalEntry.entry_date >= date_from.date(),
                    JournalEntry.entry_date <= date_to.date(),
                )
            )
        )
        posted_entries_count = posted_entries_result.scalar_one()

        # Get total petty cash disbursements
        petty_cash_result = await db.execute(
            select(func.sum(PettyCashVoucher.amount)).where(
                and_(
                    PettyCashVoucher.voucher_type == "DISBURSEMENT",
                    PettyCashVoucher.status == "POSTED",
                    PettyCashVoucher.voucher_date >= date_from.date(),
                    PettyCashVoucher.voucher_date <= date_to.date(),
                )
            )
        )
        petty_cash_total = petty_cash_result.scalar_one() or Decimal("0")

        # Get active floats count
        active_floats_result = await db.execute(select(func.count(PettyCashFloat.id)).where(PettyCashFloat.is_active == True))
        active_floats = active_floats_result.scalar_one()

        # Get active commission rules count
        active_rules_result = await db.execute(select(func.count(CommissionRule.id)).where(CommissionRule.is_active == True))
        active_rules = active_rules_result.scalar_one()

        return {
            "period": {
                "from": date_from.strftime("%Y-%m-%d"),
                "to": date_to.strftime("%Y-%m-%d"),
            },
            "financial": {
                "total_revenue": float(total_revenue),
                "total_expenses": float(total_expenses),
                "net_profit": float(total_revenue - total_expenses),
                "profit_margin": (
                    float((total_revenue - total_expenses) / total_revenue * 100) if total_revenue > 0 else 0
                ),
            },
            "journal_entries": {
                "posted_count": posted_entries_count,
            },
            "petty_cash": {
                "total_disbursements": float(petty_cash_total),
                "active_floats": active_floats,
            },
            "commissions": {
                "active_rules": active_rules,
            },
        }

    @staticmethod
    async def get_sales_analytics(
        db: AsyncSession,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        branch_id: Optional[str] = None,
    ) -> dict:
        """Get sales analytics data"""
        if not date_from:
            date_from = datetime.now() - timedelta(days=30)
        if not date_to:
            date_to = datetime.now()

        # This is a simplified version - in production, you'd query actual sales tables
        # For now, we'll use journal entries as a proxy

        conditions = [
            JournalEntry.entry_type == "VEHICLE_SALE",
            JournalEntry.status == JournalEntryStatus.POSTED.value,
            JournalEntry.entry_date >= date_from.date(),
            JournalEntry.entry_date <= date_to.date(),
        ]

        if branch_id:
            conditions.append(JournalEntry.branch_id == branch_id)

        # Total sales count
        sales_count_result = await db.execute(select(func.count(JournalEntry.id)).where(and_(*conditions)))
        total_sales = sales_count_result.scalar_one()

        # Total sales amount
        sales_amount_result = await db.execute(select(func.sum(JournalEntry.total_credit)).where(and_(*conditions)))
        total_amount = sales_amount_result.scalar_one() or Decimal("0")

        # Average sale value
        avg_sale = float(total_amount) / total_sales if total_sales > 0 else 0

        # Sales by entry type
        type_breakdown_result = await db.execute(
            select(JournalEntry.entry_type, func.count(JournalEntry.id), func.sum(JournalEntry.total_credit)).where(
                and_(
                    JournalEntry.status == JournalEntryStatus.POSTED.value,
                    JournalEntry.entry_date >= date_from.date(),
                    JournalEntry.entry_date <= date_to.date(),
                )
            ).group_by(JournalEntry.entry_type)
        )

        type_breakdown = []
        for entry_type, count, amount in type_breakdown_result.all():
            type_breakdown.append(
                {
                    "type": entry_type,
                    "count": count,
                    "total_amount": float(amount or 0),
                }
            )

        return {
            "period": {
                "from": date_from.strftime("%Y-%m-%d"),
                "to": date_to.strftime("%Y-%m-%d"),
            },
            "summary": {
                "total_sales": total_sales,
                "total_amount": float(total_amount),
                "average_sale": avg_sale,
            },
            "breakdown_by_type": type_breakdown,
        }

    @staticmethod
    async def get_commission_analytics(
        db: AsyncSession, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None
    ) -> dict:
        """Get commission analytics"""
        if not date_from:
            date_from = datetime.now() - timedelta(days=30)
        if not date_to:
            date_to = datetime.now()

        # Get commission rules by type
        rules_by_type_result = await db.execute(
            select(CommissionRule.commission_type, func.count(CommissionRule.id))
            .where(CommissionRule.is_active == True)
            .group_by(CommissionRule.commission_type)
        )

        rules_by_type = []
        for comm_type, count in rules_by_type_result.all():
            rules_by_type.append({"type": comm_type, "count": count})

        # Get formula type distribution
        formula_distribution_result = await db.execute(
            select(CommissionRule.formula_type, func.count(CommissionRule.id))
            .where(CommissionRule.is_active == True)
            .group_by(CommissionRule.formula_type)
        )

        formula_distribution = []
        for formula_type, count in formula_distribution_result.all():
            formula_distribution.append({"formula": formula_type, "count": count})

        return {
            "rules_by_type": rules_by_type,
            "formula_distribution": formula_distribution,
            "total_active_rules": sum(item["count"] for item in rules_by_type),
        }

    @staticmethod
    async def get_accounting_summary(db: AsyncSession) -> dict:
        """Get accounting summary statistics"""
        # Total accounts by category
        accounts_by_category_result = await db.execute(
            select(ChartOfAccounts.category, func.count(ChartOfAccounts.id))
            .where(ChartOfAccounts.is_active == True)
            .group_by(ChartOfAccounts.category)
        )

        accounts_by_category = []
        for category, count in accounts_by_category_result.all():
            accounts_by_category.append({"category": category, "count": count})

        # Journal entry status breakdown
        entry_status_result = await db.execute(
            select(JournalEntry.status, func.count(JournalEntry.id)).group_by(JournalEntry.status)
        )

        entry_status = []
        for status, count in entry_status_result.all():
            entry_status.append({"status": status, "count": count})

        # Petty cash voucher status breakdown
        voucher_status_result = await db.execute(
            select(PettyCashVoucher.status, func.count(PettyCashVoucher.id)).group_by(PettyCashVoucher.status)
        )

        voucher_status = []
        for status, count in voucher_status_result.all():
            voucher_status.append({"status": status, "count": count})

        return {
            "accounts_by_category": accounts_by_category,
            "journal_entry_status": entry_status,
            "petty_cash_voucher_status": voucher_status,
        }

    @staticmethod
    async def get_trend_data(
        db: AsyncSession, metric: str, date_from: datetime, date_to: datetime, interval: str = "day"
    ) -> list[dict]:
        """Get trend data for charting"""
        # This would generate time-series data for charts
        # Simplified version - in production would use date_trunc SQL function

        if metric == "journal_entries":
            # Get entries grouped by date
            result = await db.execute(
                select(JournalEntry.entry_date, func.count(JournalEntry.id))
                .where(
                    and_(
                        JournalEntry.entry_date >= date_from.date(),
                        JournalEntry.entry_date <= date_to.date(),
                        JournalEntry.status == JournalEntryStatus.POSTED.value,
                    )
                )
                .group_by(JournalEntry.entry_date)
                .order_by(JournalEntry.entry_date)
            )

            trend_data = []
            for entry_date, count in result.all():
                trend_data.append(
                    {
                        "date": entry_date.strftime("%Y-%m-%d"),
                        "value": count,
                    }
                )
            return trend_data

        return []
