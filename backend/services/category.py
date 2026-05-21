"""
CRUD service for Category operations.
"""
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from models.category import Category, CategoryType
from schemas.category import CategoryCreate, CategoryUpdate
from seeds.categories_seed import CATEGORIES_SEED


class CategoryService:
    """Service for managing Category operations"""

    @staticmethod
    def seed_categories(db: Session) -> dict:
        """Seed the database with fixed category list"""
        created_count = 0
        skipped_count = 0

        for category_data in CATEGORIES_SEED:
            existing = db.query(Category).filter(Category.name == category_data["name"]).first()
            if not existing:
                category = Category(**category_data)
                db.add(category)
                created_count += 1
            else:
                skipped_count += 1

        db.commit()
        return {
            "message": "Categories seeded successfully",
            "created": created_count,
            "skipped": skipped_count,
            "total": len(CATEGORIES_SEED)
        }

    @staticmethod
    def create(db: Session, category_data: CategoryCreate) -> Category:
        """Create a new category"""
        try:
            category = Category(**category_data.model_dump())
            db.add(category)
            db.commit()
            db.refresh(category)
            return category
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category with this name already exists"
            )

    @staticmethod
    def get_by_id(db: Session, category_id: UUID) -> Category:
        """Get category by ID"""
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {category_id} not found"
            )
        return category

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        category_type: CategoryType | None = None,
        personal_only: bool | None = None,
        allows_credit_only: bool | None = None
    ) -> list[Category]:
        """Get all categories with optional filtering"""
        query = db.query(Category)

        if category_type:
            query = query.filter(Category.type == category_type)
        if personal_only is not None:
            query = query.filter(Category.is_personal == personal_only)
        if allows_credit_only is not None:
            query = query.filter(Category.allows_credit == allows_credit_only)

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, category_id: UUID, category_data: CategoryUpdate) -> Category:
        """Update an existing category"""
        category = CategoryService.get_by_id(db, category_id)

        update_data = category_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)

        try:
            db.commit()
            db.refresh(category)
            return category
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category with this name already exists"
            )

    @staticmethod
    def delete(db: Session, category_id: UUID) -> None:
        """Delete a category"""
        category = CategoryService.get_by_id(db, category_id)
        db.delete(category)
        db.commit()
