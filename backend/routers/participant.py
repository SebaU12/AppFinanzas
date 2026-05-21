"""
API routes for Participant operations.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from schemas.participant import ParticipantCreate, ParticipantUpdate, ParticipantResponse
from services.participant import ParticipantService

router = APIRouter(
    prefix="/participants",
    tags=["participants"]
)


@router.post("/", response_model=ParticipantResponse, status_code=status.HTTP_201_CREATED)
def create_participant(
    participant: ParticipantCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new participant.

    - **name**: Participant name (required, unique)
    - **active**: Whether participant is active in current month (default: True)
    - **default_percentage**: Default percentage for reimbursements (0-100, default: 50.0)
    """
    return ParticipantService.create(db, participant)


@router.get("/", response_model=list[ParticipantResponse])
def get_participants(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get all participants.

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **active_only**: Filter to show only active participants
    """
    return ParticipantService.get_all(db, skip=skip, limit=limit, active_only=active_only)


@router.get("/{participant_id}", response_model=ParticipantResponse)
def get_participant(
    participant_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific participant by ID.
    """
    return ParticipantService.get_by_id(db, participant_id)


@router.put("/{participant_id}", response_model=ParticipantResponse)
def update_participant(
    participant_id: UUID,
    participant: ParticipantUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing participant.

    All fields are optional. Only provided fields will be updated.
    """
    return ParticipantService.update(db, participant_id, participant)


@router.delete("/{participant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_participant(
    participant_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a participant.
    """
    ParticipantService.delete(db, participant_id)
    return None
