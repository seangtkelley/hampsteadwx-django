"""Django admin configuration for API models."""

from django import forms
from django.contrib import admin
from django.forms import ModelForm
from django.http import HttpRequest

from .models import (
    AnnualSummary,
    DailyOb,
    MonthlySummary,
    PeakFoliage,
    SnowSeason,
    SunsetLakeIceInIceOut,
)


@admin.register(DailyOb)
class DailyObAdmin(admin.ModelAdmin):
    """Admin interface for daily weather observations."""

    list_display = ("date",)


@admin.register(MonthlySummary)
class MonthlySummaryAdmin(admin.ModelAdmin):
    """Admin interface for monthly climate summaries."""

    list_display = ("get_name",)

    @admin.display(description="Name")
    def get_name(self, obj: MonthlySummary) -> str:
        """Return a human-readable month and year label."""
        return obj.date.strftime("%B %Y")


@admin.register(AnnualSummary)
class AnnualSummaryAdmin(admin.ModelAdmin):
    """Admin interface for annual climate summaries."""

    list_display = ("year",)


@admin.register(PeakFoliage)
class PeakFoliageAdmin(admin.ModelAdmin):
    """Admin interface for peak foliage dates."""

    list_display = ("date",)


@admin.register(SnowSeason)
class SnowSeasonAdmin(admin.ModelAdmin):
    """Admin interface for snow season totals."""

    list_display = ("season",)

    def get_form(
        self,
        request: HttpRequest,
        obj: SnowSeason | None = None,
        change: bool = False,
        **kwargs: object,
    ) -> type[ModelForm]:
        """Customize the admin form with a season placeholder.

        Returns:
            Model form class configured for snow season entry.
        """
        kwargs["widgets"] = {
            "season": forms.TextInput(attrs={"placeholder": "Ex: 2020-2021"})
        }
        return super().get_form(request, obj, change, **kwargs)


@admin.register(SunsetLakeIceInIceOut)
class SunsetLakeIceInIceOutAdmin(admin.ModelAdmin):
    """Admin interface for Sunset Lake ice-in/ice-out records."""

    list_display = ("season",)

    def get_form(
        self,
        request: HttpRequest,
        obj: SunsetLakeIceInIceOut | None = None,
        change: bool = False,
        **kwargs: object,
    ) -> type[ModelForm]:
        """Customize the admin form with season and duration widgets.

        Returns:
            Model form class configured for ice-in/ice-out entry.
        """
        kwargs["widgets"] = {
            "season": forms.TextInput(attrs={"placeholder": "Ex: 2020-2021"}),
            "duration": forms.NumberInput(attrs={"title": "days"}),
        }
        return super().get_form(request, obj, change, **kwargs)
