from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class PriceTick(Base):
    __tablename__ = 'price_ticks'

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    price = Column(Float, nullable=False)
    timestamp = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index('idx_ticker_timestamp', 'ticker', 'timestamp'),)

    def to_dict(self):
        return {
            'id': self.id,
            'ticker': self.ticker,
            'price': self.price,
            'timestamp': self.timestamp,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
