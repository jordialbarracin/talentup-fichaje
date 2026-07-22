"""
TalentUP Fichaje — WorkCalendar model (calendario laboral).
"""
import html
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Integer, Date, DateTime, ForeignKey, Time, Text
# UUID type: String(36) for SQLite compatibility
from app.database import Base


def _s(value):
    """Escape string/Text fields for XSS-safe JSON responses."""
    if value is None:
        return None
    return html.escape(str(value))


class WorkCalendar(Base):
    __tablename__ = "work_calendar"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    year = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)

    day_type = Column(String(20), nullable=False)  # working, holiday, weekend, special
    is_working_day = Column(Boolean, default=True)
    is_holiday = Column(Boolean, default=False)
    is_weekend = Column(Boolean, default=False)

    holiday_id = Column(String(36), ForeignKey("holidays.id"), nullable=True)
    holiday_name = Column(String(200), nullable=True)

    opening_time = Column(Time, nullable=True)
    closing_time = Column(Time, nullable=True)
    requires_special_schedule = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "year": self.year,
            "date": self.date.isoformat() if self.date else None,
            "day_type": self.day_type,
            "is_working_day": self.is_working_day,
            "is_holiday": self.is_holiday,
            "is_weekend": self.is_weekend,
            "holiday_id": str(self.holiday_id) if self.holiday_id else None,
            "holiday_name": _s(self.holiday_name),
            "opening_time": self.opening_time.strftime("%H:%M") if self.opening_time else None,
            "closing_time": self.closing_time.strftime("%H:%M") if self.closing_time else None,
            "requires_special_schedule": self.requires_special_schedule,
            "notes": _s(self.notes),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
