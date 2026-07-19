"""
TalentUP Fichaje — BillingRecord model.
Tracks Stripe subscription and invoice history per tenant.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Text
from app.database import Base


class BillingRecord(Base):
    __tablename__ = "billing_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), nullable=False, index=True)
    stripe_customer_id = Column(String(100), nullable=True)
    stripe_subscription_id = Column(String(100), nullable=True)
    plan = Column(String(20), nullable=False, default="basic")
    amount = Column(Numeric(10, 2), nullable=True)
    status = Column(String(20), nullable=False, default="incomplete")
    current_period_end = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "stripe_customer_id": self.stripe_customer_id,
            "stripe_subscription_id": self.stripe_subscription_id,
            "plan": self.plan,
            "amount": float(self.amount) if self.amount else None,
            "status": self.status,
            "current_period_end": self.current_period_end.isoformat() if self.current_period_end else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
