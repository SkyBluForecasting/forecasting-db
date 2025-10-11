from datetime import datetime

import pytest
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from forecasting_db.models import (
    Asset,
    Base,
    Constraint,
    Forecast,
    ForecastRun,
    Measurement,
    PredictionJob,
)


@pytest.fixture
def session(engine):
    """Provide a fresh SQLAlchemy session with tables created from models."""
    # Create schemas before creating tables
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS openstef"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS product"))

    Base.metadata.create_all(engine)  # create all tables
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.rollback()
    s.close()
    Base.metadata.drop_all(engine)  # clean up after test


# -------------------- Asset --------------------
def test_asset_crud(session):
    parent = Asset(
        asset_uuid="sub1",
        asset_type="substation",
        name="Substation 1",
        capacity_kw=80000,
    )
    session.add(parent)
    session.commit()

    child = Asset(
        asset_uuid="pv1",
        asset_type="pv",
        name="PV 1",
        capacity_kw=5000,
        parent_uuid="sub1",
    )
    session.add(child)
    session.commit()

    db_parent = session.query(Asset).filter_by(asset_uuid="sub1").first()
    assert db_parent.children[0].asset_uuid == "pv1"

    db_child = session.query(Asset).filter_by(asset_uuid="pv1").first()
    assert db_child.parent.asset_uuid == "sub1"

    db_child.capacity_kw = 6000
    session.commit()
    assert session.query(Asset).filter_by(asset_uuid="pv1").first().capacity_kw == 6000

    session.delete(db_child)
    session.delete(db_parent)
    session.commit()
    assert session.query(Asset).count() == 0


# -------------------- PredictionJob --------------------
def test_prediction_job_crud(session):
    asset = Asset(asset_uuid="asset1", asset_type="solar", name="Asset 1")
    session.add(asset)
    session.commit()

    pj = PredictionJob(
        asset_uuid="asset1",
        model="ARIMA",
        horizon_minutes=60,
        frequency_minutes=15,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        config={},
    )
    session.add(pj)
    session.commit()

    db_pj = session.query(PredictionJob).filter_by(asset_uuid="asset1").first()
    assert db_pj.model == "ARIMA"

    db_pj.model = "LSTM"
    session.commit()
    assert (
        session.query(PredictionJob).filter_by(asset_uuid="asset1").first().model
        == "LSTM"
    )

    session.delete(db_pj)
    session.delete(asset)
    session.commit()
    assert session.query(PredictionJob).count() == 0


# -------------------- ForecastRun --------------------
def test_forecast_run_crud(session):
    asset = Asset(asset_uuid="asset1", asset_type="solar", name="Asset 1")
    session.add(asset)
    session.commit()

    pj = PredictionJob(
        asset_uuid="asset1",
        model="ARIMA",
        horizon_minutes=60,
        frequency_minutes=15,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        config={},
    )
    session.add(pj)
    session.commit()

    fr = ForecastRun(
        forecast_run_id="run1",
        prediction_job_id=pj.id,
        model_run_id="mlflow123",
        asset_uuid="asset1",
        start_time=datetime(2025, 1, 1),
        end_time=datetime(2025, 1, 2),
        frequency_min=60,
    )
    session.add(fr)
    session.commit()

    db_fr = session.query(ForecastRun).filter_by(forecast_run_id="run1").first()
    assert db_fr.model_run_id == "mlflow123"

    db_fr.frequency_min = 30
    session.commit()
    assert (
        session.query(ForecastRun)
        .filter_by(forecast_run_id="run1")
        .first()
        .frequency_min
        == 30
    )

    session.delete(db_fr)
    session.delete(pj)
    session.delete(asset)
    session.commit()
    assert session.query(ForecastRun).count() == 0


# -------------------- Forecast --------------------
def test_forecast_crud(session):
    asset = Asset(asset_uuid="asset1", asset_type="solar", name="Asset 1")
    session.add(asset)
    session.commit()

    pj = PredictionJob(
        asset_uuid="asset1",
        model="ARIMA",
        horizon_minutes=60,
        frequency_minutes=15,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        config={},
    )
    session.add(pj)
    session.commit()

    fr = ForecastRun(
        forecast_run_id="run1",
        prediction_job_id=pj.id,
        model_run_id="mlflow123",
        asset_uuid="asset1",
        start_time=datetime(2025, 1, 1),
        end_time=datetime(2025, 1, 2),
        frequency_min=60,
    )
    session.add(fr)
    session.commit()

    f = Forecast(
        forecast_run_id="run1",
        timestamp=datetime(2025, 1, 1, 0, 0),
        forecast_value=100.0,
        lower_q=90.0,
        upper_q=110.0,
    )
    session.add(f)
    session.commit()

    db_f = session.query(Forecast).first()
    assert db_f.forecast_value == 100.0

    db_f.forecast_value = 120.0
    session.commit()
    assert session.query(Forecast).first().forecast_value == 120.0

    session.delete(db_f)
    session.delete(fr)
    session.delete(pj)
    session.delete(asset)
    session.commit()
    assert session.query(Forecast).count() == 0


# -------------------- Measurement --------------------
def test_measurement_crud(session):
    asset = Asset(asset_uuid="asset1", asset_type="solar", name="Asset 1")
    session.add(asset)
    session.commit()

    m = Measurement(
        asset_uuid="asset1",
        timestamp=datetime(2025, 1, 1),
        metric="voltage",
        value=120.0,
    )
    session.add(m)
    session.commit()

    db_m = session.query(Measurement).filter_by(asset_uuid="asset1").first()
    assert db_m.value == 120.0

    db_m.value = 130.0
    session.commit()
    assert (
        session.query(Measurement).filter_by(asset_uuid="asset1").first().value == 130.0
    )

    session.delete(db_m)
    session.delete(asset)
    session.commit()

    assert session.query(Measurement).filter_by(asset_uuid="asset1").count() == 0
    assert session.query(Asset).filter_by(asset_uuid="asset1").count() == 0


# -------------------- Constraint --------------------
def test_constraint_crud(session):
    asset = Asset(asset_uuid="asset1", asset_type="solar", name="Asset 1")
    session.add(asset)
    session.commit()

    pj = PredictionJob(
        asset_uuid="asset1",
        model="ARIMA",
        horizon_minutes=60,
        frequency_minutes=15,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        config={},
    )
    session.add(pj)
    session.commit()

    fr = ForecastRun(
        forecast_run_id="run1",
        prediction_job_id=pj.id,
        model_run_id="mlflow123",
        asset_uuid="asset1",
        start_time=datetime(2025, 1, 1),
        end_time=datetime(2025, 1, 2),
        frequency_min=60,
    )
    session.add(fr)
    session.commit()

    c = Constraint(
        asset_uuid="asset1",
        timestamp=datetime(2025, 1, 1, 0, 0),
        forecast_run_id="run1",
        constraint_kw=50.0,
    )
    session.add(c)
    session.commit()

    db_c = session.query(Constraint).first()
    assert db_c.constraint_kw == 50.0

    db_c.constraint_kw = 75.0
    session.commit()
    assert session.query(Constraint).first().constraint_kw == 75.0

    session.delete(db_c)
    session.delete(fr)
    session.delete(pj)
    session.delete(asset)
    session.commit()
    assert session.query(Constraint).count() == 0
