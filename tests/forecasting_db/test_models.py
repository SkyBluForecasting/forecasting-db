import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from forecasting_db.models import (
    Base,
    Constraints,
    ForecastRuns,
    Forecasts,
    Measurements,
)


# Use the engine fixture from conftest.py
@pytest.fixture
def session(engine):
    """Provide a fresh SQLAlchemy session with tables created from models."""
    Base.metadata.create_all(engine)  # create all tables
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.rollback()
    s.close()
    Base.metadata.drop_all(engine)  # clean up after test


# -------------------- Forecasts --------------------
def test_forecasts_crud(session):
    f = Forecasts(
        asset_uuid="asset1",
        timestamp="2025-01-01T00:00:00",
        forecast_uuid="11111111-1111-1111-1111-111111111111",
        forecast_kw=100.0,
    )
    session.add(f)
    session.commit()

    # Read
    db_f = session.query(Forecasts).filter_by(asset_uuid="asset1").first()
    assert db_f.forecast_kw == 100.0

    # Update
    db_f.forecast_kw = 150.0
    session.commit()
    assert (
        session.query(Forecasts).filter_by(asset_uuid="asset1").first().forecast_kw
        == 150.0
    )

    # Delete
    session.delete(db_f)
    session.commit()
    assert session.query(Forecasts).filter_by(asset_uuid="asset1").first() is None


def test_forecasts_unique_constraint(session):
    f1 = Forecasts(
        asset_uuid="asset1",
        timestamp="2025-01-01T00:00:00",
        forecast_uuid="22222222-2222-2222-2222-222222222222",
        forecast_kw=100.0,
    )
    f2 = Forecasts(
        asset_uuid="asset2",
        timestamp="2025-01-01T01:00:00",
        forecast_uuid="22222222-2222-2222-2222-222222222222",  # duplicate UUID
        forecast_kw=200.0,
    )
    session.add(f1)
    session.commit()
    with pytest.raises(IntegrityError):
        session.add(f2)
        session.commit()


# -------------------- ForecastRuns --------------------
def test_forecast_runs_crud(session):
    # First insert a Forecast (to satisfy FK)
    f = Forecasts(
        asset_uuid="asset1",
        timestamp="2025-01-01T00:00:00",
        forecast_uuid="33333333-3333-3333-3333-333333333333",
        forecast_kw=100.0,
    )
    session.add(f)
    session.commit()
    f_run = ForecastRuns(
        forecast_uuid="33333333-3333-3333-3333-333333333333",
        run_uuid="run1",
        asset_uuid="asset1",
        created_at="2025-01-01T00:00:00",
        start_time="2025-01-01T01:00:00",
        end_time="2025-01-01T02:00:00",
        frequency_min=60.0,
    )
    session.add(f_run)
    session.commit()

    db_run = (
        session.query(ForecastRuns)
        .filter_by(forecast_uuid="33333333-3333-3333-3333-333333333333")
        .first()
    )
    assert db_run.asset_uuid == "asset1"

    db_run.frequency_min = 30.0
    session.commit()
    assert (
        session.query(ForecastRuns)
        .filter_by(forecast_uuid="33333333-3333-3333-3333-333333333333")
        .first()
        .frequency_min
        == 30.0
    )

    session.delete(db_run)
    session.commit()
    assert (
        session.query(ForecastRuns)
        .filter_by(forecast_uuid="33333333-3333-3333-3333-333333333333")
        .first()
        is None
    )


# -------------------- Constraints --------------------
def test_constraints_crud(session):
    c = Constraints(
        asset_uuid="asset1",
        timestamp="2025-01-01T00:00:00",
        forecast_uuid="44444444-4444-4444-4444-444444444444",
        constraint_kw=50.0,
    )
    session.add(c)
    session.commit()

    db_c = session.query(Constraints).filter_by(asset_uuid="asset1").first()
    assert db_c.constraint_kw == 50.0

    db_c.constraint_kw = 75.0
    session.commit()
    assert (
        session.query(Constraints).filter_by(asset_uuid="asset1").first().constraint_kw
        == 75.0
    )

    session.delete(db_c)
    session.commit()
    assert session.query(Constraints).filter_by(asset_uuid="asset1").first() is None


# -------------------- Measurements --------------------
def test_measurements_crud(session):
    m = Measurements(
        asset_uuid="asset1",
        timestamp="2025-01-01T00:00:00",
        metric="voltage",
        value=120.0,
    )
    session.add(m)
    session.commit()

    db_m = session.query(Measurements).filter_by(asset_uuid="asset1").first()
    assert db_m.value == 120.0

    db_m.value = 130.0
    session.commit()
    assert (
        session.query(Measurements).filter_by(asset_uuid="asset1").first().value
        == 130.0
    )

    session.delete(db_m)
    session.commit()
    assert session.query(Measurements).filter_by(asset_uuid="asset1").first() is None
