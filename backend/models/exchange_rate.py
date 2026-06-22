"""
ExchangeRate model - Monthly configured exchange rates between currencies.

PEN is the base currency. Rates are stored as units of PEN per 1 unit of foreign currency.
Example: from_currency=USD, to_currency=PEN, rate=3.75 means 1 USD = 3.75 PEN.
"""
import uuid
from sqlalchemy import Column, String, Numeric, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base
from models.transaction import Currency


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    month = Column(String(7), nullable=False)           # YYYY-MM
    from_currency = Column(SQLEnum(Currency), nullable=False)  # e.g. USD
    to_currency = Column(SQLEnum(Currency), nullable=False)    # always PEN
    rate = Column(Numeric(12, 6), nullable=False)       # units of to_currency per 1 from_currency

    __table_args__ = (
        UniqueConstraint("month", "from_currency", "to_currency", name="uq_exchange_rate_month_pair"),
    )

    def __repr__(self):
        return f"<ExchangeRate({self.month}: 1 {self.from_currency} = {self.rate} {self.to_currency})>"
