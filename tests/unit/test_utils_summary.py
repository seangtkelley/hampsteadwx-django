"""Unit tests for summary calculations (ORM and normals mocked)."""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pandas as pd
import pytest

from api.utils import calc_annual_summary, calc_general_summary, calc_monthly_summary
from boilerplate.settings import TRACE_VAL
from tests.unit.fakes import fake_daily_row, patch_daily_ob_objects

pytestmark = pytest.mark.unit

# 13 monthly+annual slots for mocked normals
MOCK_NORMALS = {
    "temp": [Decimal(str(30 + i)) for i in range(12)] + [Decimal("40")],
    "precip": [Decimal("1.0")] * 12 + [Decimal("12.0")],
    "sf": [Decimal("2.0")] * 12 + [Decimal("24.0")],
}


def _obs_dataframe(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def test_calc_general_summary_temps_and_ties() -> None:
    df = _obs_dataframe(
        [
            {
                "date": date(2020, 1, 1),
                "max_temp": 90.0,
                "min_temp": 10.0,
                "atob_temp": 50.0,
                "precip": 0.0,
                "snowfall": 0.0,
                "snowdepth": 0.0,
            },
            {
                "date": date(2020, 1, 2),
                "max_temp": 90.0,
                "min_temp": 10.0,
                "atob_temp": 50.0,
                "precip": 0.0,
                "snowfall": 0.0,
                "snowdepth": 0.0,
            },
            {
                "date": date(2020, 1, 3),
                "max_temp": 30.0,
                "min_temp": -5.0,
                "atob_temp": 12.0,
                "precip": 0.0,
                "snowfall": 0.0,
                "snowdepth": 0.0,
            },
        ]
    )
    summary = calc_general_summary(df)
    assert summary["max_temp"] == Decimal("90.0")
    assert list(summary["max_temp_dates"]) == [date(2020, 1, 1), date(2020, 1, 2)]
    assert summary["max_temp_grtr90_count"] == 2
    assert summary["max_temp_less32_count"] == 1
    assert summary["min_temp"] == Decimal("-5.0")
    assert list(summary["min_temp_dates"]) == [date(2020, 1, 3)]
    assert summary["min_temp_less32_count"] == 3
    assert summary["min_temp_less0_count"] == 1
    assert summary["grtst_precip_dates"] == []


def test_calc_general_summary_hdd_cdd() -> None:
    df = _obs_dataframe(
        [
            {
                "date": date(2020, 7, 1),
                "max_temp": 50.0,
                "min_temp": 40.0,
                "atob_temp": 45.0,
                "precip": 0.0,
                "snowfall": 0.0,
                "snowdepth": 0.0,
            },
            {
                "date": date(2020, 7, 2),
                "max_temp": 80.0,
                "min_temp": 70.0,
                "atob_temp": 75.0,
                "precip": 0.0,
                "snowfall": 0.0,
                "snowdepth": 0.0,
            },
        ]
    )
    summary = calc_general_summary(df)
    assert summary["hdd_count"] == 20
    assert summary["cdd_count"] == 10


def test_calc_general_summary_trace_only_precip_and_snow() -> None:
    df = _obs_dataframe(
        [
            {
                "date": date(2020, 1, 1),
                "max_temp": 40.0,
                "min_temp": 20.0,
                "atob_temp": 30.0,
                "precip": TRACE_VAL,
                "snowfall": TRACE_VAL,
                "snowdepth": TRACE_VAL,
            }
        ]
    )
    summary = calc_general_summary(df)
    assert summary["precip"] == TRACE_VAL
    assert summary["sf"] == TRACE_VAL
    assert summary["precip_grtrT"] == 1


def test_calc_general_summary_excludes_traces_from_sum() -> None:
    df = _obs_dataframe(
        [
            {
                "date": date(2020, 1, 1),
                "max_temp": 40.0,
                "min_temp": 20.0,
                "atob_temp": 30.0,
                "precip": TRACE_VAL,
                "snowfall": TRACE_VAL,
                "snowdepth": 0.0,
            },
            {
                "date": date(2020, 1, 2),
                "max_temp": 40.0,
                "min_temp": 20.0,
                "atob_temp": 30.0,
                "precip": Decimal("0.5"),
                "snowfall": Decimal("2.0"),
                "snowdepth": Decimal("3.0"),
            },
        ]
    )
    summary = calc_general_summary(df)
    assert summary["precip"] == Decimal("0.5")
    assert summary["sf"] == Decimal("2.0")
    assert list(summary["grtst_precip_dates"]) == [date(2020, 1, 2)]
    assert summary["sf_grtr1"] == 1
    assert summary["sd_grtr3"] == 1


def test_calc_monthly_summary_no_data(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_daily_ob_objects(monkeypatch, [])
    assert calc_monthly_summary(1999, 1) is None


def test_calc_annual_summary_no_data(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_daily_ob_objects(monkeypatch, [])
    assert calc_annual_summary(1999) is None


def test_calc_monthly_summary_departures(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("api.utils.get_normals", lambda _year: MOCK_NORMALS)
    rows = [
        fake_daily_row(date(2020, 1, 1), precip="1.0"),
        fake_daily_row(date(2020, 1, 2), precip="1.0"),
    ]
    patch_daily_ob_objects(monkeypatch, rows)
    summary = calc_monthly_summary(2020, 1, save_to_db=False)
    assert isinstance(summary, dict)
    assert summary["precip"] == Decimal("2.0")
    assert summary["precip_dfn"] == Decimal("2.0") - MOCK_NORMALS["precip"][0]
    assert (
        summary["avg_temp_dfn"]
        == Decimal(str(summary["avg_temp"])) - MOCK_NORMALS["temp"][0]
    )
    assert summary["precip_todate"] == Decimal("2.0")


def test_calc_monthly_summary_precip_todate_zero_when_only_traces(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("api.utils.get_normals", lambda _year: MOCK_NORMALS)
    patch_daily_ob_objects(
        monkeypatch,
        [fake_daily_row(date(2020, 1, 1), precip=TRACE_VAL)],
    )
    summary = calc_monthly_summary(2020, 1, save_to_db=False)
    assert isinstance(summary, dict)
    assert summary["precip_todate"] == Decimal("0")


def test_calc_monthly_summary_sf_todate_oct(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("api.utils.get_normals", lambda _year: MOCK_NORMALS)
    patch_daily_ob_objects(
        monkeypatch,
        [fake_daily_row(date(2020, 10, 1), snowfall="3.0", snowdepth="3.0")],
    )
    summary = calc_monthly_summary(2020, 10, save_to_db=False)
    assert isinstance(summary, dict)
    assert summary["sf_todate"] == Decimal("3.0")
    assert summary["sf_todate_dfn"] == Decimal("3.0") - MOCK_NORMALS["sf"][9]


def test_calc_monthly_summary_sf_todate_jan_cross_year(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("api.utils.get_normals", lambda _year: MOCK_NORMALS)
    patch_daily_ob_objects(
        monkeypatch,
        [
            fake_daily_row(date(2019, 10, 1), snowfall="2.0"),
            fake_daily_row(date(2019, 11, 1), snowfall="1.0"),
            fake_daily_row(date(2020, 1, 1), snowfall="4.0"),
        ],
    )
    summary = calc_monthly_summary(2020, 1, save_to_db=False)
    assert isinstance(summary, dict)
    assert summary["sf_todate"] == Decimal("7.0")


def test_calc_monthly_summary_sf_todate_summer_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("api.utils.get_normals", lambda _year: MOCK_NORMALS)
    patch_daily_ob_objects(
        monkeypatch,
        [fake_daily_row(date(2020, 7, 1), precip="0.1")],
    )
    summary = calc_monthly_summary(2020, 7, save_to_db=False)
    assert isinstance(summary, dict)
    assert summary["sf_todate"] == Decimal("0")
    assert summary["sf_todate_dfn"] == Decimal("0")


def test_calc_monthly_summary_save_creates_snowseason(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("api.utils.get_normals", lambda _year: MOCK_NORMALS)
    patch_daily_ob_objects(
        monkeypatch,
        [fake_daily_row(date(2020, 11, 1), snowfall="5.0", snowdepth="5.0")],
    )

    monthly_manager = MagicMock()
    monthly_manager.filter.return_value.exists.return_value = False
    monthly_manager.create.return_value = MagicMock()
    monkeypatch.setattr("api.utils.models.MonthlySummary.objects", monthly_manager)

    snow = MagicMock()
    snow.oct = Decimal("0")
    snow.nov = Decimal("0")
    snow.dec = Decimal("0")
    snow.jan = Decimal("0")
    snow.feb = Decimal("0")
    snow.mar = Decimal("0")
    snow.apr = Decimal("0")
    snow.may = Decimal("0")
    snow_manager = MagicMock()
    snow_manager.get_or_create.return_value = (snow, True)
    monkeypatch.setattr("api.utils.models.SnowSeason.objects", snow_manager)

    result = calc_monthly_summary(2020, 11, save_to_db=True)
    monthly_manager.create.assert_called_once()
    assert snow.nov == Decimal("5.0")
    assert snow.total == Decimal("5.0")
    snow.save.assert_called_once()
    assert result is monthly_manager.create.return_value
    snow_manager.get_or_create.assert_called_once()
    assert snow_manager.get_or_create.call_args.kwargs["season"] == "2020-2021"


def test_calc_monthly_summary_save_jan_season_string(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("api.utils.get_normals", lambda _year: MOCK_NORMALS)
    patch_daily_ob_objects(
        monkeypatch,
        [fake_daily_row(date(2021, 1, 5), snowfall="1.0", snowdepth="1.0")],
    )
    monthly_manager = MagicMock()
    monthly_manager.filter.return_value.exists.return_value = False
    monkeypatch.setattr("api.utils.models.MonthlySummary.objects", monthly_manager)

    snow = MagicMock(oct=0, nov=0, dec=0, jan=0, feb=0, mar=0, apr=0, may=0, total=0)
    snow_manager = MagicMock()
    snow_manager.get_or_create.return_value = (snow, True)
    monkeypatch.setattr("api.utils.models.SnowSeason.objects", snow_manager)

    calc_monthly_summary(2021, 1, save_to_db=True)
    assert snow_manager.get_or_create.call_args.kwargs["season"] == "2020-2021"
    assert snow.jan == Decimal("1.0")


def test_calc_annual_summary_create_and_update(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("api.utils.get_normals", lambda _year: MOCK_NORMALS)
    rows = [
        fake_daily_row(date(2018, 3, 1), precip="0.5"),
        fake_daily_row(date(2018, 3, 2), precip="0.5"),
    ]
    patch_daily_ob_objects(monkeypatch, rows)

    summary = calc_annual_summary(2018, save_to_db=False)
    assert isinstance(summary, dict)
    assert summary["year"] == 2018
    assert (
        summary["avg_temp_dfn"]
        == Decimal(str(summary["avg_temp"])) - MOCK_NORMALS["temp"][12]
    )

    annual_manager = MagicMock()
    annual_manager.filter.return_value.exists.return_value = False
    monkeypatch.setattr("api.utils.models.AnnualSummary.objects", annual_manager)
    calc_annual_summary(2018, save_to_db=True)
    annual_manager.create.assert_called_once()

    annual_manager.filter.return_value.exists.return_value = True
    annual_manager.filter.return_value.update.return_value = 1
    calc_annual_summary(2018, save_to_db=True)
    annual_manager.filter.return_value.update.assert_called_once()
