"""Integration tests: CSV ingest against PostgreSQL."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from api.models import DailyOb
from api.utils import process_csv
from boilerplate.settings import TRACE_VAL
from tests.integration.conftest import make_daily_ob

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def test_process_csv_inserts_rows(sample_csv_path: Path) -> None:
    year, month = process_csv(sample_csv_path)
    assert year == 2020
    assert month == 1
    assert DailyOb.objects.count() == 3
    first = DailyOb.objects.get(date="2020-01-01")
    assert first.max_temp == Decimal("35.0")
    assert first.precip == Decimal("0.10")


def test_process_csv_maps_trace(sample_csv_path: Path) -> None:
    process_csv(sample_csv_path)
    trace_day = DailyOb.objects.get(date="2020-01-02")
    assert trace_day.precip == TRACE_VAL
    assert trace_day.snowfall == TRACE_VAL
    assert trace_day.snowdepth == TRACE_VAL


def test_process_csv_updates_existing(write_csv) -> None:
    make_daily_ob(date(2021, 2, 1), max_temp="10.0", csv_filepath="/old.csv")
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
    process_csv(path)
    assert DailyOb.objects.count() == 1
    ob = DailyOb.objects.get(date="2021-02-01")
    assert ob.max_temp == Decimal("55.0")
    assert ob.precip == Decimal("0.55")
