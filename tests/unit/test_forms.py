"""Unit tests for forms (no database)."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from api.forms import EditRemarks, SubmitMonthlyCSV

pytestmark = pytest.mark.unit


def test_submit_monthly_csv_valid() -> None:
    upload = SimpleUploadedFile("obs.csv", b"DATE,TX\n", content_type="text/csv")
    form = SubmitMonthlyCSV(
        data={"password": "secret"},
        files={"csv_file": upload},
    )
    assert form.is_valid()


def test_submit_monthly_csv_missing_file() -> None:
    form = SubmitMonthlyCSV(data={"password": "secret"})
    assert not form.is_valid()
    assert "csv_file" in form.errors


def test_edit_remarks_valid() -> None:
    form = EditRemarks(data={"remarks": "Nice month", "password": "secret"})
    assert form.is_valid()


def test_edit_remarks_missing_fields() -> None:
    form = EditRemarks(data={})
    assert not form.is_valid()
    assert "remarks" in form.errors
    assert "password" in form.errors
