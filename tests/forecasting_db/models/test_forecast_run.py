from datetime import datetime

from forecasting_db.models import (
    Asset,
    ForecastRun,
    PredictionJob,
)


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
