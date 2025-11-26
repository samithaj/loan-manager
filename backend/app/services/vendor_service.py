"""Vendor/Supplier service for business logic"""
from __future__ import annotations

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Tuple
from datetime import datetime, date
import secrets

from ..models.vendor import Vendor, VendorCategory, VendorContact
from ..models.company import Company


class VendorService:
    """Service for vendor management operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def generate_vendor_code(company_code: str, sequence: int) -> str:
        """Generate vendor code: {company_code}-VEN-{sequence}"""
        return f"{company_code}-VEN-{sequence:04d}"

    @staticmethod
    def generate_vendor_id() -> str:
        """Generate unique vendor ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = secrets.token_hex(4).upper()
        return f"VEN-{timestamp}-{random_suffix}"

    async def get_next_vendor_code(self, company_id: str) -> str:
        """Get next available vendor code for company"""
        # Get company code
        company = await self.db.get(Company, company_id)
        if not company:
            raise ValueError(f"Company {company_id} not found")

        # Get highest sequence number for this company
        stmt = select(func.max(Vendor.vendor_code)).where(
            and_(
                Vendor.company_id == company_id,
                Vendor.vendor_code.like(f"{company.id}-VEN-%")
            )
        )
        result = await self.db.execute(stmt)
        max_code = result.scalar_one_or_none()

        if max_code:
            # Extract sequence number and increment
            try:
                seq = int(max_code.split("-VEN-")[1]) + 1
            except (IndexError, ValueError):
                seq = 1
        else:
            seq = 1

        return self.generate_vendor_code(company.id, seq)

    async def create_vendor(
        self,
        company_id: str,
        name: str,
        created_by: str,
        vendor_code: Optional[str] = None,
        contact_person: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        province: Optional[str] = None,
        postal_code: Optional[str] = None,
        tax_id: Optional[str] = None,
        payment_terms: Optional[str] = None,
        credit_limit: float = 0,
        category_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Vendor:
        """Create a new vendor"""
        # Generate vendor code if not provided
        if not vendor_code:
            vendor_code = await self.get_next_vendor_code(company_id)

        # Check if vendor code already exists
        stmt = select(Vendor).where(
            and_(
                Vendor.company_id == company_id,
                Vendor.vendor_code == vendor_code
            )
        )
        existing = (await self.db.execute(stmt)).scalar_one_or_none()
        if existing:
            raise ValueError(f"Vendor code {vendor_code} already exists for this company")

        vendor = Vendor(
            id=self.generate_vendor_id(),
            company_id=company_id,
            vendor_code=vendor_code,
            name=name,
            contact_person=contact_person,
            phone=phone,
            email=email,
            address=address,
            city=city,
            province=province,
            postal_code=postal_code,
            tax_id=tax_id,
            payment_terms=payment_terms,
            credit_limit=credit_limit,
            category_id=category_id,
            notes=notes,
            created_by=created_by,
        )

        self.db.add(vendor)
        await self.db.flush()
        await self.db.refresh(vendor)

        return vendor

    async def update_vendor(
        self,
        vendor_id: str,
        **updates
    ) -> Vendor:
        """Update vendor fields"""
        vendor = await self.db.get(Vendor, vendor_id)
        if not vendor:
            raise ValueError(f"Vendor {vendor_id} not found")

        # Update allowed fields
        allowed_fields = {
            "name", "contact_person", "phone", "email",
            "address", "city", "province", "postal_code",
            "tax_id", "business_registration_no",
            "payment_terms", "credit_limit", "currency",
            "bank_name", "bank_account_no", "bank_branch",
            "is_active", "category_id", "notes"
        }

        for key, value in updates.items():
            if key in allowed_fields and value is not None:
                setattr(vendor, key, value)

        vendor.updated_at = datetime.utcnow()

        await self.db.flush()
        await self.db.refresh(vendor)

        return vendor

    async def get_vendor(self, vendor_id: str) -> Optional[Vendor]:
        """Get vendor by ID"""
        return await self.db.get(Vendor, vendor_id)

    async def list_vendors(
        self,
        company_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        category_id: Optional[str] = None,
        search: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Vendor], int]:
        """List vendors with filters"""
        stmt = select(Vendor)

        # Filters
        filters = []
        if company_id:
            filters.append(Vendor.company_id == company_id)
        if is_active is not None:
            filters.append(Vendor.is_active == is_active)
        if category_id:
            filters.append(Vendor.category_id == category_id)
        if search:
            search_pattern = f"%{search}%"
            filters.append(
                or_(
                    Vendor.name.ilike(search_pattern),
                    Vendor.vendor_code.ilike(search_pattern),
                    Vendor.contact_person.ilike(search_pattern)
                )
            )

        if filters:
            stmt = stmt.where(and_(*filters))

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.db.scalar(count_stmt) or 0

        # Apply pagination
        stmt = stmt.order_by(Vendor.name).offset(offset).limit(limit)

        # Execute
        result = await self.db.execute(stmt)
        vendors = result.scalars().all()

        return list(vendors), total

    async def delete_vendor(self, vendor_id: str) -> bool:
        """Delete vendor (soft delete by setting inactive)"""
        vendor = await self.db.get(Vendor, vendor_id)
        if not vendor:
            return False

        vendor.is_active = False
        vendor.updated_at = datetime.utcnow()

        await self.db.flush()
        return True

    async def add_vendor_contact(
        self,
        vendor_id: str,
        name: str,
        position: Optional[str] = None,
        phone: Optional[str] = None,
        mobile: Optional[str] = None,
        email: Optional[str] = None,
        is_primary: bool = False,
        notes: Optional[str] = None,
    ) -> VendorContact:
        """Add contact person to vendor"""
        vendor = await self.db.get(Vendor, vendor_id)
        if not vendor:
            raise ValueError(f"Vendor {vendor_id} not found")

        # If this is primary, unset other primary contacts
        if is_primary:
            stmt = select(VendorContact).where(
                and_(
                    VendorContact.vendor_id == vendor_id,
                    VendorContact.is_primary == True
                )
            )
            existing_primary = (await self.db.execute(stmt)).scalars().all()
            for contact in existing_primary:
                contact.is_primary = False

        contact_id = f"VCT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"

        contact = VendorContact(
            id=contact_id,
            vendor_id=vendor_id,
            name=name,
            position=position,
            phone=phone,
            mobile=mobile,
            email=email,
            is_primary=is_primary,
            notes=notes,
        )

        self.db.add(contact)
        await self.db.flush()
        await self.db.refresh(contact)

        return contact

    async def list_vendor_contacts(self, vendor_id: str) -> List[VendorContact]:
        """List contacts for a vendor"""
        stmt = select(VendorContact).where(
            VendorContact.vendor_id == vendor_id
        ).order_by(VendorContact.is_primary.desc(), VendorContact.name)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_vendor_metrics(
        self,
        vendor_id: str,
        purchase_amount: float,
        purchase_date: date
    ):
        """Update vendor performance metrics after a purchase"""
        vendor = await self.db.get(Vendor, vendor_id)
        if not vendor:
            return

        vendor.total_purchases = float(vendor.total_purchases or 0) + purchase_amount
        vendor.total_orders = (vendor.total_orders or 0) + 1
        vendor.last_purchase_date = purchase_date
        vendor.updated_at = datetime.utcnow()

        await self.db.flush()
