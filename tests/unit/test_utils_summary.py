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
            fake_daily_row(date(2020, 1, 1), max_temp="90.0", min_temp="10.0"),
            fake_daily_row(date(2020, 1, 2), max_temp="90.0", min_temp="10.0"),
            fake_daily_row(date(2020, 1, 3), max_temp="30.0", min_temp="-5.0"),
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
            fake_daily_row(date(2020, 7, 1), max_temp="50.0", min_temp="40.0"),
            fake_daily_row(date(2020, 7, 2), max_temp="80.0", min_temp="70.0"),
        ]
    )
    summary = calc_general_summary(df)
    assert summary["hdd_count"] == 20
    assert summary["cdd_count"] == 10
    assert isinstance(summary["max_temp_avg"], Decimal)
    assert summary["max_temp_avg"] == Decimal("65")
    assert isinstance(summary["avg_temp"], Decimal)
    assert summary["avg_temp"] == Decimal("60")


@pytest.mark.parametrize(
    ("max_temp", "min_temp", "field", "expected"),
    [
        # mean 59.5, diff from 65 is 5.5 -> banker's rounding to nearest even (6)
        ("70.0", "49.0", "hdd_count", 6),
        # mean 60.5, diff from 65 is 4.5 -> rounds down to nearest even (4)
        ("71.0", "50.0", "hdd_count", 4),
        # mean 65.5, diff from 65 is 0.5 -> rounds down to nearest even (0)
        ("81.0", "50.0", "cdd_count", 0),
        # mean 66.5, diff from 65 is 1.5 -> rounds up to nearest even (2)
        ("83.0", "50.0", "cdd_count", 2),
    ],
)
def test_calc_general_summary_hdd_cdd_uses_banker_rounding(
    max_temp: str, min_temp: str, field: str, expected: int
) -> None:
    """round() on the summed Decimal diff is round-half-to-even, not half-up.

    Locks in the exact rounding behavior so a future change to how hdd/cdd are
    accumulated (e.g. per-day rounding, or a switch away from round()) doesn't
    silently shift totals for these boundary means.
    """
    df = _obs_dataframe(
        [fake_daily_row(date(2020, 1, 1), max_temp=max_temp, min_temp=min_temp)]
    )
    summary = calc_general_summary(df)
    assert summary[field] == expected


def test_calc_general_summary_hdd_cdd_boundary_at_exactly_65() -> None:
    """A day with mean temp exactly 65 counts toward neither hdd nor cdd."""
    df = _obs_dataframe(
        [fake_daily_row(date(2020, 5, 1), max_temp="70.0", min_temp="60.0")]
    )
    summary = calc_general_summary(df)
    assert summary["hdd_count"] == 0
    assert summary["cdd_count"] == 0


def test_calc_general_summary_precip_sum_has_no_float_drift() -> None:
    """0.1 + 0.2 + 0.3 is 0.30000000000000004 in binary float; must be exact here."""
    df = _obs_dataframe(
        [
            fake_daily_row(date(2020, 1, 1), precip="0.1"),
            fake_daily_row(date(2020, 1, 2), precip="0.2"),
            fake_daily_row(date(2020, 1, 3), precip="0.3"),
        ]
    )
    summary = calc_general_summary(df)
    assert summary["precip"] == Decimal("0.6")


def test_calc_general_summary_avg_temp_keeps_precision_past_one_decimal() -> None:
    """Averages that don't terminate at 1 decimal place must not be truncated.

    ``max_temp_avg``/``avg_temp`` are only rounded once they hit the
    DecimalField on save; calc_general_summary itself should return the full
    precision average.
    """
    df = _obs_dataframe(
        [
            fake_daily_row(date(2020, 1, 1), max_temp="10.0", min_temp="10.0"),
            fake_daily_row(date(2020, 1, 2), max_temp="10.0", min_temp="10.0"),
            fake_daily_row(date(2020, 1, 3), max_temp="11.0", min_temp="11.0"),
        ]
    )
    summary = calc_general_summary(df)
    expected = Decimal("31") / 3
    assert summary["max_temp_avg"] == expected
    assert summary["avg_temp"] == expected


def test_calc_general_summary_ties_for_greatest_precip_sf_sd() -> None:
    """Multi-day ties for the greatest precip/sf/sd must list every tied date."""
    df = _obs_dataframe(
        [
            fake_daily_row(
                date(2020, 1, 1), precip="0.5", snowfall="3.0", snowdepth="4.0"
            ),
            fake_daily_row(
                date(2020, 1, 2), precip="0.5", snowfall="3.0", snowdepth="4.0"
            ),
            fake_daily_row(
                date(2020, 1, 3), precip="0.2", snowfall="1.0", snowdepth="1.0"
            ),
        ]
    )
    summary = calc_general_summary(df)
    tied_dates = [date(2020, 1, 1), date(2020, 1, 2)]
    assert list(summary["grtst_precip_dates"]) == tied_dates
    assert list(summary["grtst_sf_dates"]) == tied_dates
    assert list(summary["grtst_sd_dates"]) == tied_dates


def test_calc_general_summary_trace_only_precip_and_snow() -> None:
    df = _obs_dataframe(
        [
            fake_daily_row(
                date(2020, 1, 1),
                precip=TRACE_VAL,
                snowfall=TRACE_VAL,
                snowdepth=TRACE_VAL,
            )
        ]
    )
    summary = calc_general_summary(df)
    assert summary["precip"] == TRACE_VAL
    assert summary["sf"] == TRACE_VAL
    assert summary["precip_grtrT"] == 1


def test_calc_general_summary_trace_only_does_not_sum_to_float_drift() -> None:
    """Two T snowfall/precip days must yield Trace totals, not float drift (#16)."""
    df = _obs_dataframe(
        [
            fake_daily_row(
                date(2024, 10, 28),
                precip=TRACE_VAL,
                snowfall=TRACE_VAL,
                snowdepth=TRACE_VAL,
            ),
            fake_daily_row(
                date(2024, 10, 29),
                precip=TRACE_VAL,
                snowfall=TRACE_VAL,
                snowdepth="0",
            ),
        ]
    )
    summary = calc_general_summary(df)
    assert summary["precip"] == TRACE_VAL
    assert summary["sf"] == TRACE_VAL
    assert summary["grtst_sf"] == TRACE_VAL
    assert summary["grtst_sd"] == TRACE_VAL
    assert summary["sf_grtrT"] == 2
    assert summary["sd_grtrT"] == 1


def test_calc_general_summary_excludes_traces_from_sum() -> None:
    df = _obs_dataframe(
        [
            fake_daily_row(
                date(2020, 1, 1), precip=TRACE_VAL, snowfall=TRACE_VAL, snowdepth="0"
            ),
            fake_daily_row(
                date(2020, 1, 2), precip="0.5", snowfall="2.0", snowdepth="3.0"
            ),
        ]
    )
    summary = calc_general_summary(df)
    assert summary["precip"] == Decimal("0.5")
    assert summary["sf"] == Decimal("2.0")
    assert list(summary["grtst_precip_dates"]) == [date(2020, 1, 2)]
    assert summary["sf_grtr1"] == 1
    assert summary["sd_grtr3"] == 1


def test_calc_general_summary_handles_float_dtype_frame() -> None:
    """calc_general_summary must still tolerate a float64 frame defensively."""
    df = _obs_dataframe(
        [
            {
                "date": date(2020, 1, 1),
                "max_temp": 40.0,
                "min_temp": 20.0,
                "atob_temp": 30.0,
                "precip": 0.5,
                "snowfall": 2.0,
                "snowdepth": 3.0,
            }
        ]
    )
    summary = calc_general_summary(df)
    assert summary["precip"] == Decimal("0.5")
    assert summary["sf"] == Decimal("2.0")


def test_calc_monthly_summary_no_data(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_daily_ob_objects(monkeypatch, [])
    assert calc_monthly_summary(1999, 1) is None


def test_calc_monthly_summary_orders_by_date(monkeypatch: pytest.MonkeyPatch) -> None:
    """FakeQuerySet.order_by must sort so summary date is the earliest day."""
    monkeypatch.setattr("api.utils.get_normals", lambda _year: MOCK_NORMALS)
    patch_daily_ob_objects(
        monkeypatch,
        [
            fake_daily_row(date(2020, 1, 3), precip="0.1"),
            fake_daily_row(date(2020, 1, 1), precip="0.1"),
            fake_daily_row(date(2020, 1, 2), precip="0.1"),
        ],
    )
    summary = calc_monthly_summary(2020, 1, save_to_db=False)
    assert isinstance(summary, dict)
    assert summary["date"] == date(2020, 1, 1)


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


def test_calc_monthly_summary_precip_todate_avoids_float_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ten 0.1" days must sum to exactly 1.0, not a float-accumulated 0.9999...9.

    Exercises the same Decimal summation path calc_monthly_summary feeds into
    both ``precip`` (per-month) and ``precip_todate`` (cumulative), not just
    calc_general_summary in isolation.
    """
    monkeypatch.setattr("api.utils.get_normals", lambda _year: MOCK_NORMALS)
    rows = [fake_daily_row(date(2020, 1, i + 1), precip="0.1") for i in range(10)]
    patch_daily_ob_objects(monkeypatch, rows)
    summary = calc_monthly_summary(2020, 1, save_to_db=False)
    assert isinstance(summary, dict)
    assert summary["precip"] == Decimal("1.0")
    assert summary["precip_todate"] == Decimal("1.0")


def test_calc_monthly_summary_precip_todate_trace_when_only_traces(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("api.utils.get_normals", lambda _year: MOCK_NORMALS)
    patch_daily_ob_objects(
        monkeypatch,
        [fake_daily_row(date(2020, 1, 1), precip=TRACE_VAL)],
    )
    summary = calc_monthly_summary(2020, 1, save_to_db=False)
    assert isinstance(summary, dict)
    assert summary["precip_todate"] == TRACE_VAL


def test_calc_monthly_summary_trace_only_snowfall_is_trace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Oct 2024 reproduction: two T snowfall days must yield Total Snowfall Trace (#16)."""
    monkeypatch.setattr("api.utils.get_normals", lambda _year: MOCK_NORMALS)
    patch_daily_ob_objects(
        monkeypatch,
        [
            fake_daily_row(
                date(2024, 10, 28),
                precip=TRACE_VAL,
                snowfall=TRACE_VAL,
                snowdepth=TRACE_VAL,
            ),
            fake_daily_row(
                date(2024, 10, 29),
                precip=TRACE_VAL,
                snowfall=TRACE_VAL,
                snowdepth="0",
            ),
        ],
    )
    summary = calc_monthly_summary(2024, 10, save_to_db=False)
    assert isinstance(summary, dict)
    assert summary["sf"] == TRACE_VAL
    assert summary["grtst_sf"] == TRACE_VAL
    assert summary["sf_grtrT"] == 2
    assert summary["sd_grtrT"] == 1
    assert summary["sf_todate"] == TRACE_VAL
    assert summary["precip_todate"] == TRACE_VAL


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


def test_calc_monthly_summary_save_snowseason_trace_total(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Trace-only months must not sum to 0.002 on the snow-season total."""
    monkeypatch.setattr("api.utils.get_normals", lambda _year: MOCK_NORMALS)
    patch_daily_ob_objects(
        monkeypatch,
        [fake_daily_row(date(2024, 11, 23), snowfall=TRACE_VAL)],
    )

    monthly_manager = MagicMock()
    monthly_manager.filter.return_value.exists.return_value = False
    monkeypatch.setattr("api.utils.models.MonthlySummary.objects", monthly_manager)

    snow = MagicMock()
    snow.oct = TRACE_VAL
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

    calc_monthly_summary(2024, 11, save_to_db=True)
    assert snow.nov == TRACE_VAL
    assert snow.total == TRACE_VAL


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


def test_calc_monthly_summary_update_omits_remarks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Recalc update must not pass remarks (preserves existing DB remarks)."""
    monkeypatch.setattr("api.utils.get_normals", lambda _year: MOCK_NORMALS)
    patch_daily_ob_objects(
        monkeypatch,
        [fake_daily_row(date(2013, 7, 1), precip="0.2")],
    )
    monthly_manager = MagicMock()
    monthly_manager.filter.return_value.exists.return_value = True
    monthly_manager.filter.return_value.update.return_value = 1
    monkeypatch.setattr("api.utils.models.MonthlySummary.objects", monthly_manager)

    calc_monthly_summary(2013, 7, save_to_db=True)
    monthly_manager.filter.return_value.update.assert_called_once()
    update_kwargs = monthly_manager.filter.return_value.update.call_args.kwargs
    assert "remarks" not in update_kwargs
    assert float(update_kwargs["precip"]) == pytest.approx(0.2)


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
