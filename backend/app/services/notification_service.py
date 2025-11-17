from __future__ import annotations

from typing import Optional
from loguru import logger
from ..models.bicycle_application import BicycleApplication
from ..models.bicycle import Bicycle


# Email configuration (would come from settings in production)
# For now, we'll just log the emails
EMAIL_ENABLED = False  # Set to True when SMTP is configured


async def send_application_submitted_email(
    application: BicycleApplication,
    bicycle: Optional[Bicycle] = None
) -> bool:
    """
    Send confirmation email to customer after application submission.

    Args:
        application: The submitted application
        bicycle: The bicycle they applied for (optional)

    Returns:
        True if email sent successfully, False otherwise
    """
    if not EMAIL_ENABLED:
        logger.info(
            f"[EMAIL SIMULATION] Application submitted confirmation to {application.email or application.phone}"
        )
        logger.info(f"  Application ID: {application.id}")
        logger.info(f"  Customer: {application.full_name}")
        if bicycle:
            logger.info(f"  Bicycle: {bicycle.title}")
        logger.info(f"  Status: {application.status}")
        logger.info("  Message: Thank you for your application. We will review it within 48 hours.")
        return True

    # TODO: Implement actual email sending when SMTP is configured
    # Example:
    # subject = f"Application Received - {application.id}"
    # body = f"""
    # Dear {application.full_name},
    #
    # Thank you for your bicycle hire purchase application.
    #
    # Application ID: {application.id}
    # Bicycle: {bicycle.title if bicycle else 'N/A'}
    # Branch: {application.branch_id}
    #
    # We will review your application and contact you within 48 hours.
    #
    # Best regards,
    # Bicycle Hire Purchase Team
    # """
    #
    # return send_email(to=application.email, subject=subject, body=body)

    return True


async def send_new_application_notification(
    application: BicycleApplication,
    bicycle: Optional[Bicycle] = None
) -> bool:
    """
    Send notification to branch staff about new application.

    Args:
        application: The submitted application
        bicycle: The bicycle they applied for (optional)

    Returns:
        True if notification sent successfully, False otherwise
    """
    if not EMAIL_ENABLED:
        logger.info(
            f"[EMAIL SIMULATION] New application notification to branch {application.branch_id}"
        )
        logger.info(f"  Application ID: {application.id}")
        logger.info(f"  Customer: {application.full_name} ({application.phone})")
        if bicycle:
            logger.info(f"  Bicycle: {bicycle.title} ({bicycle.id})")
        logger.info(f"  Down Payment: {application.down_payment}")
        logger.info(f"  Tenure: {application.tenure_months} months")
        logger.info("  Action Required: Review application")
        return True

    # TODO: Implement actual notification when configured
    # Get branch staff emails and send notification

    return True


async def send_application_approved_email(
    application: BicycleApplication,
    bicycle: Optional[Bicycle] = None,
    loan_id: Optional[str] = None
) -> bool:
    """
    Send approval confirmation email to customer.

    Args:
        application: The approved application
        bicycle: The bicycle they applied for (optional)
        loan_id: The created loan ID (optional)

    Returns:
        True if email sent successfully, False otherwise
    """
    if not EMAIL_ENABLED:
        logger.info(
            f"[EMAIL SIMULATION] Application approved notification to {application.email or application.phone}"
        )
        logger.info(f"  Application ID: {application.id}")
        logger.info(f"  Customer: {application.full_name}")
        if bicycle:
            logger.info(f"  Bicycle: {bicycle.title}")
        if loan_id:
            logger.info(f"  Loan ID: {loan_id}")
        logger.info("  Message: Congratulations! Your application has been approved.")
        logger.info(f"  Next Steps: Please visit branch {application.branch_id} to complete the process.")
        return True

    # TODO: Implement actual email sending
    # subject = f"Application Approved - {application.id}"
    # body = f"""
    # Dear {application.full_name},
    #
    # Congratulations! Your bicycle hire purchase application has been approved.
    #
    # Application ID: {application.id}
    # Loan ID: {loan_id}
    # Bicycle: {bicycle.title if bicycle else 'N/A'}
    #
    # Next Steps:
    # 1. Visit our {application.branch_id} branch
    # 2. Bring your identification documents
    # 3. Complete the loan disbursement process
    #
    # Branch Contact: [Branch Phone/Email]
    #
    # Best regards,
    # Bicycle Hire Purchase Team
    # """

    return True


async def send_application_rejected_email(
    application: BicycleApplication,
    bicycle: Optional[Bicycle] = None
) -> bool:
    """
    Send rejection notification email to customer.

    Args:
        application: The rejected application
        bicycle: The bicycle they applied for (optional)

    Returns:
        True if email sent successfully, False otherwise
    """
    if not EMAIL_ENABLED:
        logger.info(
            f"[EMAIL SIMULATION] Application rejected notification to {application.email or application.phone}"
        )
        logger.info(f"  Application ID: {application.id}")
        logger.info(f"  Customer: {application.full_name}")
        if bicycle:
            logger.info(f"  Bicycle: {bicycle.title}")
        logger.info(f"  Reason: {application.notes or 'Not specified'}")
        logger.info("  Message: Unfortunately, we cannot approve your application at this time.")
        logger.info("  Contact: Please contact us for more information.")
        return True

    # TODO: Implement actual email sending
    # subject = f"Application Update - {application.id}"
    # body = f"""
    # Dear {application.full_name},
    #
    # Thank you for your interest in our bicycle hire purchase program.
    #
    # Application ID: {application.id}
    #
    # Unfortunately, we are unable to approve your application at this time.
    #
    # Reason: {application.notes or 'Please contact us for more information'}
    #
    # If you have any questions or would like to discuss this further,
    # please contact our branch at {application.branch_id}.
    #
    # Best regards,
    # Bicycle Hire Purchase Team
    # """

    return True


async def send_sms_notification(phone: str, message: str) -> bool:
    """
    Send SMS notification (optional feature).

    Args:
        phone: Phone number
        message: SMS message

    Returns:
        True if SMS sent successfully, False otherwise
    """
    # TODO: Implement SMS service integration (Twilio, etc.)
    logger.info(f"[SMS SIMULATION] To: {phone}")
    logger.info(f"  Message: {message}")
    return True
