"""
CRUD service for Participant operations.
"""
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from models.participant import Participant
from schemas.participant import ParticipantCreate, ParticipantUpdate


class ParticipantService:
    """Service for managing Participant operations"""

    @staticmethod
    def create(db: Session, participant_data: ParticipantCreate) -> Participant:
        """Create a new participant"""
        try:
            participant = Participant(**participant_data.model_dump())
            db.add(participant)
            db.commit()
            db.refresh(participant)
            return participant
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Participant with this name already exists"
            )

    @staticmethod
    def get_by_id(db: Session, participant_id: UUID) -> Participant:
        """Get participant by ID"""
        participant = db.query(Participant).filter(Participant.id == participant_id).first()
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Participant with id {participant_id} not found"
            )
        return participant

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100, active_only: bool = False) -> list[Participant]:
        """Get all participants with optional filtering"""
        query = db.query(Participant)
        if active_only:
            query = query.filter(Participant.active == True)
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, participant_id: UUID, participant_data: ParticipantUpdate) -> Participant:
        """Update an existing participant"""
        participant = ParticipantService.get_by_id(db, participant_id)

        update_data = participant_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(participant, field, value)

        try:
            db.commit()
            db.refresh(participant)
            return participant
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Participant with this name already exists"
            )

    @staticmethod
    def delete(db: Session, participant_id: UUID) -> None:
        """Delete a participant"""
        participant = ParticipantService.get_by_id(db, participant_id)
        db.delete(participant)
        db.commit()
