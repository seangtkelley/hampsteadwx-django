"""Unit tests for admin form customization (no DB required)."""

import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

from api.admin import SnowSeasonAdmin, SunsetLakeIceInIceOutAdmin
from api.models import SnowSeason, SunsetLakeIceInIceOut

pytestmark = pytest.mark.unit


def test_snowseason_admin_get_form_sets_season_placeholder() -> None:
    request = RequestFactory().get("/admin/api/snowseason/add/")
    admin = SnowSeasonAdmin(SnowSeason, AdminSite())

    form_class = admin.get_form(request)

    season_widget = form_class.base_fields["season"].widget
    assert season_widget.attrs["placeholder"] == "Ex: 2020-2021"


def test_sunsetlake_admin_get_form_sets_season_and_duration_widgets() -> None:
    request = RequestFactory().get("/admin/api/sunsetlakeiceiniceout/add/")
    admin = SunsetLakeIceInIceOutAdmin(SunsetLakeIceInIceOut, AdminSite())

    form_class = admin.get_form(request)

    season_widget = form_class.base_fields["season"].widget
    duration_widget = form_class.base_fields["duration"].widget
    assert season_widget.attrs["placeholder"] == "Ex: 2020-2021"
    assert duration_widget.attrs["title"] == "days"
