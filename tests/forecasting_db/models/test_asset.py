import pytest

from forecasting_db.models import Asset


@pytest.fixture
def asset_tree(session):
    """
    Create the following assets.

      system1 (system)
        └── substation1 (distribution_substation)
              └── pv1 (pv)
    """
    parent = Asset(
        asset_uuid="system1",
        asset_type="system",
        name="System 1",
        capacity_kw=80000,
        depth=0,
        measured=True,
    )
    substation = Asset(
        asset_uuid="substation1",
        asset_type="distribution_substation",
        name="Substation 1",
        capacity_kw=5000,
        parent_uuid="system1",
        depth=1,
        measured=False,
    )
    pv = Asset(
        asset_uuid="pv1",
        asset_type="pv",
        name="PV 1",
        capacity_kw=1200,
        parent_uuid="substation1",
        depth=2,
        measured=False,
        latitude=43.6532,
        longitude=-79.3832,
        weather_site_id="site_43.6532_-79.3832",
    )

    session.add_all([parent, substation, pv])
    session.commit()
    return {"parent": parent, "substation": substation, "pv": pv}


def test_asset_hierarchy_relationships(session, asset_tree):
    db_system = session.query(Asset).filter_by(asset_uuid="system1").first()
    assert {c.asset_uuid for c in db_system.children} == {"substation1"}

    db_substation = session.query(Asset).filter_by(asset_uuid="substation1").first()
    assert db_substation.parent.asset_uuid == "system1"
    assert {c.asset_uuid for c in db_substation.children} == {"pv1"}

    db_pv = session.query(Asset).filter_by(asset_uuid="pv1").first()
    assert db_pv.parent.asset_uuid == "substation1"


def test_pv_asset_can_store_location_and_weather_site(session, asset_tree):
    db_pv = session.query(Asset).filter_by(asset_uuid="pv1").first()

    assert db_pv.asset_type == "pv"
    assert db_pv.latitude == pytest.approx(43.6532)
    assert db_pv.longitude == pytest.approx(-79.3832)
    assert db_pv.weather_site_id == "site_43.6532_-79.3832"


def test_location_is_optional(session):
    pv = Asset(
        asset_uuid="pv_no_location",
        asset_type="pv",
        name="PV No Location",
        capacity_kw=500,
        parent_uuid=None,
        depth=0,
        measured=False,
        latitude=None,
        longitude=None,
        weather_site_id=None,
    )
    session.add(pv)
    session.commit()

    db_pv = session.query(Asset).filter_by(asset_uuid="pv_no_location").first()
    assert db_pv.latitude is None
    assert db_pv.longitude is None
    assert db_pv.weather_site_id is None


def test_pv_asset_weather_site_id_can_be_updated(session, asset_tree):
    db_pv = session.query(Asset).filter_by(asset_uuid="pv1").first()
    db_pv.weather_site_id = "site_updated"
    session.commit()

    updated = session.query(Asset).filter_by(asset_uuid="pv1").first()
    assert updated.weather_site_id == "site_updated"


def test_assets_can_be_deleted(session, asset_tree):
    # Delete leaf-to-root for clarity
    pv = session.query(Asset).filter_by(asset_uuid="pv1").first()
    substation = session.query(Asset).filter_by(asset_uuid="substation1").first()
    system = session.query(Asset).filter_by(asset_uuid="system1").first()

    session.delete(pv)
    session.delete(substation)
    session.delete(system)
    session.commit()

    assert session.query(Asset).count() == 0
