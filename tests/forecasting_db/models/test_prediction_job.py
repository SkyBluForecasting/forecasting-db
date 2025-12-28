from datetime import datetime

from forecasting_db.models import Asset, PredictionJob


def test_prediction_job_crud(session):
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
