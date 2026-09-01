"""Integration tests: HTTP client against PostgreSQL-backed views."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

from api.models import MonthlySummary
from tests.integration.conftest import make_daily_obs_for_month

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


@pytest.fixture
def client() -> Client:
    return Client()


def test_monthly_view_and_remarks(
    client: Client, monthly_summary: MonthlySummary, site_pass: str
) -> None:
    make_daily_obs_for_month(2020, 1, days=1)
    response = client.get(
        reverse("summaries_monthly_view", kwargs={"year": 2020, "month": 1})
    )
    assert response.status_code == 200
    assert response.context["monthly_summary"] == monthly_summary

    saved = client.post(
        reverse("summaries_monthly_view", kwargs={"year": 2020, "month": 1}),
        {"remarks": "updated remarks", "password": site_pass},
    )
    assert b"remarks saved" in saved.content
    monthly_summary.refresh_from_db()
    assert monthly_summary.remarks == "updated remarks"


def test_monthly_csv_download(
    client: Client, monthly_summary: MonthlySummary, sample_csv_path: Path
) -> None:
    monthly_summary.csv_filepath = str(sample_csv_path)
    monthly_summary.save()
    response = client.get(
        reverse("summaries_monthly_csv", kwargs={"year": 2020, "month": 1})
    )
    assert response.status_code == 200
    assert "attachment" in response["Content-Disposition"]


def test_submit_happy_path(
    client: Client,
    site_pass: str,
    sample_csv_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "static" / "csv").mkdir(parents=True)
    monkeypatch.setattr("api.views.BASE_DIR", tmp_path)
    upload = SimpleUploadedFile(
        "jan2020.csv", sample_csv_path.read_bytes(), content_type="text/csv"
    )
    response = client.post(
        reverse("summaries_monthly_submit"),
        {"password": site_pass, "csv_file": upload},
    )
    assert b"successfully processed" in response.content
    assert MonthlySummary.objects.filter(date=date(2020, 1, 1)).exists()


def test_list_and_annual_pages(
    client: Client,
    annual_summary,
    monthly_summary: MonthlySummary,
    snow_season,
    peak_foliage,
    sunset_lake,
) -> None:
    assert (
        client.get(reverse("summaries_annual_view", kwargs={"year": 2020})).status_code
        == 200
    )
    assert (
        client.get(reverse("summaries_annual_text", kwargs={"year": 2020})).status_code
        == 200
    )
    assert (
        client.get(reverse("summaries_annual_table", kwargs={"year": 2020})).status_code
        == 200
    )
    assert client.get(reverse("summaries_snowseason_view")).status_code == 200
    assert (
        client.get(
            reverse("summaries_snowseason_season", kwargs={"season": "2019-2020"})
        ).status_code
        == 200
    )
    assert client.get(reverse("summaries_peakfoliage_view")).status_code == 200
    assert client.get(reverse("summaries_sunsetlake_view")).status_code == 200
    assert client.get(reverse("summaries_precip_view")).status_code == 200
