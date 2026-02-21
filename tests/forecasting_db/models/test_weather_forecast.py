"""Tests for WeatherForecast model."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from forecasting_db.models import WeatherForecast, WeatherSite, WeatherVariable


@pytest.fixture
def weather_site(session):
    """Create a test weather site."""
    ws = WeatherSite(
        weather_site_id="site_test_forecast",
        site_lat=40.7128,
        site_long=-74.0060,
    )
    session.add(ws)
    session.commit()
    return ws


def test_weather_forecast_crud(session, weather_site):
    """Test create, read, update, delete operations on WeatherForecast."""
    ts = datetime(2025, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
    issue_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=timezone.utc)

    wf = WeatherForecast(
        weather_site_id=weather_site.weather_site_id,
        variable=WeatherVariable.temp_air_c,
        value=12.3,
        timestamp=ts,
        issue_time=issue_time,
    )
    session.add(wf)
    session.commit()

    # Read
    db_wf = (
        session.query(WeatherForecast)
        .filter_by(weather_site_id=weather_site.weather_site_id)
        .first()
    )
    assert db_wf is not None
    assert db_wf.value == 12.3
    assert db_wf.variable == WeatherVariable.temp_air_c
    assert db_wf.issue_time == issue_time

    # Update
    db_wf.value = 13.0
    session.commit()
    assert (
        session.query(WeatherForecast)
        .filter_by(weather_site_id=weather_site.weather_site_id)
        .first()
        .value
        == 13.0
    )

    # Delete
    session.delete(db_wf)
    session.commit()
    assert (
        session.query(WeatherForecast)
        .filter_by(weather_site_id=weather_site.weather_site_id)
        .count()
        == 0
    )


def test_weather_forecast_unique_constraint(session, weather_site):
    """Verify unique constraint on (weather_site_id, variable, timestamp, issue_time)."""
    ts = datetime(2025, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
    issue_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=timezone.utc)

    wf1 = WeatherForecast(
        weather_site_id=weather_site.weather_site_id,
        variable=WeatherVariable.temp_air_c,
        value=12.3,
        timestamp=ts,
        issue_time=issue_time,
    )
    session.add(wf1)
    session.commit()

    # Try to insert duplicate (same site, variable, timestamp, and issue_time)
    wf2 = WeatherForecast(
        weather_site_id=weather_site.weather_site_id,
        variable=WeatherVariable.temp_air_c,
        value=13.0,
        timestamp=ts,
        issue_time=issue_time,
    )
    session.add(wf2)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_weather_forecast_different_issue_times_allowed(session, weather_site):
    """Verify same forecast time but different issue times are allowed."""
    ts = datetime(2025, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
    issue_time1 = datetime(2025, 1, 1, 18, 0, 0, tzinfo=timezone.utc)
    issue_time2 = datetime(2025, 1, 2, 6, 0, 0, tzinfo=timezone.utc)

    wf1 = WeatherForecast(
        weather_site_id=weather_site.weather_site_id,
        variable=WeatherVariable.temp_air_c,
        value=12.3,
        timestamp=ts,
        issue_time=issue_time1,
    )
    wf2 = WeatherForecast(
        weather_site_id=weather_site.weather_site_id,
        variable=WeatherVariable.temp_air_c,
        value=12.5,
        timestamp=ts,
        issue_time=issue_time2,
    )
    session.add(wf1)
    session.add(wf2)
    session.commit()

    count = (
        session.query(WeatherForecast)
        .filter_by(
            weather_site_id=weather_site.weather_site_id,
            variable=WeatherVariable.temp_air_c,
            timestamp=ts,
        )
        .count()
    )
    assert count == 2


def test_weather_forecast_different_variables_allowed(session, weather_site):
    """Verify different variables at same site, timestamp, and issue_time are allowed."""
    ts = datetime(2025, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
    issue_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=timezone.utc)

    wf_temp = WeatherForecast(
        weather_site_id=weather_site.weather_site_id,
        variable=WeatherVariable.temp_air_c,
        value=12.3,
        timestamp=ts,
        issue_time=issue_time,
    )
    wf_wind = WeatherForecast(
        weather_site_id=weather_site.weather_site_id,
        variable=WeatherVariable.wind_speed_ms,
        value=2.8,
        timestamp=ts,
        issue_time=issue_time,
    )
    session.add(wf_temp)
    session.add(wf_wind)
    session.commit()

    count = (
        session.query(WeatherForecast)
        .filter_by(
            weather_site_id=weather_site.weather_site_id,
            timestamp=ts,
            issue_time=issue_time,
        )
        .count()
    )
    assert count == 2


def test_weather_forecast_weather_site_relationship(session, weather_site):
    """Verify relationship between WeatherForecast and WeatherSite."""
    ts = datetime(2025, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
    issue_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=timezone.utc)

    wf = WeatherForecast(
        weather_site_id=weather_site.weather_site_id,
        variable=WeatherVariable.ghi_wm2,
        value=600.0,
        timestamp=ts,
        issue_time=issue_time,
    )
    session.add(wf)
    session.commit()

    db_wf = session.query(WeatherForecast).first()
    assert db_wf.weather_site is not None
    assert db_wf.weather_site.weather_site_id == weather_site.weather_site_id
    assert db_wf.weather_site.site_lat == pytest.approx(40.7128)


def test_weather_forecast_weather_site_backref(session, weather_site):
    """Verify backref on WeatherSite for weather_forecasts."""
    ts1 = datetime(2025, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
    ts2 = datetime(2025, 1, 2, 13, 0, 0, tzinfo=timezone.utc)
    issue_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=timezone.utc)

    wf1 = WeatherForecast(
        weather_site_id=weather_site.weather_site_id,
        variable=WeatherVariable.temp_air_c,
        value=12.3,
        timestamp=ts1,
        issue_time=issue_time,
    )
    wf2 = WeatherForecast(
        weather_site_id=weather_site.weather_site_id,
        variable=WeatherVariable.wind_speed_ms,
        value=2.8,
        timestamp=ts2,
        issue_time=issue_time,
    )
    session.add(wf1)
    session.add(wf2)
    session.commit()

    ws = (
        session.query(WeatherSite)
        .filter_by(weather_site_id=weather_site.weather_site_id)
        .first()
    )
    assert len(ws.weather_forecasts) == 2


def test_weather_forecast_fk_enforced(session):
    """Verify foreign key constraint is enforced."""
    wf = WeatherForecast(
        weather_site_id="nonexistent_site",
        variable=WeatherVariable.temp_air_c,
        value=12.3,
        timestamp=datetime(2025, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
        issue_time=datetime(2025, 1, 1, 18, 0, 0, tzinfo=timezone.utc),
    )
    session.add(wf)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_weather_forecast_all_variables(session, weather_site):
    """Test WeatherForecast with all weather variables."""
    ts = datetime(2025, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
    issue_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=timezone.utc)

    variables = [
        (WeatherVariable.ghi_wm2, 650.0),
        (WeatherVariable.temp_air_c, 12.3),
        (WeatherVariable.wind_speed_ms, 2.8),
    ]

    for var, value in variables:
        wf = WeatherForecast(
            weather_site_id=weather_site.weather_site_id,
            variable=var,
            value=value,
            timestamp=ts,
            issue_time=issue_time,
        )
        session.add(wf)

    session.commit()

    # Verify all were inserted
    count = (
        session.query(WeatherForecast)
        .filter_by(weather_site_id=weather_site.weather_site_id)
        .count()
    )
    assert count == 3


def test_weather_forecast_issue_time_before_target_time(session, weather_site):
    """Test forecast where issue_time is before forecast timestamp (typical scenario)."""
    issue_time = datetime(2025, 1, 1, 18, 0, 0, tzinfo=timezone.utc)
    target_time = issue_time + timedelta(hours=18)  # 18-hour ahead forecast

    wf = WeatherForecast(
        weather_site_id=weather_site.weather_site_id,
        variable=WeatherVariable.temp_air_c,
        value=12.3,
        timestamp=target_time,
        issue_time=issue_time,
    )
    session.add(wf)
    session.commit()

    db_wf = session.query(WeatherForecast).first()
    assert db_wf.issue_time < db_wf.timestamp
    assert (db_wf.timestamp - db_wf.issue_time).total_seconds() == 18 * 3600
