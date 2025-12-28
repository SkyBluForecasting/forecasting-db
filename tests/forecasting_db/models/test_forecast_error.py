from datetime import datetime

from forecasting_db.models import (
    Asset,
    ForecastError,
    ForecastRun,
    PredictionJob,
)


def test_forecast_error_crud(session):
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

    fe = ForecastError(
        forecast_run_id="run1",
        timestamp=datetime(2025, 1, 1, 0, 0),
        error=5.5,
    )
    session.add(fe)
    session.commit()

    db_fe = session.query(ForecastError).first()
    assert db_fe.error == 5.5
    assert db_fe.forecast_run.forecast_run_id == "run1"

    db_fe.error = 2.2
    session.commit()
    assert session.query(ForecastError).first().error == 2.2

    session.delete(db_fe)
    session.delete(fr)
    session.delete(pj)
    session.delete(asset)
    session.commit()
    assert session.query(ForecastError).count() == 0
