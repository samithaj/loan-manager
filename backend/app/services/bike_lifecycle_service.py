"""
Bike Lifecycle Service

Handles the complete lifecycle of second-hand bikes:
- Procurement (purchase/acquisition)
- Cost tracking and calculation
- Sales with P&L calculation
- Commission triggering
"""

from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets

from ..models import Bicycle, BicycleSale, Office
from .stock_number_service import StockNumberService
from .commission_service import CommissionService


class BikeLifecycleService:
    """Service for managing bicycle lifecycle from procurement to sale"""

    @staticmethod
    async def procure_bike(
        db: AsyncSession,
        procurement_data: dict
    ) -> Bicycle:
        """
        Create new bike procurement record.
        Automatically generates first stock number.

        Args:
            db: Database session
            procurement_data: Dictionary containing procurement details
                Required: branch_id, license_plate, title, model, purchase_price
                Optional: year, condition, procurement_source, etc.

        Returns:
            Bicycle object with assigned stock number
        """
        # Generate bike ID
        bike_id = f"BK-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4).upper()}"

        # Get company from branch
        result = await db.execute(
            select(Office).where(Office.id == procurement_data["branch_id"])
        )
        branch = result.scalar_one()

        if not branch.company_id:
            raise ValueError(f"Branch {procurement_data['branch_id']} is not linked to a company")

        company_id = branch.company_id

        # Create bicycle
        bicycle = Bicycle(
            id=bike_id,
            company_id=company_id,
            business_model=procurement_data.get("business_model", "STOCK"),
            branch_id=procurement_data["branch_id"],
            license_plate=procurement_data.get("license_plate"),
            frame_number=procurement_data.get("frame_number"),
            engine_number=procurement_data.get("engine_number"),
            title=procurement_data["title"],
            brand=procurement_data.get("brand", "Unknown"),
            model=procurement_data["model"],
            year=procurement_data.get("year", datetime.now().year),
            condition=procurement_data.get("condition", "USED"),
            mileage_km=procurement_data.get("mileage_km"),
            description=procurement_data.get("description"),

            # Pricing
            purchase_price=procurement_data["purchase_price"],
            cash_price=procurement_data.get("cash_price", procurement_data["purchase_price"]),
            hire_purchase_price=procurement_data.get("hire_purchase_price", procurement_data["purchase_price"]),
            base_purchase_price=procurement_data["purchase_price"],

            status="IN_STOCK",

            # Procurement details
            procurement_date=procurement_data.get("procurement_date", date.today()),
            procurement_source=procurement_data.get("procurement_source"),
            bought_method=procurement_data.get("bought_method"),
            hand_amount=procurement_data.get("hand_amount"),
            settlement_amount=procurement_data.get("settlement_amount"),
            payment_branch_id=procurement_data.get("payment_branch_id"),
            cr_location=procurement_data.get("cr_location"),
            buyer_employee_id=procurement_data.get("buyer_employee_id"),

            # Control flags
            first_od=procurement_data.get("first_od"),
            ldate=procurement_data.get("ldate"),
            sk_flag=procurement_data.get("sk_flag", False),
            ls_flag=procurement_data.get("ls_flag", False),
            caller=procurement_data.get("caller"),
            house_use=procurement_data.get("house_use", False),
        )
        db.add(bicycle)
        await db.flush()

        # Assign first stock number
        await StockNumberService.assign_stock_number(
            db,
            bicycle_id=bike_id,
            company_id=company_id,
            branch_id=procurement_data["branch_id"],
            reason="PURCHASE",
            notes="Initial procurement"
        )

        return bicycle

    @staticmethod
    async def calculate_bike_cost_summary(
        db: AsyncSession,
        bicycle_id: str
    ) -> dict:
        """
        Calculate detailed cost breakdown for a bike.
        Returns dictionary similar to summery.xlsx row.

        Args:
            db: Database session
            bicycle_id: Bicycle ID

        Returns:
            Dictionary with cost breakdown
        """
        result = await db.execute(
            select(Bicycle).where(Bicycle.id == bicycle_id)
        )
        bike = result.scalar_one()

        purchase_price = Decimal(str(bike.base_purchase_price or 0))
        branch_expenses = Decimal(str(bike.get_total_branch_expenses))
        garage_expenses = Decimal(str(bike.total_repair_cost or 0))
        total_expenses = purchase_price + branch_expenses + garage_expenses

        selling_price = Decimal(str(bike.selling_price or 0))
        profit_or_loss = selling_price - total_expenses if selling_price else None

        return {
            "bicycle_id": bike.id,
            "bike_no": bike.license_plate,
            "model": bike.model,
            "brand": bike.brand,
            "branch": bike.current_branch_id,
            "stock_number": bike.current_stock_number,
            "received_date": bike.procurement_date.isoformat() if bike.procurement_date else None,
            "purchased_price": float(purchase_price),
            "branch_expenses": float(branch_expenses),
            "garage_expenses": float(garage_expenses),
            "total_expenses": float(total_expenses),
            "released_date": bike.sold_date.isoformat() if bike.sold_date else None,
            "selling_price": float(selling_price) if selling_price else None,
            "profit_or_loss": float(profit_or_loss) if profit_or_loss else None,
            "status": bike.status,
        }

    @staticmethod
    async def sell_bike(
        db: AsyncSession,
        bicycle_id: str,
        sale_data: dict
    ) -> BicycleSale:
        """
        Record bike sale, update bike status, calculate P&L, and trigger commission.

        Args:
            db: Database session
            bicycle_id: Bicycle ID
            sale_data: Dictionary containing sale details
                Required: selling_price, payment_method, sold_by
                Optional: customer details, finance details, etc.

        Returns:
            BicycleSale object

        Raises:
            ValueError: If bike is already sold or not in sellable status
        """
        # Get bike
        result = await db.execute(
            select(Bicycle).where(Bicycle.id == bicycle_id)
        )
        bike = result.scalar_one()

        # Validate bike is sellable
        if bike.status == "SOLD":
            raise ValueError("Bicycle already sold")
        if bike.status not in ["IN_STOCK", "AVAILABLE"]:
            raise ValueError(f"Cannot sell bicycle in status {bike.status}")

        # Get current stock number
        current_assignment = await StockNumberService.get_current_assignment(db, bicycle_id)
        stock_number_at_sale = current_assignment.full_stock_number if current_assignment else None

        # Calculate costs
        cost_summary = await BikeLifecycleService.calculate_bike_cost_summary(db, bicycle_id)
        total_cost = Decimal(str(cost_summary["total_expenses"]))
        selling_price = Decimal(str(sale_data["selling_price"]))
        profit_or_loss = selling_price - total_cost

        # Get selling branch and company
        selling_branch_id = sale_data.get("selling_branch_id", bike.current_branch_id)
        result = await db.execute(
            select(Office).where(Office.id == selling_branch_id)
        )
        selling_branch = result.scalar_one()
        selling_company_id = selling_branch.company_id

        # Create sale record
        sale_id = f"SALE-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
        sale = BicycleSale(
            id=sale_id,
            bicycle_id=bicycle_id,
            selling_branch_id=selling_branch_id,
            selling_company_id=selling_company_id,
            stock_number_at_sale=stock_number_at_sale,
            sale_date=sale_data.get("sale_date", date.today()),
            selling_price=selling_price,
            payment_method=sale_data["payment_method"],

            # Customer details
            customer_name=sale_data.get("customer_name"),
            customer_phone=sale_data.get("customer_phone"),
            customer_email=sale_data.get("customer_email"),
            customer_address=sale_data.get("customer_address"),
            customer_nic=sale_data.get("customer_nic"),

            # Trade-in details
            trade_in_bicycle_id=sale_data.get("trade_in_bicycle_id"),
            trade_in_value=sale_data.get("trade_in_value"),

            # Finance details
            finance_institution=sale_data.get("finance_institution"),
            down_payment=sale_data.get("down_payment"),
            financed_amount=sale_data.get("financed_amount"),

            # Sale details
            sold_by=sale_data["sold_by"],
            sale_invoice_number=sale_data.get("sale_invoice_number"),
            delivery_date=sale_data.get("delivery_date"),
            warranty_months=sale_data.get("warranty_months"),

            # Computed fields
            total_cost=total_cost,
            profit_or_loss=profit_or_loss,
            notes=sale_data.get("notes"),
        )
        db.add(sale)

        # Update bicycle status
        bike.status = "SOLD"
        bike.sold_date = sale.sale_date
        bike.selling_price = selling_price

        await db.flush()

        # Calculate and record commissions
        await CommissionService.calculate_bike_sale_commission(db, sale_id)

        return sale

    @staticmethod
    async def update_branch_expenses(
        db: AsyncSession,
        bicycle_id: str
    ) -> float:
        """
        Recalculate and update total_branch_expenses on bicycle.

        Args:
            db: Database session
            bicycle_id: Bicycle ID

        Returns:
            Updated total branch expenses
        """
        result = await db.execute(
            select(Bicycle).where(Bicycle.id == bicycle_id)
        )
        bike = result.scalar_one()

        total = bike.get_total_branch_expenses
        bike.total_branch_expenses = total

        return total
