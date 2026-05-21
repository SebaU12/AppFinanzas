"""
Pydantic schemas for Category operations.
"""
from uuid import UUID
from pydantic import BaseModel, Field
from models.category import CategoryType


class CategoryBase(BaseModel):
    """Base schema for Category"""
    name: str = Field(..., min_length=1, max_length=100, description="Category name (in Spanish)")
    type: CategoryType = Field(..., description="Category type: income or expense")
    is_personal: bool = Field(default=False, description="Excluded from reimbursements if True")
    allows_credit: bool = Field(default=False, description="Whether credit card payments are allowed")
    parent_id: UUID | None = Field(None, description="Parent category ID for subcategories")


class CategoryCreate(CategoryBase):
    """Schema for creating a new Category"""
    pass


class CategoryUpdate(BaseModel):
    """Schema for updating a Category"""
    name: str | None = Field(None, min_length=1, max_length=100)
    type: CategoryType | None = None
    is_personal: bool | None = None
    allows_credit: bool | None = None
    parent_id: UUID | None = None


class CategoryResponse(CategoryBase):
    """Schema for Category response"""
    id: UUID

    class Config:
        from_attributes = True
