import pytest
from sqlalchemy.exc import IntegrityError

from forecasting_db.models import Asset, WeatherSite


@pytest.fixture
def weather_site(session):
    ws = WeatherSite(
        weather_site_id="site_43.6532_-79.3832",
        site_lat=43.6532,
        site_long=-79.3832,
    )
    session.add(ws)
    session.commit()
    return ws


def test_weather_site_can_be_created_and_queried(session, weather_site):
    ws = (
        session.query(WeatherSite)
        .filter_by(weather_site_id="site_43.6532_-79.3832")
        .first()
    )

    assert ws is not None
    assert ws.site_lat == pytest.approx(43.6532)
    assert ws.site_long == pytest.approx(-79.3832)


def test_weather_site_lat_long_unique_constraint(session, weather_site):
    dup = WeatherSite(
        weather_site_id="site_duplicate_id",
        site_lat=43.6532,
        site_long=-79.3832,
    )
    session.add(dup)

    with pytest.raises(IntegrityError):
        session.flush()  # force constraint check
    session.rollback()


def test_asset_can_reference_weather_site_via_fk_and_relationship(
    session, weather_site
):
    pv = Asset(
        asset_uuid="pv1",
        asset_type="pv",
        name="PV 1",
        capacity_kw=1200,
        parent_uuid=None,
        depth=0,
        measured=False,
        latitude=43.6532,
        longitude=-79.3832,
        weather_site_id=weather_site.weather_site_id,
    )
    session.add(pv)
    session.commit()

    db_pv = session.query(Asset).filter_by(asset_uuid="pv1").first()
    assert db_pv.weather_site_id == "site_43.6532_-79.3832"
    assert db_pv.weather_site is not None
    assert db_pv.weather_site.weather_site_id == "site_43.6532_-79.3832"


def test_weather_site_assets_backref_works(session, weather_site):
    pv = Asset(
        asset_uuid="pv_backref",
        asset_type="pv",
        name="PV Backref",
        capacity_kw=500,
        parent_uuid=None,
        depth=0,
        measured=False,
        latitude=43.6532,
        longitude=-79.3832,
        weather_site_id=weather_site.weather_site_id,
    )
    session.add(pv)
    session.commit()

    ws = (
        session.query(WeatherSite)
        .filter_by(weather_site_id=weather_site.weather_site_id)
        .first()
    )

    assert {a.asset_uuid for a in ws.assets} == {"pv_backref"}


def test_asset_fk_enforced_weather_site_must_exist(session):
    pv = Asset(
        asset_uuid="pv_invalid_fk",
        asset_type="pv",
        name="PV Invalid FK",
        capacity_kw=500,
        parent_uuid=None,
        depth=0,
        measured=False,
        latitude=1.0,
        longitude=2.0,
        weather_site_id="does_not_exist",
    )
    session.add(pv)

    with pytest.raises(IntegrityError):
        session.flush()  # force FK check
    session.rollback()


def test_asset_weather_site_id_can_be_cleared(session, weather_site):
    pv = Asset(
        asset_uuid="pv_clear_site",
        asset_type="pv",
        name="PV Clear Site",
        capacity_kw=500,
        parent_uuid=None,
        depth=0,
        measured=False,
        latitude=43.6532,
        longitude=-79.3832,
        weather_site_id=weather_site.weather_site_id,
    )
    session.add(pv)
    session.commit()

    db_pv = session.query(Asset).filter_by(asset_uuid="pv_clear_site").first()
    db_pv.weather_site_id = None
    session.commit()

    updated = session.query(Asset).filter_by(asset_uuid="pv_clear_site").first()
    assert updated.weather_site_id is None
    assert updated.weather_site is None
