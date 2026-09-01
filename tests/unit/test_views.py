"""Unit tests for views with ORM/utils/render mocked via RequestFactory."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404, HttpResponse
from django.test import RequestFactory

from api import views

pytestmark = pytest.mark.unit


@pytest.fixture
def rf() -> RequestFactory:
    return RequestFactory()


def _ok(*_args: object, **_kwargs: object) -> HttpResponse:
    return HttpResponse(b"ok")


def _render_context(mock_render: MagicMock) -> dict:
    # render(request, template, context)
    return mock_render.call_args.args[2]


@patch("api.views.render", side_effect=_ok)
def test_static_pages(mock_render: MagicMock, rf: RequestFactory) -> None:
    for view in (views.index, views.info_view, views.normals_view):
        assert view(rf.get("/")).status_code == 200
    assert mock_render.call_count == 3


@patch("api.views.render", side_effect=_ok)
def test_summary_homes(mock_render: MagicMock, rf: RequestFactory) -> None:
    assert views.summaries_monthly_home(rf.get("/")).status_code == 200
    assert views.summaries_annual_home(rf.get("/")).status_code == 200
    assert views.summaries_monthly_submit(rf.get("/")).status_code == 200


@patch("api.views.render", side_effect=_ok)
@patch("api.views.models.MonthlySummary.objects")
@patch("api.views.models.DailyOb.objects")
def test_monthly_view_missing_summary(
    daily_objs: MagicMock,
    monthly_objs: MagicMock,
    mock_render: MagicMock,
    rf: RequestFactory,
) -> None:
    monthly_objs.filter.return_value.exists.return_value = False
    daily_objs.filter.return_value.order_by.return_value = []
    views.summaries_monthly_view(rf.get("/"), 1990, 1)
    ctx = _render_context(mock_render)
    assert any(a["color"] == "warning" for a in ctx["alerts"])


@patch("api.views.render", side_effect=_ok)
@patch("api.views.models.MonthlySummary.objects")
@patch("api.views.models.DailyOb.objects")
def test_monthly_view_with_summary(
    daily_objs: MagicMock,
    monthly_objs: MagicMock,
    mock_render: MagicMock,
    rf: RequestFactory,
) -> None:
    summary = SimpleNamespace(remarks="hi")
    monthly_objs.filter.return_value.exists.return_value = True
    monthly_objs.filter.return_value.first.return_value = summary
    daily_objs.filter.return_value.order_by.return_value = ["obs"]
    views.summaries_monthly_view(rf.get("/"), 2020, 1)
    ctx = _render_context(mock_render)
    assert ctx["monthly_summary"] == summary
    assert ctx["daily_obs"] == ["obs"]


@patch("api.views.models.MonthlySummary.objects")
def test_monthly_text_404(monthly_objs: MagicMock, rf: RequestFactory) -> None:
    monthly_objs.filter.return_value.exists.return_value = False
    with pytest.raises(Http404):
        views.summaries_monthly_text(rf.get("/"), 1990, 1)


@patch("api.views.render", side_effect=_ok)
@patch("api.views.utils.get_normals")
@patch("api.views.models.MonthlySummary.objects")
def test_monthly_text_ok(
    monthly_objs: MagicMock,
    get_normals: MagicMock,
    mock_render: MagicMock,
    rf: RequestFactory,
) -> None:
    summary = SimpleNamespace()
    monthly_objs.filter.return_value.exists.return_value = True
    monthly_objs.filter.return_value.first.return_value = summary
    get_normals.return_value = {
        "temp": [1] * 13,
        "precip": [2] * 13,
        "sf": [3] * 13,
    }
    views.summaries_monthly_text(rf.get("/"), 2020, 1)
    ctx = _render_context(mock_render)
    assert ctx["monthly_summary"] == summary
    assert ctx["AVG_TEMP"] == 1


@patch("api.views.utils.calc_monthly_summary", return_value=None)
@patch("api.views.models.MonthlySummary.objects")
def test_monthly_csv_404(
    monthly_objs: MagicMock, _calc: MagicMock, rf: RequestFactory
) -> None:
    monthly_objs.filter.return_value.exists.return_value = False
    with pytest.raises(Http404):
        views.summaries_monthly_csv(rf.get("/"), 1990, 1)


@patch("api.views.models.MonthlySummary.objects")
def test_monthly_csv_download(
    monthly_objs: MagicMock, rf: RequestFactory, sample_csv_path: Path
) -> None:
    summary = SimpleNamespace(csv_filepath=str(sample_csv_path))
    monthly_objs.filter.return_value.exists.return_value = True
    monthly_objs.filter.return_value.first.return_value = summary
    response = views.summaries_monthly_csv(rf.get("/"), 2020, 1)
    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv"
    assert b"DATE,TX" in response.content


@patch("api.views.render", side_effect=_ok)
@patch("api.views.models.MonthlySummary.objects")
def test_edit_remarks_wrong_password(
    monthly_objs: MagicMock,
    mock_render: MagicMock,
    rf: RequestFactory,
    site_pass: str,
) -> None:
    monthly_objs.filter.return_value.exists.return_value = True
    monthly_objs.filter.return_value.first.return_value = SimpleNamespace(remarks="old")
    request = rf.post("/", {"remarks": "x", "password": "wrong"})
    views.summaries_monthly_view(request, 2020, 1)
    ctx = _render_context(mock_render)
    assert any("Incorrect password" in a["body"] for a in ctx["alerts"])


@patch("api.views.render", side_effect=_ok)
@patch("api.views.models.MonthlySummary.objects")
def test_edit_remarks_success(
    monthly_objs: MagicMock,
    mock_render: MagicMock,
    rf: RequestFactory,
    site_pass: str,
) -> None:
    summary = MagicMock(remarks="old")
    monthly_objs.filter.return_value.exists.return_value = True
    monthly_objs.filter.return_value.first.return_value = summary
    request = rf.post("/", {"remarks": "updated", "password": site_pass})
    views.summaries_monthly_view(request, 2020, 1)
    assert summary.remarks == "updated"
    summary.save.assert_called_once()
    ctx = _render_context(mock_render)
    assert any("remarks saved" in a["body"] for a in ctx["alerts"])


@patch("api.views.render", side_effect=_ok)
@patch("api.views.models.MonthlySummary.objects")
def test_edit_remarks_missing_summary(
    monthly_objs: MagicMock,
    mock_render: MagicMock,
    rf: RequestFactory,
    site_pass: str,
) -> None:
    monthly_objs.filter.return_value.first.return_value = None
    monthly_objs.filter.return_value.exists.return_value = False
    request = rf.post("/", {"remarks": "x", "password": site_pass})
    views.summaries_monthly_view(request, 1988, 3)
    ctx = _render_context(mock_render)
    assert any("Summary not found" in a["body"] for a in ctx["alerts"])


@patch("api.views.render", side_effect=_ok)
def test_submit_invalid_form(mock_render: MagicMock, rf: RequestFactory) -> None:
    views.summaries_monthly_submit(rf.post("/", {}))
    ctx = _render_context(mock_render)
    assert any("Form data invalid" in a["body"] for a in ctx["alerts"])


@patch("api.views.render", side_effect=_ok)
def test_submit_wrong_password(
    mock_render: MagicMock, rf: RequestFactory, site_pass: str
) -> None:
    upload = SimpleUploadedFile("obs.csv", b"DATE,TX\n", content_type="text/csv")
    request = rf.post("/", {"password": "nope", "csv_file": upload})
    views.summaries_monthly_submit(request)
    ctx = _render_context(mock_render)
    assert any("Incorrect password" in a["body"] for a in ctx["alerts"])


@patch("api.views.render", side_effect=_ok)
@patch("api.views.utils.calc_annual_summary")
@patch("api.views.utils.calc_monthly_summary")
@patch("api.views.utils.process_csv", return_value=(2020, 1))
def test_submit_happy_path(
    process_csv: MagicMock,
    calc_monthly: MagicMock,
    calc_annual: MagicMock,
    mock_render: MagicMock,
    rf: RequestFactory,
    site_pass: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "static" / "csv").mkdir(parents=True)
    monkeypatch.setattr("api.views.BASE_DIR", tmp_path)
    upload = SimpleUploadedFile("jan.csv", b"DATE,TX\n", content_type="text/csv")
    request = rf.post("/", {"password": site_pass, "csv_file": upload})
    views.summaries_monthly_submit(request)
    process_csv.assert_called_once()
    calc_monthly.assert_called_once_with(2020, 1, save_to_db=True)
    calc_annual.assert_called_once_with(2020, save_to_db=True)
    ctx = _render_context(mock_render)
    assert any("successfully processed" in a["body"] for a in ctx["alerts"])


@patch("api.views.render", side_effect=_ok)
@patch("api.views.utils.process_csv", side_effect=ValueError("bad csv"))
def test_submit_csv_processing_error(
    _process: MagicMock,
    mock_render: MagicMock,
    rf: RequestFactory,
    site_pass: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "static" / "csv").mkdir(parents=True)
    monkeypatch.setattr("api.views.BASE_DIR", tmp_path)
    upload = SimpleUploadedFile("bad.csv", b"x\n", content_type="text/csv")
    request = rf.post("/", {"password": site_pass, "csv_file": upload})
    views.summaries_monthly_submit(request)
    ctx = _render_context(mock_render)
    assert any("processing csv" in a["body"] for a in ctx["alerts"])


@patch("api.views.render", side_effect=_ok)
@patch("api.views.utils.calc_monthly_summary", side_effect=RuntimeError("boom"))
@patch("api.views.utils.process_csv", return_value=(2020, 1))
def test_submit_calc_error(
    _process: MagicMock,
    _calc: MagicMock,
    mock_render: MagicMock,
    rf: RequestFactory,
    site_pass: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "static" / "csv").mkdir(parents=True)
    monkeypatch.setattr("api.views.BASE_DIR", tmp_path)
    upload = SimpleUploadedFile("jan.csv", b"x\n", content_type="text/csv")
    request = rf.post("/", {"password": site_pass, "csv_file": upload})
    views.summaries_monthly_submit(request)
    ctx = _render_context(mock_render)
    assert any("calculating summary" in a["body"] for a in ctx["alerts"])


@patch("api.views.render", side_effect=_ok)
@patch("api.views.models.AnnualSummary.objects")
@patch("api.views.models.MonthlySummary.objects")
def test_annual_view_missing_and_present(
    monthly_objs: MagicMock,
    annual_objs: MagicMock,
    mock_render: MagicMock,
    rf: RequestFactory,
) -> None:
    annual_objs.filter.return_value.exists.return_value = False
    views.summaries_annual_view(rf.get("/"), 1991)
    assert any(a["color"] == "warning" for a in _render_context(mock_render)["alerts"])

    annual = SimpleNamespace(year=2020)
    annual_objs.filter.return_value.exists.return_value = True
    annual_objs.filter.return_value.first.return_value = annual
    monthly_objs.filter.return_value.order_by.return_value = []
    views.summaries_annual_view(rf.get("/"), 2020)
    assert _render_context(mock_render)["annual_summary"] == annual


@patch("api.views.models.AnnualSummary.objects")
def test_annual_text_404(annual_objs: MagicMock, rf: RequestFactory) -> None:
    annual_objs.filter.return_value.exists.return_value = False
    with pytest.raises(Http404):
        views.summaries_annual_text(rf.get("/"), 1991)


@patch("api.views.render", side_effect=_ok)
@patch("api.views.utils.get_normals")
@patch("api.views.models.AnnualSummary.objects")
def test_annual_text_ok(
    annual_objs: MagicMock,
    get_normals: MagicMock,
    mock_render: MagicMock,
    rf: RequestFactory,
) -> None:
    annual_objs.filter.return_value.exists.return_value = True
    annual_objs.filter.return_value.first.return_value = SimpleNamespace()
    get_normals.return_value = {"temp": [0] * 13, "precip": [0] * 13, "sf": [0] * 13}
    views.summaries_annual_text(rf.get("/"), 2020)
    assert "annual_summary" in _render_context(mock_render)


@patch("api.views.render", side_effect=_ok)
@patch("api.views.models.AnnualSummary.objects")
@patch("api.views.models.MonthlySummary.objects")
def test_annual_table(
    monthly_objs: MagicMock,
    annual_objs: MagicMock,
    mock_render: MagicMock,
    rf: RequestFactory,
) -> None:
    annual_objs.filter.return_value.exists.return_value = False
    with pytest.raises(Http404):
        views.summaries_annual_table(rf.get("/"), 1991)

    annual_objs.filter.return_value.exists.return_value = True
    annual_objs.filter.return_value.first.return_value = SimpleNamespace(year=2020)
    monthly_objs.filter.return_value.order_by.return_value = [SimpleNamespace()]
    views.summaries_annual_table(rf.get("/"), 2020)
    assert len(_render_context(mock_render)["all_summaries"]) == 2


@patch("api.views.render", side_effect=_ok)
@patch("api.views.models.SnowSeason.objects")
@patch("api.views.models.PeakFoliage.objects")
@patch("api.views.models.SunsetLakeIceInIceOut.objects")
@patch("api.views.models.MonthlySummary.objects")
def test_list_pages(
    monthly_objs: MagicMock,
    lake_objs: MagicMock,
    peak_objs: MagicMock,
    snow_objs: MagicMock,
    mock_render: MagicMock,
    rf: RequestFactory,
) -> None:
    snow_objs.all.return_value.order_by.return_value = ["s"]
    peak_objs.all.return_value.order_by.return_value = ["p"]
    lake_objs.all.return_value.order_by.return_value = ["l"]
    monthly_objs.all.return_value.order_by.return_value = ["m"]
    snow_objs.filter.return_value.first.return_value = "season-row"

    views.summaries_snowseason_view(rf.get("/"))
    assert _render_context(mock_render)["summaries"] == ["s"]

    views.summaries_snowseason_season(rf.get("/"), "2019-2020")
    assert _render_context(mock_render)["summary"] == "season-row"

    views.summaries_peakfoliage_view(rf.get("/"))
    assert _render_context(mock_render)["peaks"] == ["p"]

    views.summaries_sunsetlake_view(rf.get("/"))
    assert _render_context(mock_render)["summaries"] == ["l"]

    views.summaries_precip_view(rf.get("/"))
    assert _render_context(mock_render)["summaries"] == ["m"]


@patch("api.views.render", side_effect=lambda *_a, **_k: HttpResponse(status=404))
def test_handler404(mock_render: MagicMock, rf: RequestFactory) -> None:
    assert views.handler404(rf.get("/missing")).status_code == 404


@patch("api.views.render", side_effect=lambda *_a, **_k: HttpResponse(status=500))
def test_handler500(mock_render: MagicMock, rf: RequestFactory) -> None:
    assert views.handler500(rf.get("/")).status_code == 500
