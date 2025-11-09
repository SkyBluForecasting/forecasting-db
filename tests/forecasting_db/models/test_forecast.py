from datetime import datetime

from forecasting_db.models import (
    Asset,
    Forecast,
    ForecastRun,
    PredictionJob,
)


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
