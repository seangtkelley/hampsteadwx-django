"""Unit tests for CSV ingest with ORM mocked."""

from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from api.utils import process_csv
from boilerplate.settings import TRACE_VAL

pytestmark = pytest.mark.unit


def _patch_daily_ob(
    monkeypatch: pytest.MonkeyPatch, *, exists: bool
) -> tuple[MagicMock, list[MagicMock], MagicMock | None]:
    """Patch DailyOb constructor and manager; return (cls, created, existing)."""
    created: list[MagicMock] = []
    existing: MagicMock | None = MagicMock() if exists else None
    if existing is not None:
        existing.save = MagicMock()

    cls = MagicMock()
    qs = MagicMock()
    qs.exists.return_value = exists
    qs.first.return_value = existing
    cls.objects.filter.return_value = qs

    def ctor(**kwargs: object) -> MagicMock:
        obj = MagicMock()
        for key, value in kwargs.items():
            setattr(obj, key, value)
        obj.save = MagicMock()
        created.append(obj)
        return obj

    cls.side_effect = ctor
    monkeypatch.setattr("api.utils.models.DailyOb", cls)
    return cls, created, existing


def test_process_csv_inserts_and_maps_trace(
    sample_csv_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, created, _ = _patch_daily_ob(monkeypatch, exists=False)

    year, month = process_csv(sample_csv_path)
    assert year == 2020
    assert month == 1
    assert len(created) == 3
    assert created[0].max_temp == Decimal("35.0")
    assert created[0].precip == Decimal("0.10")
    assert created[0].snowfall == Decimal("1.5")
    assert created[1].precip == TRACE_VAL
    assert created[1].snowfall == TRACE_VAL
    assert created[1].snowdepth == TRACE_VAL
    for inst in created:
        inst.save.assert_called_once()


def test_process_csv_updates_existing(
    write_csv, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, created, existing = _patch_daily_ob(monkeypatch, exists=True)
    assert existing is not None

    path = write_csv(
        [
            {
                "DATE": "2021-02-01",
                "TX": "55.0",
                "TN": "30.0",
                "TA": "42.0",
                "PP": "0.55",
                "SF": "2.0",
                "SD": "3.0",
            }
        ]
    )
    year, month = process_csv(path)
    assert (year, month) == (2021, 2)
    assert created == []
    assert existing.max_temp == Decimal("55.0")
    assert existing.min_temp == Decimal("30.0")
    assert float(existing.precip) == pytest.approx(0.55)
    assert float(existing.snowfall) == pytest.approx(2.0)
    assert str(existing.csv_filepath) == str(path)
    existing.save.assert_called_once()
