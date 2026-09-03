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
    empty_snowseason,
    get_month_abbr,
    get_month_name,
)
from boilerplate.settings import TRACE_VAL

pytestmark = pytest.mark.unit


def test_get_month_name() -> None:
    assert get_month_name(1) == "January"
    assert get_month_name(12) == "December"


def test_get_month_abbr() -> None:
    assert get_month_abbr(1) == "jan"
    assert get_month_abbr(10) == "oct"


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
