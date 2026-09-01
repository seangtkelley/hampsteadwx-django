"""Unit tests for bulk_recalc with ORM and calc helpers mocked."""

from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

pytestmark = pytest.mark.unit


def test_bulk_recalc_requires_args() -> None:
    with pytest.raises(CommandError, match="Missing or malformed"):
        call_command("bulk_recalc")


@patch("api.management.commands.bulk_recalc.AnnualSummary.objects")
@patch("api.utils.calc_annual_summary")
def test_bulk_recalc_years_calls_annual(
    calc_annual: MagicMock, annual_objs: MagicMock
) -> None:
    annual_objs.filter.return_value = [SimpleNamespace(year=2015)]
    call_command("bulk_recalc", years=[2015])
    calc_annual.assert_called_once_with(2015, save_to_db=True)


@patch("api.management.commands.bulk_recalc.MonthlySummary.objects")
@patch("api.utils.calc_monthly_summary")
def test_bulk_recalc_months_only(
    calc_monthly: MagicMock, monthly_objs: MagicMock
) -> None:
    monthly_objs.filter.return_value = [
        SimpleNamespace(date=date(2016, 3, 1)),
    ]
    call_command("bulk_recalc", months=[3])
    calc_monthly.assert_called_once_with(2016, 3, save_to_db=True)


@patch("api.management.commands.bulk_recalc.MonthlySummary.objects")
@patch("api.utils.calc_monthly_summary")
def test_bulk_recalc_months_and_years(
    calc_monthly: MagicMock, monthly_objs: MagicMock
) -> None:
    monthly_objs.filter.return_value = [
        SimpleNamespace(date=date(2017, 4, 1)),
    ]
    call_command("bulk_recalc", months=[4], years=[2017])
    calc_monthly.assert_called_once_with(2017, 4, save_to_db=True)


@patch("api.management.commands.bulk_recalc.AnnualSummary.objects")
@patch("api.management.commands.bulk_recalc.MonthlySummary.objects")
@patch("api.utils.calc_annual_summary")
@patch("api.utils.calc_monthly_summary")
def test_bulk_recalc_all(
    calc_monthly: MagicMock,
    calc_annual: MagicMock,
    monthly_objs: MagicMock,
    annual_objs: MagicMock,
) -> None:
    monthly_objs.all.return_value = [SimpleNamespace(date=date(2019, 5, 1))]
    annual_objs.all.return_value = [SimpleNamespace(year=2019)]
    call_command("bulk_recalc", all=True)
    calc_monthly.assert_called_once_with(2019, 5, save_to_db=True)
    calc_annual.assert_called_once_with(2019, save_to_db=True)


@patch("api.management.commands.bulk_recalc.AnnualSummary.objects")
@patch("api.management.commands.bulk_recalc.MonthlySummary.objects")
@patch("api.utils.calc_annual_summary")
@patch("api.utils.calc_monthly_summary")
def test_bulk_recalc_all_years_only(
    calc_monthly: MagicMock,
    calc_annual: MagicMock,
    monthly_objs: MagicMock,
    annual_objs: MagicMock,
) -> None:
    annual_objs.all.return_value = [SimpleNamespace(year=2012)]
    call_command("bulk_recalc", all=True, years=[2012])
    calc_annual.assert_called_once_with(2012, save_to_db=True)
    calc_monthly.assert_not_called()


@patch("api.management.commands.bulk_recalc.AnnualSummary.objects")
@patch("api.management.commands.bulk_recalc.MonthlySummary.objects")
@patch("api.utils.calc_annual_summary")
@patch("api.utils.calc_monthly_summary")
def test_bulk_recalc_all_months_only(
    calc_monthly: MagicMock,
    calc_annual: MagicMock,
    monthly_objs: MagicMock,
    annual_objs: MagicMock,
) -> None:
    monthly_objs.all.return_value = [SimpleNamespace(date=date(2014, 6, 1))]
    call_command("bulk_recalc", all=True, months=[6])
    calc_monthly.assert_called_once_with(2014, 6, save_to_db=True)
    calc_annual.assert_not_called()
