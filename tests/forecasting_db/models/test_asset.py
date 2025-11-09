from forecasting_db.models import Asset


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
