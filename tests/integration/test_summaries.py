"""Integration tests: summary persistence against PostgreSQL."""

from datetime import date
from decimal import Decimal

import pytest

from api.models import AnnualSummary, DailyOb, MonthlySummary, SnowSeason
from api.utils import (
    calc_annual_summary,
    calc_monthly_summary,
    recalc_dependent_monthly_summaries,
)
from boilerplate.settings import TRACE_VAL
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


def test_snowseason_trace_total_persists_with_db_roundtrip() -> None:
    """Trace-only snowfall months persist as TRACE, not rounded to 0.0."""
    make_daily_ob(date(2024, 10, 28), snowfall=TRACE_VAL, snowdepth=TRACE_VAL)
    calc_monthly_summary(2024, 10, save_to_db=True)

    make_daily_ob(date(2024, 11, 23), snowfall=TRACE_VAL, snowdepth=TRACE_VAL)
    calc_monthly_summary(2024, 11, save_to_db=True)

    season = SnowSeason.objects.get(season="2024-2025")
    assert season.oct == TRACE_VAL
    assert season.nov == TRACE_VAL
    assert season.total == TRACE_VAL


def test_recalc_dependent_refreshes_later_month_precip_todate() -> None:
    """Submitting an earlier month must fix later months' stale precip_todate."""
    # October saved before September daily data exists → under-counted YTD
    make_daily_obs_for_month(2025, 8, days=1, precip="1.00")
    make_daily_obs_for_month(2025, 10, days=1, precip="3.00")
    calc_monthly_summary(2025, 10, save_to_db=True)
    oct_summary = MonthlySummary.objects.get(date__year=2025, date__month=10)
    assert oct_summary.precip_todate == Decimal("4.00")

    # September arrives later
    make_daily_obs_for_month(2025, 9, days=1, precip="2.00")
    calc_monthly_summary(2025, 9, save_to_db=True)
    recalc_dependent_monthly_summaries(2025, 9)

    oct_summary.refresh_from_db()
    assert oct_summary.precip_todate == Decimal("6.00")
