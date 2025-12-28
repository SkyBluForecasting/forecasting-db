from forecasting_db.models import Asset


def test_asset_crud(session):
    parent = Asset(
        asset_uuid="system1",
        asset_type="system",
        name="System 1",
        capacity_kw=80000,
        depth=0,
    )
    session.add(parent)
    session.commit()

    child = Asset(
        asset_uuid="substation1",
        asset_type="distribution_substation",
        name="Substation 1",
        capacity_kw=5000,
        parent_uuid="system1",
        depth=1,
    )
    session.add(child)
    session.commit()

    db_parent = session.query(Asset).filter_by(asset_uuid="system1").first()
    assert db_parent.children[0].asset_uuid == "substation1"

    db_child = session.query(Asset).filter_by(asset_uuid="substation1").first()
    assert db_child.parent.asset_uuid == "system1"

    db_child.capacity_kw = 6000
    session.commit()
    assert (
        session.query(Asset).filter_by(asset_uuid="substation1").first().capacity_kw
        == 6000
    )

    session.delete(db_child)
    session.delete(db_parent)
    session.commit()
    assert session.query(Asset).count() == 0
