"""Integration tests: summary persistence against PostgreSQL."""

from datetime import date
from decimal import Decimal

import pytest

from api.models import AnnualSummary, DailyOb, MonthlySummary, SnowSeason
from api.utils import calc_annual_summary, calc_monthly_summary
from tests.integration.conftest import make_daily_ob, make_daily_obs_for_month

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def test_calc_monthly_and_snowseason_roundtrip() -> None:
    make_daily_ob(
        date(2020, 11, 1),
        precip="0",
        snowfall="5.0",
        snowdepth="5.0",
    )
    calc_monthly_summary(2020, 11, save_to_db=True)
    assert MonthlySummary.objects.filter(date__year=2020, date__month=11).exists()
    season = SnowSeason.objects.get(season="2020-2021")
    assert season.nov == Decimal("5.0")
    assert season.total == Decimal("5.0")

    DailyOb.objects.all().delete()
    make_daily_ob(
        date(2020, 11, 1),
        precip="0",
        snowfall="2.0",
        snowdepth="2.0",
    )
    calc_monthly_summary(2020, 11, save_to_db=True)
    season.refresh_from_db()
    assert season.nov == Decimal("2.0")
    assert season.total == Decimal("2.0")
    assert MonthlySummary.objects.filter(date__year=2020, date__month=11).count() == 1


def test_calc_annual_roundtrip() -> None:
    make_daily_obs_for_month(2018, 3, days=2, precip="0.5")
    calc_annual_summary(2018, save_to_db=True)
    assert AnnualSummary.objects.filter(year=2018).count() == 1
    calc_annual_summary(2018, save_to_db=True)
    assert AnnualSummary.objects.filter(year=2018).count() == 1


def test_sf_todate_cross_year_with_db() -> None:
    make_daily_ob(date(2019, 10, 1), snowfall="2.0")
    make_daily_ob(date(2019, 11, 1), snowfall="1.0")
    make_daily_ob(date(2020, 1, 1), snowfall="4.0")
    summary = calc_monthly_summary(2020, 1, save_to_db=False)
    assert isinstance(summary, dict)
    assert summary["sf_todate"] == Decimal("7.0")
