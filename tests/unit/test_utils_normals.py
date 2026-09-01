"""Unit tests for climate normals loading (filesystem mocked via tmp_path)."""

from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

from api.utils import _numeric_series_to_decimals, get_normals

pytestmark = pytest.mark.unit

LEGACY_CONTENT = (
    "23.8,27.4,34.4,45.7,55.7,65.6,70.8,69.2,61.3,49.5,39.8,29.2,47.8\n"
    "3.27,3.43,4.48,4.4,4.04,4.18,3.74,3.58,3.94,4.4,4.47,4.21,48.18\n"
    "21.2,16.1,14.7,2.4,0,0,0,0,0,0.1,2.4,20.1,72.4\n"
)

MODERN_CONTENT = (
    "STATION,DATE,MLY-PRCP-NORMAL,MLY-SNOW-NORMAL,MLY-TAVG-NORMAL,"
    "MLY-TMAX-NORMAL,MLY-TMIN-NORMAL\n"
    + "\n".join(
        f'X,"{m:02d}",{3.0 + m * 0.01},{10.0 + m},{20.0 + m},30.0,10.0'
        for m in range(1, 13)
    )
    + "\n"
)


@pytest.fixture
def normals_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point api.utils.BASE_DIR at a temp tree with normals CSV fixtures."""
    csv_dir = tmp_path / "static" / "csv"
    csv_dir.mkdir(parents=True)
    (csv_dir / "HMPN3-Monthly-Climate-Normals.csv").write_text(LEGACY_CONTENT)
    (csv_dir / "normals-monthly-1991-2020-2022-01-23T16-24-36.csv").write_text(
        MODERN_CONTENT
    )
    monkeypatch.setattr("api.utils.BASE_DIR", tmp_path)
    return tmp_path


def test_get_normals_legacy_pre_2022(normals_root: Path) -> None:
    normals = get_normals(2021)
    assert len(normals["temp"]) == 13
    assert normals["temp"][0] == Decimal("23.8")
    assert normals["temp"][12] == Decimal("47.8")
    assert normals["precip"][12] == Decimal("48.18")
    assert normals["sf"][12] == Decimal("72.4")


def test_get_normals_modern_2022_plus(normals_root: Path) -> None:
    normals = get_normals(2022)
    assert len(normals["temp"]) == 13
    assert normals["temp"][0] == Decimal("21.0")  # 20.0 + 1
    assert normals["precip"][0] == Decimal("3.01")
    assert normals["sf"][0] == Decimal("11.0")
    assert normals["temp"][12] == Decimal(
        str(round(sum(float(v) for v in normals["temp"][:12]) / 12, 1))
    )


def test_numeric_series_to_decimals_rejects_nan() -> None:
    series = pd.to_numeric(pd.Series(["1.0", "bad", "3.0"]), errors="coerce")
    with pytest.raises(ValueError, match="Invalid numeric values"):
        _numeric_series_to_decimals(series, "TEST-COL")


def test_numeric_series_to_decimals_ok() -> None:
    series = pd.Series([1.5, 2.0])
    assert _numeric_series_to_decimals(series, "X") == [
        Decimal("1.5"),
        Decimal("2.0"),
    ]


def test_get_normals_invalid_modern_csv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    csv_dir = tmp_path / "static" / "csv"
    csv_dir.mkdir(parents=True)
    (csv_dir / "normals-monthly-1991-2020-2022-01-23T16-24-36.csv").write_text(
        "STATION,DATE,MLY-PRCP-NORMAL,MLY-SNOW-NORMAL,MLY-TAVG-NORMAL\n"
        "X,01,nope,1.0,2.0\n"
    )
    monkeypatch.setattr("api.utils.BASE_DIR", tmp_path)
    with pytest.raises(ValueError, match="Invalid numeric values"):
        get_normals(2023)
