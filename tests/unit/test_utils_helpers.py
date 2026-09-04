"""Unit tests for pure helper utilities."""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from api.utils import (
    ZERO,
    _snowseason_total,
    _total_with_optional_trace,
    add_alert,
    create_alert,
    dependent_months_for_todate,
    empty_snowseason,
    get_month_abbr,
    get_month_name,
    recalc_dependent_monthly_summaries,
)
from boilerplate.settings import TRACE_VAL

pytestmark = pytest.mark.unit


def test_get_month_name() -> None:
    assert get_month_name(1) == "January"
    assert get_month_name(12) == "December"


def test_get_month_abbr() -> None:
    assert get_month_abbr(1) == "jan"
    assert get_month_abbr(10) == "oct"


def test_dependent_months_for_todate_mid_year() -> None:
    assert dependent_months_for_todate(2019, 9) == [
        (2019, 10),
        (2019, 11),
        (2019, 12),
    ]


def test_dependent_months_for_todate_december_spans_snow_season() -> None:
    assert dependent_months_for_todate(2025, 12) == [
        (2026, 1),
        (2026, 2),
        (2026, 3),
        (2026, 4),
        (2026, 5),
    ]


def test_dependent_months_for_todate_october_includes_next_spring() -> None:
    assert dependent_months_for_todate(2025, 10) == [
        (2025, 11),
        (2025, 12),
        (2026, 1),
        (2026, 2),
        (2026, 3),
        (2026, 4),
        (2026, 5),
    ]


def test_recalc_dependent_monthly_summaries_only_existing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cascade recalcs only months that already have a MonthlySummary row."""
    calls: list[tuple[int, int]] = []

    def fake_calc(year: int, month: int, save_to_db: bool = False) -> None:
        calls.append((year, month))
        assert save_to_db is True

    monthly_manager = MagicMock()

    def filter_side_effect(**kwargs: object) -> MagicMock:
        result = MagicMock()
        # Pretend only November 2025 exists among dependents of September
        result.exists.return_value = kwargs == {
            "date__year": 2025,
            "date__month": 11,
        }
        return result

    monthly_manager.filter.side_effect = filter_side_effect
    monkeypatch.setattr(
        "api.utils.models.MonthlySummary.objects", monthly_manager
    )
    monkeypatch.setattr("api.utils.calc_monthly_summary", fake_calc)

    recalc_dependent_monthly_summaries(2025, 9)
    assert calls == [(2025, 11)]


def test_create_alert() -> None:
    assert create_alert("success", "ok") == {"color": "success", "body": "ok"}


def test_add_alert_appends_to_empty_payload() -> None:
    payload = add_alert({"title": "t"}, "danger", "bad")
    assert payload["title"] == "t"
    assert payload["alerts"] == [{"color": "danger", "body": "bad"}]


def test_add_alert_appends_to_existing_alerts() -> None:
    payload = {"alerts": [{"color": "warning", "body": "w"}]}
    updated = add_alert(payload, "success", "s")
    assert len(updated["alerts"]) == 2
    assert updated["alerts"][1] == {"color": "success", "body": "s"}
    assert len(payload["alerts"]) == 1


def test_empty_snowseason() -> None:
    result = empty_snowseason("2020-2021")
    assert result["season"] == "2020-2021"
    assert result["oct"] == 0
    assert result["may"] == 0
    assert result["total"] == 0


def test_total_with_optional_trace() -> None:
    assert _total_with_optional_trace(None, has_trace=False) == ZERO
    assert _total_with_optional_trace(None, has_trace=True) == TRACE_VAL
    assert _total_with_optional_trace(ZERO, has_trace=True) == TRACE_VAL
    assert _total_with_optional_trace(ZERO, has_trace=False) == ZERO
    assert _total_with_optional_trace(Decimal("2.5"), has_trace=True) == Decimal("2.5")


def test_snowseason_total_collapses_traces() -> None:
    snow = MagicMock(
        oct=TRACE_VAL,
        nov=TRACE_VAL,
        dec=ZERO,
        jan=ZERO,
        feb=ZERO,
        mar=ZERO,
        apr=ZERO,
        may=ZERO,
    )
    assert _snowseason_total(snow) == TRACE_VAL

    snow.nov = Decimal("4.0")
    assert _snowseason_total(snow) == Decimal("4.0")
