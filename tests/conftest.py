"""Shared pytest configuration for unit and integration suites."""

from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path

import pytest

# Must be set before Django settings are imported by pytest-django.
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault(
    "DATABASE_URL",
    "postgres://hampsteadwx_dev:test@127.0.0.1:5433/hampsteadwx_test",
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
SAMPLE_CSV = FIXTURES_DIR / "sample_daily.csv"


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "integration: tests that require PostgreSQL and hit the real ORM/filesystem",
    )
    config.addinivalue_line(
        "markers",
        "unit: fast tests with external dependencies mocked",
    )


@pytest.fixture(autouse=True)
def _test_settings(settings) -> None:
    """Configure Django settings that are awkward under pytest."""
    settings.ALLOWED_HOSTS = ["*", "testserver"]
    settings.DEBUG = True
    settings.STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )


@pytest.fixture
def site_pass(monkeypatch: pytest.MonkeyPatch) -> str:
    """Set SITE_PASS for password-gated views."""
    password = "test-site-pass"
    monkeypatch.setenv("SITE_PASS", password)
    return password


@pytest.fixture
def sample_csv_path() -> Path:
    """Path to the checked-in sample daily observation CSV."""
    return SAMPLE_CSV


def _empty_date_arrays() -> dict[str, list]:
    """Return empty nested date-array fields required by GeneralSummary."""
    return {
        "max_temp_dates": [],
        "min_temp_dates": [],
        "grtst_precip_dates": [],
        "grtst_sf_dates": [],
        "grtst_sd_dates": [],
    }


def general_summary_defaults(**overrides: object) -> dict[str, object]:
    """Build a minimal set of GeneralSummary field values."""
    data: dict[str, object] = {
        "max_temp": Decimal("50.0"),
        "max_temp_avg": Decimal("45.0"),
        "max_temp_grtr90_count": 0,
        "max_temp_less32_count": 0,
        "min_temp": Decimal("20.0"),
        "min_temp_avg": Decimal("25.0"),
        "min_temp_less32_count": 0,
        "min_temp_less0_count": 0,
        "avg_temp": Decimal("35.0"),
        "avg_temp_dfn": Decimal("0.0"),
        "hdd_count": 0,
        "cdd_count": 0,
        "precip": Decimal("1.000"),
        "precip_dfn": Decimal("0.000"),
        "grtst_precip": Decimal("0.500"),
        "precip_grtrT": 1,
        "precip_grtr01": 1,
        "precip_grtr10": 1,
        "precip_grtr50": 1,
        "precip_grtr100": 0,
        "sf": Decimal("0.000"),
        "sf_dfn": Decimal("0.000"),
        "grtst_sf": Decimal("0.000"),
        "sf_grtrT": 0,
        "sf_grtr1": 0,
        "sf_grtr3": 0,
        "sf_grtr6": 0,
        "sf_grtr12": 0,
        "sf_grtr18": 0,
        "grtst_sd": Decimal("0.000"),
        "sd_grtrT": 0,
        "sd_grtr1": 0,
        "sd_grtr3": 0,
        "sd_grtr6": 0,
        "sd_grtr12": 0,
        "sd_grtr18": 0,
        **_empty_date_arrays(),
    }
    data.update(overrides)
    return data


@pytest.fixture
def write_csv(tmp_path: Path):
    """Return a helper that writes a daily CSV and returns its path."""

    def _write(
        rows: list[dict[str, object]],
        filename: str = "obs.csv",
    ) -> Path:
        path = tmp_path / filename
        header = "DATE,TX,TN,TA,PP,SF,SD"
        lines = [header] + [
            f"{row['DATE']},{row['TX']},{row['TN']},{row['TA']},"
            f"{row['PP']},{row['SF']},{row['SD']}"
            for row in rows
        ]
        path.write_text("\n".join(lines) + "\n")
        return path

    return _write
