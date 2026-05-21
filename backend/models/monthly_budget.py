"""
MonthlyBudget model - Defines monthly spending limits per category.
"""
import uuid
from sqlalchemy import Column, String, Numeric, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class MonthlyBudget(Base):
    __tablename__ = "monthly_budgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    month = Column(String(7), nullable=False)  # Format: YYYY-MM
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    budgeted_amount = Column(Numeric(10, 2), nullable=False)

    # Relationships
    category = relationship("Category", backref="monthly_budgets")

    # Unique constraint on month + category
    __table_args__ = (
        UniqueConstraint("month", "category_id", name="uq_month_category"),
    )

    def __repr__(self):
        return f"<MonthlyBudget(month={self.month}, category_id={self.category_id}, amount={self.budgeted_amount})>"
