from sqlalchemy import Column, DateTime, Float, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Forecast(Base):
    __tablename__ = "forecasts"

    asset_uuid = Column(String(50), primary_key=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    forecast_uuid = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    forecast_kw = Column(Float, nullable=False)

    __table_args__ = (Index("ix_forecasts_forecast_uuid", "forecast_uuid"),)
