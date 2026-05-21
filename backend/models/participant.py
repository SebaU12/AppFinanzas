"""
Participant model - Represents people sharing finances.
"""
import uuid
from sqlalchemy import Column, String, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Participant(Base):
    __tablename__ = "participants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    active = Column(Boolean, default=True, nullable=False)
    default_percentage = Column(Float, nullable=False, default=50.0)

    # Relationships
    credit_cards = relationship("CreditCard", back_populates="participant")

    def __repr__(self):
        return f"<Participant(id={self.id}, name={self.name}, active={self.active})>"
