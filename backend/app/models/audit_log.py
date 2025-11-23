"""Audit log model for tracking changes to records"""

from datetime import datetime
from enum import Enum
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.orm import validates

from ..db import Base


class AuditAction(str, Enum):
    """Audit actions"""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    POST = "POST"
    VOID = "VOID"
    SUBMIT = "SUBMIT"
    RECONCILE = "RECONCILE"


class AuditLog(Base):
    """Audit log model for tracking all changes"""
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))

    # What was changed
    entity_type = Column(String, nullable=False, index=True)  # e.g., "JournalEntry", "PettyCashVoucher"
    entity_id = Column(String, nullable=False, index=True)  # ID of the changed entity
    action = Column(String, nullable=False)  # CREATE, UPDATE, DELETE, APPROVE, etc.

    # Who made the change
    user_id = Column(String, index=True)  # User who made the change
    username = Column(String, nullable=False)  # Username for quick display
    user_role = Column(String)  # Role at the time of action

    # When it happened
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # What changed
    old_values = Column(JSON, nullable=True)  # Previous values (for UPDATE/DELETE)
    new_values = Column(JSON, nullable=True)  # New values (for CREATE/UPDATE)
    changes_summary = Column(Text, nullable=True)  # Human-readable summary

    # Additional context
    ip_address = Column(String, nullable=True)  # IP address of the request
    user_agent = Column(String, nullable=True)  # User agent string
    metadata = Column(JSON, nullable=True)  # Additional metadata

    @validates("action")
    def validate_action(self, key, value):
        """Validate audit action"""
        if value not in [a.value for a in AuditAction]:
            raise ValueError(f"Invalid audit action: {value}")
        return value

    def __repr__(self):
        return f"<AuditLog {self.action} {self.entity_type}:{self.entity_id} by {self.username} at {self.timestamp}>"
