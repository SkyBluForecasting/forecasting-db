from alembic import command
from sqlalchemy import text


def enum_labels(engine, schema: str, enum_name: str) -> list[str]:
    """Return ordered labels for a Postgres enum type, e.g. public.asset_type_enum."""
    sql = text(
        """
        SELECT e.enumlabel
        FROM pg_type t
        JOIN pg_enum e ON t.oid = e.enumtypid
        JOIN pg_namespace n ON n.oid = t.typnamespace
        WHERE n.nspname = :schema
          AND t.typname = :enum_name
        ORDER BY e.enumsortorder
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(sql, {"schema": schema, "enum_name": enum_name}).fetchall()
    return [r[0] for r in rows]


def test_rev8_adds_region_to_asset_type_enum_on_upgrade(alembic_cfg, upgraded_engine):
    """
    Upgrade to rev8.

      - public.asset_type_enum exists
      - enum labels include 'region'
      - enum still includes the previously supported labels (at least system, distribution_substation, pv)
    """
    command.upgrade(alembic_cfg, "rev8")

    labels = enum_labels(upgraded_engine, "public", "asset_type_enum")
    assert labels, "Expected public.asset_type_enum to exist and have labels"

    assert "region" in labels
    assert "system" in labels
    assert "distribution_substation" in labels
    assert "pv" in labels


def test_rev8_downgrade_is_noop(alembic_cfg, upgraded_engine):
    command.upgrade(alembic_cfg, "rev8")
    command.downgrade(alembic_cfg, "rev7")

    # value may still exist because downgrade is noop; this is expected
    labels = enum_labels(upgraded_engine, "public", "asset_type_enum")
    assert "region" in labels
