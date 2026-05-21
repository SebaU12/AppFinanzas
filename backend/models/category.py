"""
Category model - Defines financial categories and their accounting behavior.
"""
import uuid
from sqlalchemy import Column, String, Boolean, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class CategoryType(str, enum.Enum):
    """Category type enumeration"""
    INCOME = "income"
    EXPENSE = "expense"


class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    type = Column(SQLEnum(CategoryType), nullable=False)
    is_personal = Column(Boolean, default=False, nullable=False)
    allows_credit = Column(Boolean, default=False, nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)

    # Self-referential relationship
    parent = relationship("Category", remote_side=[id], back_populates="subcategories")
    subcategories = relationship("Category", back_populates="parent", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name}, type={self.type}, parent_id={self.parent_id})>"
