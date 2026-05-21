"""
API routes for Category operations.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from models.category import CategoryType
from schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from services.category import CategoryService

router = APIRouter(
    prefix="/categories",
    tags=["categories"]
)


@router.post("/seed", status_code=status.HTTP_200_OK)
def seed_categories(db: Session = Depends(get_db)):
    """
    Seed the database with the fixed category list (Spanish labels).

    This endpoint populates the database with all predefined categories.
    Safe to run multiple times - will skip existing categories.
    """
    return CategoryService.seed_categories(db)


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new category.

    - **name**: Category name in Spanish (required, unique)
    - **type**: Category type: income or expense
    - **is_personal**: Excluded from reimbursements if True (default: False)
    - **allows_credit**: Whether credit card payments are allowed (default: False)
    """
    return CategoryService.create(db, category)


@router.get("/", response_model=list[CategoryResponse])
def get_categories(
    skip: int = 0,
    limit: int = 100,
    type: CategoryType | None = Query(None, description="Filter by category type"),
    personal_only: bool | None = Query(None, description="Filter personal categories"),
    allows_credit_only: bool | None = Query(None, description="Filter categories that allow credit"),
    db: Session = Depends(get_db)
):
    """
    Get all categories with optional filtering.

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **type**: Filter by income or expense
    - **personal_only**: Show only personal/non-personal categories
    - **allows_credit_only**: Show only categories that allow/don't allow credit
    """
    return CategoryService.get_all(
        db,
        skip=skip,
        limit=limit,
        category_type=type,
        personal_only=personal_only,
        allows_credit_only=allows_credit_only
    )


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific category by ID.
    """
    return CategoryService.get_by_id(db, category_id)


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: UUID,
    category: CategoryUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing category.

    All fields are optional. Only provided fields will be updated.
    """
    return CategoryService.update(db, category_id, category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a category.
    """
    CategoryService.delete(db, category_id)
    return None
