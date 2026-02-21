"""Tests for WeatherActual model."""

from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from forecasting_db.models import WeatherActual, WeatherSite, WeatherVariable


@pytest.fixture
def weather_site(session):
    """Create a test weather site."""
    ws = WeatherSite(
        weather_site_id="site_test_actual",
        site_lat=43.6532,
        site_long=-79.3832,
    )
    session.add(ws)
    session.commit()
    return ws


def test_weather_variable_enum_values():
    """Verify WeatherVariable enum has all expected values."""
    assert WeatherVariable.ghi_wm2.value == "ghi_wm2"
    assert WeatherVariable.temp_air_c.value == "temp_air_c"
    assert WeatherVariable.wind_speed_ms.value == "wind_speed_ms"


def test_weather_variable_enum_members():
    """Verify all expected members exist in enum."""
    members = [member.name for member in WeatherVariable]
    assert "ghi_wm2" in members
    assert "temp_air_c" in members
    assert "wind_speed_ms" in members


def test_weather_variable_enum_is_string_enum():
    """Verify WeatherVariable is a string-based enum."""
    var = WeatherVariable.ghi_wm2
    assert isinstance(var, str)
    assert isinstance(var, WeatherVariable)


def test_weather_variable_enum_string_comparison():
    """Verify enum values can be compared with strings."""
    assert WeatherVariable.ghi_wm2 == "ghi_wm2"
    assert WeatherVariable.temp_air_c == "temp_air_c"
    assert WeatherVariable.wind_speed_ms == "wind_speed_ms"


def test_weather_variable_enum_from_string():
    """Verify enum can be instantiated from string values."""
    var1 = WeatherVariable("ghi_wm2")
    var2 = WeatherVariable("temp_air_c")
    var3 = WeatherVariable("wind_speed_ms")

    assert var1 == WeatherVariable.ghi_wm2
    assert var2 == WeatherVariable.temp_air_c
    assert var3 == WeatherVariable.wind_speed_ms


def test_weather_actual_crud(session, weather_site):
    """Test create, read, update, delete operations on WeatherActual."""
    ts = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    wa = WeatherActual(
        weather_site_id=weather_site.weather_site_id,
        variable=WeatherVariable.temp_air_c,
        value=15.5,
        timestamp=ts,
    )
    session.add(wa)
    session.commit()

    # Read
    db_wa = (
        session.query(WeatherActual)
        .filter_by(weather_site_id=weather_site.weather_site_id)
        .first()
    )
    assert db_wa is not None
    assert db_wa.value == 15.5
    assert db_wa.variable == WeatherVariable.temp_air_c

    # Update
    db_wa.value = 16.0
    session.commit()
    assert (
        session.query(WeatherActual)
        .filter_by(weather_site_id=weather_site.weather_site_id)
        .first()
        .value
        == 16.0
    )

    # Delete
    session.delete(db_wa)
    session.commit()
    assert (
        session.query(WeatherActual)
        .filter_by(weather_site_id=weather_site.weather_site_id)
        .count()
        == 0
    )


def test_weather_actual_unique_constraint(session, weather_site):
    """Verify unique constraint on (weather_site_id, variable, timestamp)."""
    ts = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    wa1 = WeatherActual(
        weather_site_id=weather_site.weather_site_id,
        variable=WeatherVariable.temp_air_c,
        value=15.5,
        timestamp=ts,
    )
    session.add(wa1)
    session.commit()

    # Try to insert duplicate (same site, same variable, same timestamp)
    wa2 = WeatherActual(
        weather_site_id=weather_site.weather_site_id,
        variable=WeatherVariable.temp_air_c,
        value=16.0,
        timestamp=ts,
    )
    session.add(wa2)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_weather_actual_different_variables_allowed(session, weather_site):
    """Verify different variables at same site and timestamp are allowed."""
    ts = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    wa_temp = WeatherActual(
        weather_site_id=weather_site.weather_site_id,
        variable=WeatherVariable.temp_air_c,
        value=15.5,
        timestamp=ts,
    )
    wa_wind = WeatherActual(
        weather_site_id=weather_site.weather_site_id,
        variable=WeatherVariable.wind_speed_ms,
        value=3.2,
        timestamp=ts,
    )
    session.add(wa_temp)
    session.add(wa_wind)
    session.commit()

    count = (
        session.query(WeatherActual)
        .filter_by(weather_site_id=weather_site.weather_site_id, timestamp=ts)
        .count()
    )
    assert count == 2


def test_weather_actual_different_timestamps_allowed(session, weather_site):
    """Verify same variable at same site but different timestamps are allowed."""
    ts1 = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    ts2 = datetime(2025, 1, 1, 13, 0, 0, tzinfo=timezone.utc)

    wa1 = WeatherActual(
        weather_site_id=weather_site.weather_site_id,
        variable=WeatherVariable.temp_air_c,
        value=15.5,
        timestamp=ts1,
    )
    wa2 = WeatherActual(
        weather_site_id=weather_site.weather_site_id,
        variable=WeatherVariable.temp_air_c,
        value=16.0,
        timestamp=ts2,
    )
    session.add(wa1)
    session.add(wa2)
    session.commit()

    count = (
        session.query(WeatherActual)
        .filter_by(
            weather_site_id=weather_site.weather_site_id,
            variable=WeatherVariable.temp_air_c,
        )
        .count()
    )
    assert count == 2


def test_weather_actual_weather_site_relationship(session, weather_site):
    """Verify relationship between WeatherActual and WeatherSite."""
    ts = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    wa = WeatherActual(
        weather_site_id=weather_site.weather_site_id,
        variable=WeatherVariable.ghi_wm2,
        value=500.0,
        timestamp=ts,
    )
    session.add(wa)
    session.commit()

    db_wa = session.query(WeatherActual).first()
    assert db_wa.weather_site is not None
    assert db_wa.weather_site.weather_site_id == weather_site.weather_site_id
    assert db_wa.weather_site.site_lat == pytest.approx(43.6532)


def test_weather_actual_weather_site_backref(session, weather_site):
    """Verify backref on WeatherSite for weather_actuals."""
    ts1 = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    ts2 = datetime(2025, 1, 1, 13, 0, 0, tzinfo=timezone.utc)

    wa1 = WeatherActual(
        weather_site_id=weather_site.weather_site_id,
        variable=WeatherVariable.temp_air_c,
        value=15.5,
        timestamp=ts1,
    )
    wa2 = WeatherActual(
        weather_site_id=weather_site.weather_site_id,
        variable=WeatherVariable.wind_speed_ms,
        value=3.2,
        timestamp=ts2,
    )
    session.add(wa1)
    session.add(wa2)
    session.commit()

    ws = (
        session.query(WeatherSite)
        .filter_by(weather_site_id=weather_site.weather_site_id)
        .first()
    )
    assert len(ws.weather_actuals) == 2


def test_weather_actual_fk_enforced(session):
    """Verify foreign key constraint is enforced."""
    wa = WeatherActual(
        weather_site_id="nonexistent_site",
        variable=WeatherVariable.temp_air_c,
        value=15.5,
        timestamp=datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )
    session.add(wa)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_weather_actual_all_variables(session, weather_site):
    """Test WeatherActual with all weather variables."""
    ts = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    variables = [
        (WeatherVariable.ghi_wm2, 750.0),
        (WeatherVariable.temp_air_c, 15.5),
        (WeatherVariable.wind_speed_ms, 3.2),
    ]

    for var, value in variables:
        wa = WeatherActual(
            weather_site_id=weather_site.weather_site_id,
            variable=var,
            value=value,
            timestamp=ts,
        )
        session.add(wa)

    session.commit()

    # Verify all were inserted
    count = (
        session.query(WeatherActual)
        .filter_by(weather_site_id=weather_site.weather_site_id)
        .count()
    )
    assert count == 3
