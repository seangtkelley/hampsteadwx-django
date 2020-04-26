from django.contrib import admin

from .models import DailyOb, MonthlyOb, SunsetLakeIceInIceOut, SnowSeason, PeakFoliage, Photo

admin.site.register(DailyOb)
admin.site.register(MonthlyOb)
admin.site.register(SunsetLakeIceInIceOut)
admin.site.register(SnowSeason)
admin.site.register(PeakFoliage)
admin.site.register(Photo)