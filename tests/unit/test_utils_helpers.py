"""Unit tests for pure helper utilities."""

import pytest

from api.utils import (
    add_alert,
    create_alert,
    empty_snowseason,
    get_month_abbr,
    get_month_name,
)

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
