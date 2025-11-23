"""Customer KYC service - Business logic for guarantors, employment, and bank accounts"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import Optional
from datetime import datetime
import uuid

from ..models.customer_guarantor import CustomerGuarantor
from ..models.customer_employment import CustomerEmployment
from ..models.customer_bank_account import CustomerBankAccount
from ..schemas.customer_kyc_schemas import (
    CustomerGuarantorCreate,
    CustomerGuarantorUpdate,
    CustomerEmploymentCreate,
    CustomerEmploymentUpdate,
    CustomerBankAccountCreate,
    CustomerBankAccountUpdate,
)


class CustomerKYCService:
    """Service for managing customer KYC data"""

    # ============= CustomerGuarantor Methods =============

    @staticmethod
    async def get_guarantor(db: AsyncSession, guarantor_id: str) -> Optional[CustomerGuarantor]:
        """Get guarantor by ID"""
        result = await db.execute(
            select(CustomerGuarantor).where(CustomerGuarantor.id == guarantor_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_guarantors(
        db: AsyncSession,
        customer_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[CustomerGuarantor], int]:
        """List guarantors for a customer"""
        # Get total count
        count_result = await db.execute(
            select(func.count(CustomerGuarantor.id)).where(
                CustomerGuarantor.customer_id == customer_id
            )
        )
        total = count_result.scalar_one()

        # Get guarantors
        result = await db.execute(
            select(CustomerGuarantor)
            .where(CustomerGuarantor.customer_id == customer_id)
            .order_by(CustomerGuarantor.is_primary.desc(), CustomerGuarantor.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        guarantors = result.scalars().all()

        return list(guarantors), total

    @staticmethod
    async def create_guarantor(
        db: AsyncSession,
        guarantor_data: CustomerGuarantorCreate,
        created_by: str
    ) -> CustomerGuarantor:
        """Create a new guarantor"""
        # If this is set as primary, unset other primary guarantors for this customer
        if guarantor_data.is_primary:
            await db.execute(
                select(CustomerGuarantor)
                .where(
                    and_(
                        CustomerGuarantor.customer_id == guarantor_data.customer_id,
                        CustomerGuarantor.is_primary == True
                    )
                )
            )
            # Update existing primary guarantors
            result = await db.execute(
                select(CustomerGuarantor).where(
                    and_(
                        CustomerGuarantor.customer_id == guarantor_data.customer_id,
                        CustomerGuarantor.is_primary == True
                    )
                )
            )
            existing_primary = result.scalars().all()
            for g in existing_primary:
                g.is_primary = False

        guarantor = CustomerGuarantor(
            id=str(uuid.uuid4()),
            **guarantor_data.model_dump(),
            created_by=created_by
        )
        db.add(guarantor)
        await db.commit()
        await db.refresh(guarantor)
        return guarantor

    @staticmethod
    async def update_guarantor(
        db: AsyncSession,
        guarantor_id: str,
        guarantor_data: CustomerGuarantorUpdate
    ) -> Optional[CustomerGuarantor]:
        """Update guarantor"""
        guarantor = await CustomerKYCService.get_guarantor(db, guarantor_id)
        if not guarantor:
            return None

        # If setting as primary, unset other primary guarantors
        if guarantor_data.is_primary and not guarantor.is_primary:
            result = await db.execute(
                select(CustomerGuarantor).where(
                    and_(
                        CustomerGuarantor.customer_id == guarantor.customer_id,
                        CustomerGuarantor.is_primary == True
                    )
                )
            )
            existing_primary = result.scalars().all()
            for g in existing_primary:
                g.is_primary = False

        # Update fields
        update_data = guarantor_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(guarantor, field, value)

        await db.commit()
        await db.refresh(guarantor)
        return guarantor

    @staticmethod
    async def delete_guarantor(db: AsyncSession, guarantor_id: str) -> bool:
        """Delete guarantor"""
        guarantor = await CustomerKYCService.get_guarantor(db, guarantor_id)
        if not guarantor:
            return False

        await db.delete(guarantor)
        await db.commit()
        return True

    @staticmethod
    async def verify_guarantor(
        db: AsyncSession,
        guarantor_id: str,
        verified_by: str
    ) -> Optional[CustomerGuarantor]:
        """Verify guarantor"""
        guarantor = await CustomerKYCService.get_guarantor(db, guarantor_id)
        if not guarantor:
            return None

        guarantor.verify(verified_by)
        await db.commit()
        await db.refresh(guarantor)
        return guarantor

    # ============= CustomerEmployment Methods =============

    @staticmethod
    async def get_employment(db: AsyncSession, employment_id: str) -> Optional[CustomerEmployment]:
        """Get employment by ID"""
        result = await db.execute(
            select(CustomerEmployment).where(CustomerEmployment.id == employment_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_employment(
        db: AsyncSession,
        customer_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[CustomerEmployment], int]:
        """List employment records for a customer"""
        # Get total count
        count_result = await db.execute(
            select(func.count(CustomerEmployment.id)).where(
                CustomerEmployment.customer_id == customer_id
            )
        )
        total = count_result.scalar_one()

        # Get employment records
        result = await db.execute(
            select(CustomerEmployment)
            .where(CustomerEmployment.customer_id == customer_id)
            .order_by(CustomerEmployment.is_current.desc(), CustomerEmployment.start_date.desc())
            .offset(skip)
            .limit(limit)
        )
        employment = result.scalars().all()

        return list(employment), total

    @staticmethod
    async def create_employment(
        db: AsyncSession,
        employment_data: CustomerEmploymentCreate,
        created_by: str
    ) -> CustomerEmployment:
        """Create employment record"""
        # Calculate monthly income
        monthly_income = CustomerEmployment.normalize_to_monthly(
            employment_data.gross_income,
            employment_data.income_frequency.value
        )

        employment = CustomerEmployment(
            id=str(uuid.uuid4()),
            **employment_data.model_dump(),
            monthly_income=monthly_income,
            created_by=created_by
        )
        db.add(employment)
        await db.commit()
        await db.refresh(employment)
        return employment

    @staticmethod
    async def update_employment(
        db: AsyncSession,
        employment_id: str,
        employment_data: CustomerEmploymentUpdate
    ) -> Optional[CustomerEmployment]:
        """Update employment record"""
        employment = await CustomerKYCService.get_employment(db, employment_id)
        if not employment:
            return None

        # Update fields
        update_data = employment_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(employment, field, value)

        # Recalculate monthly income if gross_income or income_frequency changed
        if 'gross_income' in update_data or 'income_frequency' in update_data:
            employment.monthly_income = CustomerEmployment.normalize_to_monthly(
                employment.gross_income,
                employment.income_frequency
            )

        await db.commit()
        await db.refresh(employment)
        return employment

    @staticmethod
    async def delete_employment(db: AsyncSession, employment_id: str) -> bool:
        """Delete employment record"""
        employment = await CustomerKYCService.get_employment(db, employment_id)
        if not employment:
            return False

        await db.delete(employment)
        await db.commit()
        return True

    @staticmethod
    async def verify_employment(
        db: AsyncSession,
        employment_id: str,
        verified_by: str,
        verification_method: str
    ) -> Optional[CustomerEmployment]:
        """Verify employment"""
        employment = await CustomerKYCService.get_employment(db, employment_id)
        if not employment:
            return None

        employment.verify(verified_by, verification_method)
        await db.commit()
        await db.refresh(employment)
        return employment

    # ============= CustomerBankAccount Methods =============

    @staticmethod
    async def get_bank_account(db: AsyncSession, account_id: str) -> Optional[CustomerBankAccount]:
        """Get bank account by ID"""
        result = await db.execute(
            select(CustomerBankAccount).where(CustomerBankAccount.id == account_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_bank_accounts(
        db: AsyncSession,
        customer_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[CustomerBankAccount], int]:
        """List bank accounts for a customer"""
        # Get total count
        count_result = await db.execute(
            select(func.count(CustomerBankAccount.id)).where(
                CustomerBankAccount.customer_id == customer_id
            )
        )
        total = count_result.scalar_one()

        # Get bank accounts
        result = await db.execute(
            select(CustomerBankAccount)
            .where(CustomerBankAccount.customer_id == customer_id)
            .order_by(CustomerBankAccount.is_primary.desc(), CustomerBankAccount.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        accounts = result.scalars().all()

        return list(accounts), total

    @staticmethod
    async def create_bank_account(
        db: AsyncSession,
        account_data: CustomerBankAccountCreate,
        created_by: str
    ) -> CustomerBankAccount:
        """Create bank account"""
        # If this is set as primary, unset other primary accounts for this customer
        if account_data.is_primary:
            result = await db.execute(
                select(CustomerBankAccount).where(
                    and_(
                        CustomerBankAccount.customer_id == account_data.customer_id,
                        CustomerBankAccount.is_primary == True
                    )
                )
            )
            existing_primary = result.scalars().all()
            for acc in existing_primary:
                acc.is_primary = False

        account = CustomerBankAccount(
            id=str(uuid.uuid4()),
            **account_data.model_dump(),
            created_by=created_by
        )
        db.add(account)
        await db.commit()
        await db.refresh(account)
        return account

    @staticmethod
    async def update_bank_account(
        db: AsyncSession,
        account_id: str,
        account_data: CustomerBankAccountUpdate
    ) -> Optional[CustomerBankAccount]:
        """Update bank account"""
        account = await CustomerKYCService.get_bank_account(db, account_id)
        if not account:
            return None

        # If setting as primary, unset other primary accounts
        if account_data.is_primary and not account.is_primary:
            result = await db.execute(
                select(CustomerBankAccount).where(
                    and_(
                        CustomerBankAccount.customer_id == account.customer_id,
                        CustomerBankAccount.is_primary == True
                    )
                )
            )
            existing_primary = result.scalars().all()
            for acc in existing_primary:
                acc.is_primary = False

        # Update fields
        update_data = account_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(account, field, value)

        await db.commit()
        await db.refresh(account)
        return account

    @staticmethod
    async def delete_bank_account(db: AsyncSession, account_id: str) -> bool:
        """Delete bank account"""
        account = await CustomerKYCService.get_bank_account(db, account_id)
        if not account:
            return False

        await db.delete(account)
        await db.commit()
        return True

    @staticmethod
    async def verify_bank_account(
        db: AsyncSession,
        account_id: str,
        verified_by: str,
        verification_method: str
    ) -> Optional[CustomerBankAccount]:
        """Verify bank account"""
        account = await CustomerKYCService.get_bank_account(db, account_id)
        if not account:
            return None

        account.verify(verified_by, verification_method)
        await db.commit()
        await db.refresh(account)
        return account

    @staticmethod
    async def set_primary_account(
        db: AsyncSession,
        account_id: str,
        customer_id: str
    ) -> Optional[CustomerBankAccount]:
        """Set account as primary"""
        account = await CustomerKYCService.get_bank_account(db, account_id)
        if not account or account.customer_id != customer_id:
            return None

        # Unset other primary accounts
        result = await db.execute(
            select(CustomerBankAccount).where(
                and_(
                    CustomerBankAccount.customer_id == customer_id,
                    CustomerBankAccount.is_primary == True
                )
            )
        )
        existing_primary = result.scalars().all()
        for acc in existing_primary:
            acc.is_primary = False

        # Set this as primary
        account.is_primary = True
        await db.commit()
        await db.refresh(account)
        return account
