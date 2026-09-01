"""In-memory ORM stand-ins for unit tests."""

from __future__ import annotations

from copy import deepcopy
from datetime import date
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock


class FakeQuerySet:
    """Minimal QuerySet stand-in supporting filter/exclude/aggregate/values."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = [deepcopy(r) for r in rows]

    def filter(self, **kwargs: object) -> FakeQuerySet:
        return FakeQuerySet([r for r in self.rows if _row_matches(r, kwargs)])

    def exclude(self, **kwargs: object) -> FakeQuerySet:
        return FakeQuerySet([r for r in self.rows if not _row_matches(r, kwargs)])

    def order_by(self, *_args: object) -> FakeQuerySet:
        return self

    def count(self) -> int:
        return len(self.rows)

    def exists(self) -> bool:
        return bool(self.rows)

    def values(self, *_fields: str) -> list[dict[str, Any]]:
        return [deepcopy(r) for r in self.rows]

    def first(self) -> dict[str, Any] | None:
        return deepcopy(self.rows[0]) if self.rows else None

    def all(self) -> FakeQuerySet:
        return FakeQuerySet(self.rows)

    def aggregate(self, *args: object, **_kwargs: object) -> dict[str, Decimal | None]:
        if not args:
            return {}
        field = str(args[0])
        if "precip" in field:
            key, col = "precip__sum", "precip"
        elif "snowfall" in field:
            key, col = "snowfall__sum", "snowfall"
        else:
            return {}
        if not self.rows:
            return {key: None}
        total = sum((Decimal(str(r[col])) for r in self.rows), Decimal("0"))
        return {key: total}


def _row_matches(row: dict[str, Any], kwargs: dict[str, object]) -> bool:
    day = row["date"]
    if not isinstance(day, date):
        day = date.fromisoformat(str(day))
    for key, expected in kwargs.items():
        if key == "date":
            if day != expected:
                return False
        elif key == "date__year":
            if day.year != expected:
                return False
        elif key == "date__month":
            if day.month != expected:
                return False
        elif key == "date__month__in":
            if day.month not in expected:  # type: ignore[operator]
                return False
        elif key == "date__year__in":
            if day.year not in expected:  # type: ignore[operator]
                return False
        elif key.endswith("__in"):
            field = key[: -len("__in")]
            if row.get(field) not in expected:  # type: ignore[operator]
                return False
        elif row.get(key) != expected:
            return False
    return True


def patch_daily_ob_objects(monkeypatch: Any, rows: list[dict[str, Any]]) -> MagicMock:
    """Patch ``api.utils.models.DailyOb.objects`` with a FakeQuerySet-backed manager."""
    manager = MagicMock()
    store = {"rows": [deepcopy(r) for r in rows]}

    def filter_(**kwargs: object) -> FakeQuerySet:
        return FakeQuerySet(store["rows"]).filter(**kwargs)

    def create(**kwargs: object) -> MagicMock:
        row = dict(kwargs)
        store["rows"].append(row)
        obj = MagicMock()
        for k, v in kwargs.items():
            setattr(obj, k, v)
        obj.save = MagicMock()
        return obj

    manager.filter.side_effect = filter_
    manager.create.side_effect = create
    monkeypatch.setattr("api.utils.models.DailyOb.objects", manager)
    return manager


def fake_daily_row(
    day: date,
    *,
    max_temp: str | Decimal = "40.0",
    min_temp: str | Decimal = "20.0",
    atob_temp: str | Decimal = "30.0",
    precip: str | Decimal = "0",
    snowfall: str | Decimal = "0",
    snowdepth: str | Decimal = "0",
    csv_filepath: str = "/tmp/test.csv",
) -> dict[str, Any]:
    """Build a DailyOb-like values() dict for FakeQuerySet."""
    return {
        "id": 1,
        "date": day,
        "csv_filepath": csv_filepath,
        "max_temp": Decimal(str(max_temp)),
        "min_temp": Decimal(str(min_temp)),
        "atob_temp": Decimal(str(atob_temp)),
        "precip": Decimal(str(precip)),
        "snowfall": Decimal(str(snowfall)),
        "snowdepth": Decimal(str(snowdepth)),
    }
