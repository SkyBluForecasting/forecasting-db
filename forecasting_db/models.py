import uuid
from enum import Enum

import sqlalchemy as sa
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
)
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import (
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import backref, declarative_base, relationship

Base = declarative_base()


#
# ─── OPENSTEF SCHEMA ───────────────────────────────────────────────
#


class AssetType(str, Enum):
    system = "system"
    distribution_substation = "distribution_substation"
    pv = "pv"


class Asset(Base):
    __tablename__ = "assets"
    __table_args__ = {"schema": "openstef"}

    asset_uuid = Column(String, primary_key=True)
    name = Column(String, nullable=False)

    asset_type = Column(
        SqlEnum(AssetType, name="asset_type_enum", schema="public"), nullable=False
    )

    capacity_kw = Column(Float, nullable=True)

    measured = Column(Boolean, nullable=False, default=False)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    weather_site_id = Column(String, nullable=True)

    parent_uuid = Column(
        String, ForeignKey("openstef.assets.asset_uuid"), nullable=True
    )

    children = relationship(
        "Asset",
        backref=backref("parent", remote_side=[asset_uuid]),
        cascade="all, delete-orphan",
    )

    depth = Column(Integer, nullable=False)


class PredictionJob(Base):
    __tablename__ = "prediction_job"
    __table_args__ = {"schema": "openstef"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_uuid = Column(
        String, ForeignKey("openstef.assets.asset_uuid"), nullable=False
    )
    model = Column(String(100))
    horizon_minutes = Column(Integer)
    frequency_minutes = Column(Integer)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    config = Column(JSON)

    asset = relationship("Asset", backref="prediction_jobs")


class ForecastRun(Base):
    __tablename__ = "forecast_runs"
    __table_args__ = {"schema": "openstef"}

    forecast_run_id = Column(String, primary_key=True)  # unique per run
    prediction_job_id = Column(
        Integer,
        ForeignKey("openstef.prediction_job.id", ondelete="CASCADE"),
        nullable=False,
    )
    model_run_id = Column(
        String(100), nullable=True
    )  # e.g., MLflow run_id. Null if a simple aggregation forecast.
    asset_uuid = Column(
        String, ForeignKey("openstef.assets.asset_uuid"), nullable=False
    )
    created_at = Column(DateTime(timezone=True), server_default=sa.func.now())
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    frequency_min = Column(Integer)

    prediction_job = relationship("PredictionJob", backref="forecast_runs")
    asset = relationship("Asset", backref="forecast_runs")


class Forecast(Base):
    __tablename__ = "forecast"
    __table_args__ = {"schema": "openstef"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    forecast_run_id = Column(
        String,
        ForeignKey("openstef.forecast_runs.forecast_run_id", ondelete="CASCADE"),
        nullable=False,
    )
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    forecast_value = Column(Float, nullable=False)
    lower_q = Column(Float, nullable=True)  # optional quantiles
    upper_q = Column(Float, nullable=True)

    forecast_run = relationship("ForecastRun", backref="forecasts")


class Measurement(Base):
    __tablename__ = "measurement"
    __table_args__ = (
        sa.UniqueConstraint(
            "asset_uuid",
            "timestamp",
            "metric",
            name="uq_measurement_asset_ts_metric",
        ),
        {"schema": "openstef"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_uuid = Column(
        String,
        ForeignKey("openstef.assets.asset_uuid", ondelete="CASCADE"),
        nullable=False,
    )
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    metric = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)


#
# ─── SKYBLU SCHEMA ───────────────────────────────────────────────
#


class Constraint(Base):
    __tablename__ = "constraints"
    __table_args__ = (
        sa.Index("ix_constraints_asset_ts", "asset_uuid", "timestamp"),
        sa.UniqueConstraint(
            "asset_uuid",
            "timestamp",
            "forecast_run_id",
            name="uq_constraints_asset_ts_run",
        ),
        {"schema": "product"},
    )

    constraint_uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_uuid = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    forecast_run_id = Column(
        String, ForeignKey("openstef.forecast_runs.forecast_run_id"), nullable=False
    )
    constraint_kw = Column(Float, nullable=False)

    forecast_run = relationship("ForecastRun", backref="constraints")


class ForecastError(Base):
    __tablename__ = "forecast_errors"
    __table_args__ = (
        sa.Index("ix_forecast_errors_run_ts", "forecast_run_id", "timestamp"),
        sa.UniqueConstraint(
            "forecast_run_id",
            "timestamp",
            name="uq_forecast_errors_run_ts",
        ),
        {"schema": "product"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    forecast_run_id = Column(
        String,
        ForeignKey("openstef.forecast_runs.forecast_run_id", ondelete="CASCADE"),
        nullable=False,
    )
    timestamp = Column(DateTime(timezone=True), nullable=False)
    error = Column(Float, nullable=False)

    forecast_run = relationship("ForecastRun", backref="forecast_errors")
