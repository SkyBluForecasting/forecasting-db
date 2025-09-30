from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# TODO: Eventually as our schema grows, should split this out into multiple files.


class Forecasts(Base):
    __tablename__ = "forecasts"

    asset_uuid = Column(String(50), primary_key=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    forecast_uuid = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    forecast_kw = Column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint("forecast_uuid"),
        Index("ix_forecasts_forecast_uuid", "forecast_uuid"),
    )


class ForecastRuns(Base):
    __tablename__ = "forecast_runs"

    forecast_uuid = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    run_uuid = Column(String(50), nullable=False)
    asset_uuid = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    frequency_min = Column(Float, nullable=False)

    # FK to Forecasts
    __table_args__ = (
        ForeignKeyConstraint(["forecast_uuid"], ["forecasts.forecast_uuid"]),
        Index("ix_forecast_runs_asset_uuid", "asset_uuid"),
    )


class Constraints(Base):
    __tablename__ = "constraints"

    asset_uuid = Column(String(50), primary_key=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    forecast_uuid = Column(UUID(as_uuid=True), primary_key=True, nullable=False)

    constraint_kw = Column(Float, nullable=False)

    __table_args__ = (Index("ix_constraints_forecast_uuid", "forecast_uuid"),)


class Measurements(Base):
    __tablename__ = "measurements"

    asset_uuid = Column(String(50), primary_key=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    metric = Column(String(50), primary_key=True, nullable=False)

    value = Column(Float, nullable=False)
