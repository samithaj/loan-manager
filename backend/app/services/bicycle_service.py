from __future__ import annotations

import secrets
import json
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.bicycle import Bicycle, BicycleStatus
from ..models.bicycle_application import BicycleApplication, ApplicationStatus
from ..models.client import Client
from ..models.loan import Loan, Collateral
from ..models.loan_product import LoanProduct
from typing import Optional


def generate_application_id() -> str:
    """
    Generate unique application ID with format: APP-{timestamp}-{random}

    Returns:
        Unique application ID string
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = secrets.token_hex(4).upper()
    return f"APP-{timestamp}-{random_suffix}"


async def get_or_create_client_from_application(
    session: AsyncSession,
    application: BicycleApplication
) -> Client:
    """
    Get existing client or create new one from bicycle application data.

    Searches by NIP number first, then creates if not found.

    Args:
        session: Database session
        application: BicycleApplication instance

    Returns:
        Client instance (existing or newly created)
    """
    client = None

    # Try to find existing client by NIP number
    if application.nip_number:
        stmt = select(Client).where(Client.national_id == application.nip_number)
        result = await session.execute(stmt)
        client = result.scalar_one_or_none()

    if client:
        # Update existing client with latest information
        client.display_name = application.full_name
        client.mobile = application.phone
        client.address = f"{application.address_line1}, {application.city}"
        if application.address_line2:
            client.address = f"{application.address_line1}, {application.address_line2}, {application.city}"
    else:
        # Create new client
        # Generate client ID based on timestamp and random suffix
        client_id = f"CL-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"

        address = f"{application.address_line1}, {application.city}"
        if application.address_line2:
            address = f"{application.address_line1}, {application.address_line2}, {application.city}"

        client = Client(
            id=client_id,
            display_name=application.full_name,
            mobile=application.phone,
            national_id=application.nip_number,
            address=address,
        )
        session.add(client)

    await session.flush()
    return client


async def create_loan_from_application(
    session: AsyncSession,
    application: BicycleApplication,
    bicycle: Bicycle,
    client: Client
) -> Loan:
    """
    Create a loan from an approved bicycle application.

    Args:
        session: Database session
        application: BicycleApplication instance
        bicycle: Bicycle instance
        client: Client instance

    Returns:
        Newly created Loan instance
    """
    # Fetch bicycle hire purchase loan product
    loan_product_stmt = select(LoanProduct).where(LoanProduct.id == "BICYCLE_HP")
    result = await session.execute(loan_product_stmt)
    loan_product = result.scalar_one_or_none()

    if not loan_product:
        raise ValueError("Bicycle hire purchase loan product not found (BICYCLE_HP)")

    # Calculate principal amount
    principal = float(bicycle.hire_purchase_price) - float(application.down_payment)

    # Generate loan ID
    loan_id = f"LN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"

    # Create loan
    loan = Loan(
        id=loan_id,
        client_id=client.id,
        product_id=loan_product.id,
        principal=principal,
        interest_rate=loan_product.interest_rate,
        term_months=application.tenure_months,
        status="PENDING",  # Loan starts in PENDING status, needs to be disbursed
    )

    session.add(loan)
    await session.flush()
    return loan


async def reserve_bicycle(session: AsyncSession, bicycle_id: str) -> Bicycle:
    """
    Reserve a bicycle (mark as RESERVED status).

    Args:
        session: Database session
        bicycle_id: ID of bicycle to reserve

    Returns:
        Updated Bicycle instance

    Raises:
        ValueError: If bicycle not found or not available
    """
    bicycle = await session.get(Bicycle, bicycle_id)

    if not bicycle:
        raise ValueError(f"Bicycle {bicycle_id} not found")

    if bicycle.status != BicycleStatus.AVAILABLE.value:
        raise ValueError(f"Bicycle {bicycle_id} is not available (status: {bicycle.status})")

    bicycle.status = BicycleStatus.RESERVED.value
    await session.flush()
    return bicycle


async def release_bicycle_reservation(session: AsyncSession, bicycle_id: str) -> Bicycle:
    """
    Release a bicycle reservation (mark as AVAILABLE status).

    Args:
        session: Database session
        bicycle_id: ID of bicycle to release

    Returns:
        Updated Bicycle instance

    Raises:
        ValueError: If bicycle not found or not reserved
    """
    bicycle = await session.get(Bicycle, bicycle_id)

    if not bicycle:
        raise ValueError(f"Bicycle {bicycle_id} not found")

    if bicycle.status != BicycleStatus.RESERVED.value:
        raise ValueError(f"Bicycle {bicycle_id} is not reserved (status: {bicycle.status})")

    bicycle.status = BicycleStatus.AVAILABLE.value
    await session.flush()
    return bicycle


async def mark_bicycle_sold(session: AsyncSession, bicycle_id: str, loan_id: str) -> Bicycle:
    """
    Mark a bicycle as sold and link to loan.

    Args:
        session: Database session
        bicycle_id: ID of bicycle
        loan_id: ID of loan to link

    Returns:
        Updated Bicycle instance

    Raises:
        ValueError: If bicycle not found
    """
    bicycle = await session.get(Bicycle, bicycle_id)

    if not bicycle:
        raise ValueError(f"Bicycle {bicycle_id} not found")

    bicycle.status = BicycleStatus.SOLD.value
    await session.flush()
    return bicycle


async def create_collateral_for_bicycle(
    session: AsyncSession,
    loan: Loan,
    bicycle: Bicycle
) -> Collateral:
    """
    Create a collateral record linking bicycle to loan.

    Args:
        session: Database session
        loan: Loan instance
        bicycle: Bicycle instance

    Returns:
        Created Collateral instance
    """
    # Generate collateral ID
    collateral_id = f"COL-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"

    # Create collateral details with bicycle information
    details = json.dumps({
        "bicycle_id": bicycle.id,
        "title": bicycle.title,
        "brand": bicycle.brand,
        "model": bicycle.model,
        "year": bicycle.year,
        "condition": bicycle.condition,
        "license_plate": bicycle.license_plate,
        "frame_number": bicycle.frame_number,
        "engine_number": bicycle.engine_number,
    })

    # Create collateral
    collateral = Collateral(
        id=collateral_id,
        loan_id=loan.id,
        type="VEHICLE",  # Using VEHICLE type for bicycles/motorcycles
        value=float(bicycle.hire_purchase_price),
        details=details
    )

    session.add(collateral)
    await session.flush()
    return collateral


async def approve_application_and_create_loan(
    session: AsyncSession,
    application: BicycleApplication,
    reviewed_by_user_id
) -> Loan:
    """
    Approve an application and create a loan in one transaction.

    This function:
    1. Validates application can be approved
    2. Gets or creates client from application data
    3. Creates loan with calculated values
    4. Creates collateral linking bicycle to loan
    5. Updates application status to CONVERTED_TO_LOAN
    6. Marks bicycle as SOLD
    7. Links application to loan

    Args:
        session: Database session
        application: BicycleApplication to approve
        reviewed_by_user_id: UUID of user approving

    Returns:
        Created Loan instance

    Raises:
        ValueError: If application cannot be approved or bicycle not found
    """
    if not application.can_approve():
        raise ValueError(f"Application {application.id} cannot be approved (status: {application.status})")

    # Get bicycle
    bicycle = await session.get(Bicycle, application.bicycle_id)
    if not bicycle:
        raise ValueError(f"Bicycle {application.bicycle_id} not found")

    # Get or create client
    client = await get_or_create_client_from_application(session, application)

    # Create loan
    loan = await create_loan_from_application(session, application, bicycle, client)

    # Create collateral linking bicycle to loan
    await create_collateral_for_bicycle(session, loan, bicycle)

    # Update application
    application.status = ApplicationStatus.CONVERTED_TO_LOAN.value
    application.loan_id = loan.id
    application.reviewed_by = reviewed_by_user_id
    application.reviewed_at = datetime.utcnow()

    # Mark bicycle as sold
    await mark_bicycle_sold(session, bicycle.id, loan.id)

    await session.flush()
    return loan


async def reject_application_and_release_bicycle(
    session: AsyncSession,
    application: BicycleApplication,
    rejection_notes: str,
    reviewed_by_user_id
) -> None:
    """
    Reject an application and release bicycle reservation.

    Args:
        session: Database session
        application: BicycleApplication to reject
        rejection_notes: Reason for rejection
        reviewed_by_user_id: UUID of user rejecting

    Raises:
        ValueError: If application cannot be rejected
    """
    if not application.can_reject():
        raise ValueError(f"Application {application.id} cannot be rejected (status: {application.status})")

    # Update application
    application.status = ApplicationStatus.REJECTED.value
    application.notes = rejection_notes
    application.reviewed_by = reviewed_by_user_id
    application.reviewed_at = datetime.utcnow()

    # Release bicycle if it's reserved
    bicycle = await session.get(Bicycle, application.bicycle_id)
    if bicycle and bicycle.status == BicycleStatus.RESERVED.value:
        await release_bicycle_reservation(session, bicycle.id)

    await session.flush()
