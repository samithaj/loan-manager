"""Chart of Accounts service - Account hierarchy management"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import Optional
import uuid

from ..models.chart_of_accounts import ChartOfAccounts, AccountCategory
from ..schemas.accounting_schemas import (
    ChartOfAccountsCreate,
    ChartOfAccountsUpdate,
)


class ChartOfAccountsService:
    """Service for managing chart of accounts"""

    @staticmethod
    async def get_account(db: AsyncSession, account_id: str) -> Optional[ChartOfAccounts]:
        """Get account by ID"""
        result = await db.execute(
            select(ChartOfAccounts).where(ChartOfAccounts.id == account_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_account_by_code(db: AsyncSession, account_code: str) -> Optional[ChartOfAccounts]:
        """Get account by code"""
        result = await db.execute(
            select(ChartOfAccounts).where(ChartOfAccounts.account_code == account_code)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_accounts(
        db: AsyncSession,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_header: Optional[bool] = None,
        branch_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[ChartOfAccounts], int]:
        """List accounts with filters"""
        # Build query conditions
        conditions = []
        if category:
            conditions.append(ChartOfAccounts.category == category)
        if is_active is not None:
            conditions.append(ChartOfAccounts.is_active == is_active)
        if is_header is not None:
            conditions.append(ChartOfAccounts.is_header == is_header)
        if branch_id:
            conditions.append(ChartOfAccounts.branch_id == branch_id)

        # Get total count
        count_query = select(func.count(ChartOfAccounts.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        # Get accounts
        query = select(ChartOfAccounts).order_by(
            ChartOfAccounts.account_code
        )
        if conditions:
            query = query.where(and_(*conditions))
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        accounts = result.scalars().all()

        return list(accounts), total

    @staticmethod
    async def get_account_hierarchy(db: AsyncSession) -> list[ChartOfAccounts]:
        """Get full account hierarchy (all top-level accounts with children)"""
        result = await db.execute(
            select(ChartOfAccounts)
            .where(ChartOfAccounts.parent_account_id.is_(None))
            .order_by(ChartOfAccounts.account_code)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_account(
        db: AsyncSession,
        account_data: ChartOfAccountsCreate,
        created_by: str
    ) -> ChartOfAccounts:
        """Create account"""
        # Check if account code already exists
        existing = await ChartOfAccountsService.get_account_by_code(db, account_data.account_code)
        if existing:
            raise ValueError(f"Account code {account_data.account_code} already exists")

        # Determine normal balance based on category
        normal_balance = ChartOfAccounts.determine_normal_balance(account_data.category.value)

        # Calculate level if parent is specified
        level = account_data.level
        if account_data.parent_account_id:
            parent = await ChartOfAccountsService.get_account(db, account_data.parent_account_id)
            if parent:
                level = parent.level + 1

        account = ChartOfAccounts(
            id=str(uuid.uuid4()),
            **account_data.model_dump(),
            normal_balance=normal_balance,
            level=level,
            is_system=False,
            created_by=created_by
        )
        db.add(account)
        await db.commit()
        await db.refresh(account)
        return account

    @staticmethod
    async def update_account(
        db: AsyncSession,
        account_id: str,
        account_data: ChartOfAccountsUpdate
    ) -> Optional[ChartOfAccounts]:
        """Update account"""
        account = await ChartOfAccountsService.get_account(db, account_id)
        if not account:
            return None

        # Prevent editing system accounts
        if account.is_system:
            raise ValueError("Cannot modify system accounts")

        # Check for account code uniqueness if changing code
        if account_data.account_code and account_data.account_code != account.account_code:
            existing = await ChartOfAccountsService.get_account_by_code(db, account_data.account_code)
            if existing:
                raise ValueError(f"Account code {account_data.account_code} already exists")

        # Update fields
        update_data = account_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(account, field, value)

        # Recalculate normal balance if category changed
        if 'category' in update_data:
            account.normal_balance = ChartOfAccounts.determine_normal_balance(account.category)

        # Recalculate level if parent changed
        if 'parent_account_id' in update_data:
            if account.parent_account_id:
                parent = await ChartOfAccountsService.get_account(db, account.parent_account_id)
                if parent:
                    account.level = parent.level + 1
            else:
                account.level = 0

        await db.commit()
        await db.refresh(account)
        return account

    @staticmethod
    async def delete_account(db: AsyncSession, account_id: str) -> bool:
        """Delete account"""
        account = await ChartOfAccountsService.get_account(db, account_id)
        if not account:
            return False

        # Prevent deleting system accounts
        if account.is_system:
            raise ValueError("Cannot delete system accounts")

        # Check if account has children
        children_result = await db.execute(
            select(func.count(ChartOfAccounts.id)).where(
                ChartOfAccounts.parent_account_id == account_id
            )
        )
        children_count = children_result.scalar_one()
        if children_count > 0:
            raise ValueError("Cannot delete account with sub-accounts")

        # TODO: Check if account has journal entries
        # This would require importing JournalEntryLine and checking

        await db.delete(account)
        await db.commit()
        return True

    @staticmethod
    async def seed_default_accounts(db: AsyncSession, created_by: str):
        """Seed default chart of accounts"""
        default_accounts = [
            # Assets
            {"code": "1000", "name": "Assets", "category": "ASSET", "type": "CURRENT_ASSET", "is_header": True},
            {"code": "1100", "name": "Current Assets", "category": "ASSET", "type": "CURRENT_ASSET", "is_header": True, "parent_code": "1000"},
            {"code": "1110", "name": "Cash on Hand", "category": "ASSET", "type": "CASH_AND_BANK", "parent_code": "1100"},
            {"code": "1120", "name": "Cash in Bank", "category": "ASSET", "type": "CASH_AND_BANK", "parent_code": "1100"},
            {"code": "1130", "name": "Petty Cash", "category": "ASSET", "type": "CASH_AND_BANK", "parent_code": "1100"},
            {"code": "1200", "name": "Inventory", "category": "ASSET", "type": "INVENTORY", "is_header": True, "parent_code": "1000"},
            {"code": "1210", "name": "Vehicle Inventory", "category": "ASSET", "type": "INVENTORY", "parent_code": "1200"},
            {"code": "1220", "name": "Parts Inventory", "category": "ASSET", "type": "INVENTORY", "parent_code": "1200"},
            {"code": "1300", "name": "Fixed Assets", "category": "ASSET", "type": "FIXED_ASSET", "is_header": True, "parent_code": "1000"},

            # Liabilities
            {"code": "2000", "name": "Liabilities", "category": "LIABILITY", "type": "CURRENT_LIABILITY", "is_header": True},
            {"code": "2100", "name": "Accounts Payable", "category": "LIABILITY", "type": "ACCOUNTS_PAYABLE", "parent_code": "2000"},

            # Equity
            {"code": "3000", "name": "Equity", "category": "EQUITY", "type": "OWNER_EQUITY", "is_header": True},
            {"code": "3100", "name": "Owner's Capital", "category": "EQUITY", "type": "OWNER_EQUITY", "parent_code": "3000"},
            {"code": "3200", "name": "Retained Earnings", "category": "EQUITY", "type": "RETAINED_EARNINGS", "parent_code": "3000"},

            # Revenue
            {"code": "4000", "name": "Revenue", "category": "REVENUE", "type": "SALES_REVENUE", "is_header": True},
            {"code": "4100", "name": "Vehicle Sales", "category": "REVENUE", "type": "SALES_REVENUE", "parent_code": "4000"},
            {"code": "4200", "name": "Repair Services", "category": "REVENUE", "type": "SERVICE_REVENUE", "parent_code": "4000"},

            # Expenses
            {"code": "5000", "name": "Expenses", "category": "EXPENSE", "type": "OPERATING_EXPENSE", "is_header": True},
            {"code": "5100", "name": "Cost of Goods Sold", "category": "EXPENSE", "type": "COST_OF_GOODS_SOLD", "parent_code": "5000"},
            {"code": "5200", "name": "Salaries Expense", "category": "EXPENSE", "type": "OPERATING_EXPENSE", "parent_code": "5000"},
            {"code": "5300", "name": "Commission Expense", "category": "EXPENSE", "type": "OPERATING_EXPENSE", "parent_code": "5000"},
            {"code": "5400", "name": "Repair Expenses", "category": "EXPENSE", "type": "OPERATING_EXPENSE", "parent_code": "5000"},
        ]

        # Create accounts with parent relationships
        code_to_id = {}
        for acc_data in default_accounts:
            parent_id = None
            if "parent_code" in acc_data:
                parent_id = code_to_id.get(acc_data["parent_code"])

            normal_balance = ChartOfAccounts.determine_normal_balance(acc_data["category"])
            level = 0
            if parent_id:
                parent_result = await db.execute(
                    select(ChartOfAccounts).where(ChartOfAccounts.id == parent_id)
                )
                parent = parent_result.scalar_one_or_none()
                if parent:
                    level = parent.level + 1

            account = ChartOfAccounts(
                id=str(uuid.uuid4()),
                account_code=acc_data["code"],
                account_name=acc_data["name"],
                category=acc_data["category"],
                account_type=acc_data["type"],
                parent_account_id=parent_id,
                level=level,
                is_header=acc_data.get("is_header", False),
                normal_balance=normal_balance,
                is_active=True,
                is_system=True,  # Mark as system account
                created_by=created_by
            )
            db.add(account)
            code_to_id[acc_data["code"]] = account.id

        await db.commit()
