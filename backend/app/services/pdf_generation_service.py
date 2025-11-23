"""PDF Generation Service - Generate invoices and receipts"""

from datetime import datetime
from decimal import Decimal
from io import BytesIO
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfgen import canvas


class PDFGenerationService:
    """Service for generating PDF documents"""

    @staticmethod
    def generate_vehicle_sale_invoice(
        invoice_number: str,
        sale_date: datetime,
        customer_name: str,
        customer_address: str,
        customer_mobile: str,
        vehicle_details: dict,
        sale_amount: Decimal,
        paid_amount: Decimal,
        payment_method: str,
        salesperson_name: str,
        branch_name: str,
        company_info: Optional[dict] = None,
    ) -> BytesIO:
        """Generate vehicle sale invoice PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5 * inch)
        story = []
        styles = getSampleStyleSheet()

        # Company header
        company_name = company_info.get("name", "Loan Manager") if company_info else "Loan Manager"
        company_address = (
            company_info.get("address", "123 Main St, Colombo, Sri Lanka")
            if company_info
            else "123 Main St, Colombo, Sri Lanka"
        )
        company_phone = company_info.get("phone", "+94 11 234 5678") if company_info else "+94 11 234 5678"

        # Title
        title_style = ParagraphStyle(
            "CustomTitle", parent=styles["Heading1"], fontSize=24, textColor=colors.HexColor("#1E40AF"), alignment=1
        )
        story.append(Paragraph(company_name, title_style))
        story.append(Paragraph(f"<font size=10>{company_address}</font>", styles["Normal"]))
        story.append(Paragraph(f"<font size=10>Phone: {company_phone}</font>", styles["Normal"]))
        story.append(Spacer(1, 0.3 * inch))

        # Invoice title
        invoice_title_style = ParagraphStyle(
            "InvoiceTitle", parent=styles["Heading2"], fontSize=18, textColor=colors.HexColor("#DC2626")
        )
        story.append(Paragraph("VEHICLE SALE INVOICE", invoice_title_style))
        story.append(Spacer(1, 0.2 * inch))

        # Invoice details
        invoice_data = [
            ["Invoice Number:", invoice_number, "Date:", sale_date.strftime("%Y-%m-%d")],
            ["Branch:", branch_name, "Sales Person:", salesperson_name],
        ]
        invoice_table = Table(invoice_data, colWidths=[1.5 * inch, 2 * inch, 1.5 * inch, 2 * inch])
        invoice_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(invoice_table)
        story.append(Spacer(1, 0.3 * inch))

        # Customer details
        story.append(Paragraph("<b>CUSTOMER INFORMATION</b>", styles["Heading3"]))
        customer_data = [
            ["Name:", customer_name],
            ["Address:", customer_address],
            ["Mobile:", customer_mobile],
        ]
        customer_table = Table(customer_data, colWidths=[1.5 * inch, 5 * inch])
        customer_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(customer_table)
        story.append(Spacer(1, 0.3 * inch))

        # Vehicle details
        story.append(Paragraph("<b>VEHICLE DETAILS</b>", styles["Heading3"]))
        vehicle_data = [
            ["Make & Model:", vehicle_details.get("make_model", "N/A")],
            ["Year:", str(vehicle_details.get("year", "N/A"))],
            ["Color:", vehicle_details.get("color", "N/A")],
            ["Chassis Number:", vehicle_details.get("chassis_number", "N/A")],
            ["Engine Number:", vehicle_details.get("engine_number", "N/A")],
            ["Condition:", vehicle_details.get("condition", "N/A")],
        ]
        vehicle_table = Table(vehicle_data, colWidths=[2 * inch, 4.5 * inch])
        vehicle_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )
        story.append(vehicle_table)
        story.append(Spacer(1, 0.3 * inch))

        # Payment details
        story.append(Paragraph("<b>PAYMENT DETAILS</b>", styles["Heading3"]))
        balance = float(sale_amount) - float(paid_amount)
        payment_data = [
            ["Description", "Amount (LKR)"],
            ["Sale Amount", f"{float(sale_amount):,.2f}"],
            ["Amount Paid", f"{float(paid_amount):,.2f}"],
            ["Balance Due", f"{balance:,.2f}"],
            ["Payment Method", payment_method],
        ]
        payment_table = Table(payment_data, colWidths=[4 * inch, 2.5 * inch])
        payment_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("BACKGROUND", (0, -2), (-1, -2), colors.HexColor("#FEF3C7")),
                    ("FONTNAME", (0, -2), (-1, -2), "Helvetica-Bold"),
                ]
            )
        )
        story.append(payment_table)
        story.append(Spacer(1, 0.5 * inch))

        # Terms and conditions
        story.append(Paragraph("<b>TERMS AND CONDITIONS</b>", styles["Heading3"]))
        terms = [
            "1. This invoice is valid for 30 days from the date of issue.",
            "2. All payments are non-refundable unless otherwise stated.",
            "3. Vehicle ownership transfer will be completed within 7 business days of full payment.",
            "4. Customer is responsible for all registration and insurance costs.",
        ]
        for term in terms:
            story.append(Paragraph(f"<font size=9>{term}</font>", styles["Normal"]))
        story.append(Spacer(1, 0.5 * inch))

        # Signature section
        signature_data = [
            ["_______________________", "_______________________"],
            ["Customer Signature", "Authorized Signature"],
        ]
        signature_table = Table(signature_data, colWidths=[3 * inch, 3 * inch])
        signature_table.setStyle(
            TableStyle(
                [
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ]
            )
        )
        story.append(signature_table)

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_petty_cash_receipt(
        voucher_number: str,
        voucher_date: datetime,
        voucher_type: str,
        amount: Decimal,
        description: str,
        payee_name: str,
        category: str,
        approved_by: str,
        custodian_name: str,
    ) -> BytesIO:
        """Generate petty cash receipt PDF"""
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Title
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width / 2, height - 50, "PETTY CASH VOUCHER")

        # Voucher type badge
        if voucher_type == "DISBURSEMENT":
            c.setFillColor(colors.HexColor("#DC2626"))
        else:
            c.setFillColor(colors.HexColor("#16A34A"))
        c.rect(width / 2 - 50, height - 80, 100, 20, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(width / 2, height - 75, voucher_type)

        # Reset color
        c.setFillColor(colors.black)

        # Voucher details
        y = height - 120
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Voucher Number:")
        c.setFont("Helvetica", 12)
        c.drawString(200, y, voucher_number)

        y -= 25
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Date:")
        c.setFont("Helvetica", 12)
        c.drawString(200, y, voucher_date.strftime("%Y-%m-%d"))

        y -= 25
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Category:")
        c.setFont("Helvetica", 12)
        c.drawString(200, y, category)

        # Payee/Payer
        y -= 40
        c.setFont("Helvetica-Bold", 14)
        if voucher_type == "DISBURSEMENT":
            c.drawString(50, y, "Paid To:")
        else:
            c.drawString(50, y, "Received From:")
        c.setFont("Helvetica", 14)
        c.drawString(200, y, payee_name)

        # Amount (highlighted box)
        y -= 50
        c.setFillColor(colors.HexColor("#FEF3C7"))
        c.rect(50, y - 30, width - 100, 50, fill=1, stroke=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(60, y - 10, "Amount:")
        c.setFont("Helvetica-Bold", 24)
        c.drawRightString(width - 60, y - 10, f"LKR {float(amount):,.2f}")

        # Description
        y -= 80
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Description:")
        c.setFont("Helvetica", 11)
        # Wrap text if too long
        max_width = width - 120
        words = description.split()
        line = ""
        y -= 20
        for word in words:
            test_line = line + word + " "
            if c.stringWidth(test_line, "Helvetica", 11) < max_width:
                line = test_line
            else:
                c.drawString(60, y, line)
                line = word + " "
                y -= 15
        if line:
            c.drawString(60, y, line)

        # Approval section
        y -= 50
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Approved By:")
        c.setFont("Helvetica", 12)
        c.drawString(200, y, approved_by)

        y -= 25
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Custodian:")
        c.setFont("Helvetica", 12)
        c.drawString(200, y, custodian_name)

        # Signature lines
        y -= 80
        c.line(50, y, 250, y)
        c.line(350, y, 550, y)
        y -= 20
        c.setFont("Helvetica", 10)
        c.drawString(100, y, "Received/Paid By")
        c.drawString(400, y, "Authorized Signature")

        # Footer
        c.setFont("Helvetica-Oblique", 8)
        c.drawCentredString(width / 2, 30, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        c.save()
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_commission_statement(
        employee_name: str,
        employee_id: str,
        period_start: datetime,
        period_end: datetime,
        commissions: list[dict],
        total_commission: Decimal,
    ) -> BytesIO:
        """Generate commission statement PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()

        # Title
        title_style = ParagraphStyle("CustomTitle", parent=styles["Heading1"], fontSize=20, alignment=1)
        story.append(Paragraph("COMMISSION STATEMENT", title_style))
        story.append(Spacer(1, 0.2 * inch))

        # Employee details
        employee_data = [
            ["Employee Name:", employee_name, "Employee ID:", employee_id],
            [
                "Period:",
                f"{period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}",
                "Statement Date:",
                datetime.now().strftime("%Y-%m-%d"),
            ],
        ]
        employee_table = Table(employee_data, colWidths=[1.5 * inch, 2 * inch, 1.5 * inch, 2 * inch])
        employee_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                ]
            )
        )
        story.append(employee_table)
        story.append(Spacer(1, 0.3 * inch))

        # Commissions table
        story.append(Paragraph("<b>COMMISSION DETAILS</b>", styles["Heading3"]))
        table_data = [["Date", "Type", "Sale Amount", "Commission", "Rule"]]
        for comm in commissions:
            table_data.append(
                [
                    comm["date"],
                    comm["type"],
                    f"LKR {float(comm['sale_amount']):,.2f}",
                    f"LKR {float(comm['commission_amount']):,.2f}",
                    comm.get("rule_name", "N/A"),
                ]
            )

        # Total row
        table_data.append(["", "", "", f"LKR {float(total_commission):,.2f}", "TOTAL"])

        commission_table = Table(table_data, colWidths=[1.2 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch, 1.8 * inch])
        commission_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (2, 1), (3, -1), "RIGHT"),
                    ("GRID", (0, 0), (-1, -2), 0.5, colors.grey),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#FEF3C7")),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("LINEABOVE", (0, -1), (-1, -1), 2, colors.black),
                ]
            )
        )
        story.append(commission_table)
        story.append(Spacer(1, 0.5 * inch))

        # Summary box
        summary_style = ParagraphStyle("Summary", parent=styles["Normal"], fontSize=14, alignment=1)
        story.append(
            Paragraph(
                f"<b>Total Commission Earned: LKR {float(total_commission):,.2f}</b>",
                summary_style,
            )
        )

        doc.build(story)
        buffer.seek(0)
        return buffer
