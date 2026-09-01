"""Integration tests for bulk_recalc against PostgreSQL."""

from datetime import date
from decimal import Decimal

import pytest
from django.core.management import call_command

from api.models import MonthlySummary
from tests.conftest import general_summary_defaults
from tests.integration.conftest import make_daily_ob

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def test_bulk_recalc_updates_summary() -> None:
    make_daily_ob(
        date(2013, 2, 1),
        max_temp="30",
        min_temp="10",
        precip="0.2",
    )
    MonthlySummary.objects.create(
        date=date(2013, 2, 1),
        remarks="old",
        csv_filepath="/x.csv",
        precip_todate=Decimal("0"),
        precip_todate_dfn=Decimal("0"),
        sf_todate=Decimal("0"),
        sf_todate_dfn=Decimal("0"),
        **general_summary_defaults(precip=Decimal("99.0")),
    )
    call_command("bulk_recalc", months=[2], years=[2013])
    summary = MonthlySummary.objects.get(date=date(2013, 2, 1))
    assert summary.precip == Decimal("0.2")
    assert summary.remarks == "old"
