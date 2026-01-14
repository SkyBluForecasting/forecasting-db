from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from forecasting_db.models import (
    Asset,
    Measurement,
)


def test_measurement_crud(session):
    asset = Asset(
        asset_uuid="asset1",
        asset_type="distribution_substation",
        name="Asset 1",
        depth=0,
    )
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


def test_measurement_unique_constraint(session):
    asset = Asset(
        asset_uuid="asset1",
        asset_type="distribution_substation",
        name="Asset 1",
        depth=0,
    )
    session.add(asset)
    session.commit()

    ts = datetime(2025, 1, 1, tzinfo=timezone.utc)

    session.add(
        Measurement(asset_uuid="asset1", timestamp=ts, metric="voltage", value=120.0)
    )
    session.commit()

    # Same (asset_uuid, timestamp, metric) should violate uq_measurement_asset_ts_metric
    session.add(
        Measurement(asset_uuid="asset1", timestamp=ts, metric="voltage", value=130.0)
    )
    with pytest.raises(IntegrityError):
        session.commit()
