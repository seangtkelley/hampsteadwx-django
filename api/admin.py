from django.contrib import admin
from django import forms

from .models import DailyOb, MonthlySummary, AnnualSummary, SunsetLakeIceInIceOut, SnowSeason, PeakFoliage


@admin.register(DailyOb)
class DailyObAdmin(admin.ModelAdmin):
    list_display = ['date']


@admin.register(MonthlySummary)
class MonthlySummaryAdmin(admin.ModelAdmin):
    list_display = ['get_name']

    def get_name(self, obj):
        return obj.date.strftime('%B %Y')


@admin.register(AnnualSummary)
class AnnualSummaryAdmin(admin.ModelAdmin):
    list_display = ['year']


@admin.register(PeakFoliage)
class PeakFoliageAdmin(admin.ModelAdmin):
    list_display = ['date']


@admin.register(SnowSeason)
class SnowSeasonAdmin(admin.ModelAdmin):
    list_display = ['season']

    def get_form(self, request, obj=None, **kwargs):
        kwargs['widgets'] = {
            'season': forms.TextInput(attrs={'placeholder': 'Ex: 2020-2021'})
        }
        return super().get_form(request, obj, **kwargs)


@admin.register(SunsetLakeIceInIceOut)
class SunsetLakeIceInIceOutAdmin(admin.ModelAdmin):
    list_display = ['season']

    def get_form(self, request, obj=None, **kwargs):
        kwargs['widgets'] = {
            'season': forms.TextInput(attrs={'placeholder': 'Ex: 2020-2021'}),
            'duration': forms.NumberInput(attrs={'title': 'days'})
        }
        return super().get_form(request, obj, **kwargs)