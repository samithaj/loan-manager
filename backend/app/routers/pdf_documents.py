"""PDF Document Generation endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from pydantic import BaseModel
from decimal import Decimal

from ..db import get_db
from ..rbac import require_permission
from ..services.pdf_generation_service import PDFGenerationService

router = APIRouter(prefix="/v1/pdf", tags=["PDF Generation"])


class VehicleSaleInvoiceRequest(BaseModel):
    invoice_number: str
    sale_date: str
    customer_name: str
    customer_address: str
    customer_mobile: str
    vehicle_make_model: str
    vehicle_year: int
    vehicle_color: str
    vehicle_chassis: str
    vehicle_engine: str
    vehicle_condition: str
    sale_amount: float
    paid_amount: float
    payment_method: str
    salesperson_name: str
    branch_name: str


class PettyCashReceiptRequest(BaseModel):
    voucher_number: str
    voucher_date: str
    voucher_type: str
    amount: float
    description: str
    payee_name: str
    category: str
    approved_by: str
    custodian_name: str


class CommissionStatementRequest(BaseModel):
    employee_name: str
    employee_id: str
    period_start: str
    period_end: str
    commissions: list[dict]
    total_commission: float


@router.post(
    "/vehicle-sale-invoice",
    dependencies=[Depends(require_permission("create:invoices"))],
)
async def generate_vehicle_sale_invoice(
    request: VehicleSaleInvoiceRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate vehicle sale invoice PDF"""
    try:
        vehicle_details = {
            "make_model": request.vehicle_make_model,
            "year": request.vehicle_year,
            "color": request.vehicle_color,
            "chassis_number": request.vehicle_chassis,
            "engine_number": request.vehicle_engine,
            "condition": request.vehicle_condition,
        }

        pdf_buffer = PDFGenerationService.generate_vehicle_sale_invoice(
            invoice_number=request.invoice_number,
            sale_date=datetime.fromisoformat(request.sale_date),
            customer_name=request.customer_name,
            customer_address=request.customer_address,
            customer_mobile=request.customer_mobile,
            vehicle_details=vehicle_details,
            sale_amount=Decimal(str(request.sale_amount)),
            paid_amount=Decimal(str(request.paid_amount)),
            payment_method=request.payment_method,
            salesperson_name=request.salesperson_name,
            branch_name=request.branch_name,
        )

        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=invoice_{request.invoice_number}.pdf"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/petty-cash-receipt",
    dependencies=[Depends(require_permission("view:petty_cash"))],
)
async def generate_petty_cash_receipt(
    request: PettyCashReceiptRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate petty cash receipt PDF"""
    try:
        pdf_buffer = PDFGenerationService.generate_petty_cash_receipt(
            voucher_number=request.voucher_number,
            voucher_date=datetime.fromisoformat(request.voucher_date),
            voucher_type=request.voucher_type,
            amount=Decimal(str(request.amount)),
            description=request.description,
            payee_name=request.payee_name,
            category=request.category,
            approved_by=request.approved_by,
            custodian_name=request.custodian_name,
        )

        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=voucher_{request.voucher_number}.pdf"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/commission-statement",
    dependencies=[Depends(require_permission("view:commission_rules"))],
)
async def generate_commission_statement(
    request: CommissionStatementRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate commission statement PDF"""
    try:
        pdf_buffer = PDFGenerationService.generate_commission_statement(
            employee_name=request.employee_name,
            employee_id=request.employee_id,
            period_start=datetime.fromisoformat(request.period_start),
            period_end=datetime.fromisoformat(request.period_end),
            commissions=request.commissions,
            total_commission=Decimal(str(request.total_commission)),
        )

        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=commission_statement_{request.employee_id}.pdf"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
