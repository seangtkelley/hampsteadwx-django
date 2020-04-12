from django.db import models
from django.contrib.postgres.fields import ArrayField

class DailyOb(models.Model):
    date = models.DateField()
    max_temp = models.DecimalField(max_digits=8, decimal_places=1)
    min_temp = models.DecimalField(max_digits=8, decimal_places=1)
    atob_temp = models.DecimalField(max_digits=8, decimal_places=1)
    precip = models.DecimalField(max_digits=8, decimal_places=2)
    snowfall = models.DecimalField(max_digits=8, decimal_places=1)
    snowdepth = models.DecimalField(max_digits=8, decimal_places=1)

class MonthlyOb(models.Model):
    # meta
    date = models.DateField()
    remarks = models.TextField()
    csv_filepath = models.CharField(max_length=512)

    # abrv key:
    # grtr = greater
    # grtst = greatest
    # hdd = heating degree days
    # cdd = cooling degree days

    # temp fields
    max_temp = models.DecimalField(max_digits=8, decimal_places=1)
    max_temp_dates = ArrayField(
        ArrayField(models.DateField())
    )
    max_temp_avg = models.DecimalField(max_digits=8, decimal_places=1)
    max_temp_grtr90_count = models.IntegerField()
    max_temp_less32_count = models.IntegerField()

    min_temp = models.DecimalField(max_digits=8, decimal_places=1)
    min_temp_dates = ArrayField(
        ArrayField(models.DateField())
    )
    min_temp_avg = models.DecimalField(max_digits=8, decimal_places=1)
    min_temp_less32_count = models.IntegerField()
    min_temp_less0_count = models.IntegerField()

    avg_temp = models.DecimalField(max_digits=8, decimal_places=1)
    avg_dfn = models.DecimalField(max_digits=8, decimal_places=1)

    hdd_count = models.IntegerField()
    cdd_count = models.IntegerField()

    # precip fields
    precip = models.DecimalField(max_digits=8, decimal_places=2)
    precip_todate = models.DecimalField(max_digits=8, decimal_places=2)
    precip_todate_dfn = models.DecimalField(max_digits=8, decimal_places=2)
    
    grtst_precip = models.DecimalField(max_digits=8, decimal_places=2)
    grtst_precip_dates = ArrayField(
        ArrayField(models.DateField())
    )
    precip_grtrT = models.IntegerField() # trace (T)
    precip_grtr01 = models.IntegerField() # 01 = 0.01"
    precip_grtr10 = models.IntegerField() # 10 = 0.10"
    precip_grtr50 = models.IntegerField()
    precip_grtr100 = models.IntegerField()

    # snowfall and snowdepth fields
    sf = models.DecimalField(max_digits=8, decimal_places=1)

    sf_todate = models.DecimalField(max_digits=8, decimal_places=1)
    sf_todate_dfn = models.DecimalField(max_digits=8, decimal_places=1)

    grtst_sf = models.DecimalField(max_digits=8, decimal_places=1)
    grtst_sf_dates = ArrayField(
        ArrayField(models.DateField())
    )
    sf_grtrT = models.IntegerField()
    sf_grtr50 = models.IntegerField() # 50 = 0.50"
    sf_grtr100 = models.IntegerField() # 100 = 1.00"
    sf_grtr500 = models.IntegerField()
    sf_grtr1000 = models.IntegerField()

    grtst_sd = models.DecimalField(max_digits=8, decimal_places=1)
    grtst_sd_dates = ArrayField(
        ArrayField(models.DateField())
    )
    sd_grtrT = models.IntegerField()
    sd_grtr50 = models.IntegerField() # 50 = 0.50"
    sd_grtr100 = models.IntegerField() # 100 = 1.00"
    sd_grtr500 = models.IntegerField()
    sd_grtr1000 = models.IntegerField()


class SunsetLakeIceInIceOut(models.Model):
    season = models.CharField(max_length=16)
    icein_date = models.DateField()
    iceout_date = models.DateField()
    duration = models.IntegerField()


class SnowSeason(models.Model):
    date = models.DateField()
    season = models.CharField(max_length=16)
    oct = models.DecimalField(max_digits=8, decimal_places=1)
    nov = models.DecimalField(max_digits=8, decimal_places=1)
    dec = models.DecimalField(max_digits=8, decimal_places=1)
    jan = models.DecimalField(max_digits=8, decimal_places=1)
    feb = models.DecimalField(max_digits=8, decimal_places=1)
    mar = models.DecimalField(max_digits=8, decimal_places=1)
    apr = models.DecimalField(max_digits=8, decimal_places=1)
    may = models.DecimalField(max_digits=8, decimal_places=1)


class PeakFoliage(models.Model):
    date = models.DateField()


class Photo(models.Model):
    url = models.CharField(max_length=256)
    caption = models.CharField(max_length=256)