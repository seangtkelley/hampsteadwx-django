"""Integration fixtures that require PostgreSQL."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from api.models import (
    AnnualSummary,
    DailyOb,
    MonthlySummary,
    PeakFoliage,
    SnowSeason,
    SunsetLakeIceInIceOut,
)
from tests.conftest import SAMPLE_CSV, general_summary_defaults


def make_daily_ob(
    day: date,
    *,
    max_temp: str | Decimal = "40.0",
    min_temp: str | Decimal = "20.0",
    atob_temp: str | Decimal = "30.0",
    precip: str | Decimal = "0",
    snowfall: str | Decimal = "0",
    snowdepth: str | Decimal = "0",
    csv_filepath: str = "/tmp/test.csv",
) -> DailyOb:
    """Create and return a DailyOb with the given values."""
    return DailyOb.objects.create(
        date=day,
        csv_filepath=csv_filepath,
        max_temp=Decimal(str(max_temp)),
        min_temp=Decimal(str(min_temp)),
        atob_temp=Decimal(str(atob_temp)),
        precip=Decimal(str(precip)),
        snowfall=Decimal(str(snowfall)),
        snowdepth=Decimal(str(snowdepth)),
    )


def make_daily_obs_for_month(
    year: int,
    month: int,
    days: int = 3,
    **kwargs: object,
) -> list[DailyOb]:
    """Create ``days`` consecutive DailyOb rows starting on the 1st."""
    return [
        make_daily_ob(date(year, month, 1) + timedelta(days=i), **kwargs)
        for i in range(days)
    ]


@pytest.fixture
def monthly_summary() -> MonthlySummary:
    return MonthlySummary.objects.create(
        date=date(2020, 1, 1),
        remarks="Test remarks",
        csv_filepath=str(SAMPLE_CSV),
        precip_todate=Decimal("1.000"),
        precip_todate_dfn=Decimal("0.000"),
        sf_todate=Decimal("0.000"),
        sf_todate_dfn=Decimal("0.000"),
        **general_summary_defaults(),
    )


@pytest.fixture
def annual_summary() -> AnnualSummary:
    return AnnualSummary.objects.create(
        year=2020,
        **general_summary_defaults(),
    )


@pytest.fixture
def snow_season() -> SnowSeason:
    return SnowSeason.objects.create(
        season="2019-2020",
        oct=Decimal("1.0"),
        nov=Decimal("2.0"),
        dec=Decimal("3.0"),
        jan=Decimal("4.0"),
        feb=Decimal("5.0"),
        mar=Decimal("1.0"),
        apr=Decimal("0.5"),
        may=Decimal("0.0"),
        total=Decimal("16.5"),
    )


@pytest.fixture
def peak_foliage() -> PeakFoliage:
    return PeakFoliage.objects.create(date=date(2020, 10, 15))


@pytest.fixture
def sunset_lake() -> SunsetLakeIceInIceOut:
    return SunsetLakeIceInIceOut.objects.create(
        season="2019-2020",
        icein_date=date(2019, 12, 1),
        iceout_date=date(2020, 4, 1),
        duration=122,
    )
