from datetime import datetime

from forecasting_db.models import (
    Asset,
    Constraint,
    ForecastRun,
    PredictionJob,
)


def test_constraint_crud(session):
    asset = Asset(
        asset_uuid="asset1",
        asset_type="distribution_substation",
        name="Asset 1",
        depth=0,
    )
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
