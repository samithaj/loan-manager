from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Numeric, Date, DateTime, Time, Boolean, Text, UUID
from datetime import datetime, date, time
from typing import Optional
from enum import Enum
from ..db import Base


class AttendanceStatus(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    HALF_DAY = "HALF_DAY"
    ON_LEAVE = "ON_LEAVE"
    HOLIDAY = "HOLIDAY"
    WEEKEND = "WEEKEND"


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(UUID, nullable=False)  # References users.id
    date: Mapped[date] = mapped_column(Date, nullable=False)
    clock_in: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    clock_out: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default=AttendanceStatus.ABSENT.value)
    work_hours: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    overtime_hours: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def calculate_work_hours(self) -> float:
        """Calculate total work hours from clock in/out times"""
        if self.clock_in and self.clock_out:
            delta = self.clock_out - self.clock_in
            hours = delta.total_seconds() / 3600
            return round(hours, 2)
        return 0.0

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": str(self.user_id),
            "date": self.date.isoformat() if self.date else None,
            "clock_in": self.clock_in.isoformat() if self.clock_in else None,
            "clock_out": self.clock_out.isoformat() if self.clock_out else None,
            "status": self.status,
            "work_hours": float(self.work_hours) if self.work_hours else 0.0,
            "overtime_hours": float(self.overtime_hours),
            "notes": self.notes,
            "location": self.location,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class WorkSchedule(Base):
    __tablename__ = "work_schedules"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    monday_start: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    monday_end: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    tuesday_start: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    tuesday_end: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    wednesday_start: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    wednesday_end: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    thursday_start: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    thursday_end: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    friday_start: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    friday_end: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    saturday_start: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    saturday_end: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    sunday_start: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    sunday_end: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "monday_start": self.monday_start.isoformat() if self.monday_start else None,
            "monday_end": self.monday_end.isoformat() if self.monday_end else None,
            "tuesday_start": self.tuesday_start.isoformat() if self.tuesday_start else None,
            "tuesday_end": self.tuesday_end.isoformat() if self.tuesday_end else None,
            "wednesday_start": self.wednesday_start.isoformat() if self.wednesday_start else None,
            "wednesday_end": self.wednesday_end.isoformat() if self.wednesday_end else None,
            "thursday_start": self.thursday_start.isoformat() if self.thursday_start else None,
            "thursday_end": self.thursday_end.isoformat() if self.thursday_end else None,
            "friday_start": self.friday_start.isoformat() if self.friday_start else None,
            "friday_end": self.friday_end.isoformat() if self.friday_end else None,
            "saturday_start": self.saturday_start.isoformat() if self.saturday_start else None,
            "saturday_end": self.saturday_end.isoformat() if self.saturday_end else None,
            "sunday_start": self.sunday_start.isoformat() if self.sunday_start else None,
            "sunday_end": self.sunday_end.isoformat() if self.sunday_end else None,
            "is_default": self.is_default,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class UserWorkSchedule(Base):
    __tablename__ = "user_work_schedules"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(UUID, nullable=False)  # References users.id
    schedule_id: Mapped[str] = mapped_column(String, nullable=False)  # References work_schedules.id
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": str(self.user_id),
            "schedule_id": self.schedule_id,
            "effective_from": self.effective_from.isoformat() if self.effective_from else None,
            "effective_to": self.effective_to.isoformat() if self.effective_to else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
