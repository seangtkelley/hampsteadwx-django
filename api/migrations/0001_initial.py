# Generated by Django 3.0.5 on 2020-05-26 02:57

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DailyOb',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('csv_filepath', models.CharField(max_length=512)),
                ('max_temp', models.DecimalField(decimal_places=1, max_digits=8)),
                ('min_temp', models.DecimalField(decimal_places=1, max_digits=8)),
                ('atob_temp', models.DecimalField(decimal_places=1, max_digits=8)),
                ('precip', models.DecimalField(decimal_places=3, max_digits=8)),
                ('snowfall', models.DecimalField(decimal_places=3, max_digits=8)),
                ('snowdepth', models.DecimalField(decimal_places=3, max_digits=8)),
            ],
        ),
        migrations.CreateModel(
            name='GeneralSummary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('max_temp', models.DecimalField(decimal_places=1, max_digits=8)),
                ('max_temp_dates', django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.ArrayField(base_field=models.DateField(), size=None), size=None)),
                ('max_temp_avg', models.DecimalField(decimal_places=1, max_digits=8)),
                ('max_temp_grtr90_count', models.IntegerField()),
                ('max_temp_less32_count', models.IntegerField()),
                ('min_temp', models.DecimalField(decimal_places=1, max_digits=8)),
                ('min_temp_dates', django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.ArrayField(base_field=models.DateField(), size=None), size=None)),
                ('min_temp_avg', models.DecimalField(decimal_places=1, max_digits=8)),
                ('min_temp_less32_count', models.IntegerField()),
                ('min_temp_less0_count', models.IntegerField()),
                ('avg_temp', models.DecimalField(decimal_places=1, max_digits=8)),
                ('avg_temp_dfn', models.DecimalField(decimal_places=1, max_digits=8)),
                ('hdd_count', models.IntegerField()),
                ('cdd_count', models.IntegerField()),
                ('precip', models.DecimalField(decimal_places=3, max_digits=8)),
                ('precip_dfn', models.DecimalField(decimal_places=3, max_digits=8)),
                ('grtst_precip', models.DecimalField(decimal_places=3, max_digits=8)),
                ('grtst_precip_dates', django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.ArrayField(base_field=models.DateField(), size=None), size=None)),
                ('precip_grtrT', models.IntegerField()),
                ('precip_grtr01', models.IntegerField()),
                ('precip_grtr10', models.IntegerField()),
                ('precip_grtr50', models.IntegerField()),
                ('precip_grtr100', models.IntegerField()),
                ('sf', models.DecimalField(decimal_places=3, max_digits=8)),
                ('sf_dfn', models.DecimalField(decimal_places=3, max_digits=8)),
                ('grtst_sf', models.DecimalField(decimal_places=3, max_digits=8)),
                ('grtst_sf_dates', django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.ArrayField(base_field=models.DateField(), size=None), size=None)),
                ('sf_grtrT', models.IntegerField()),
                ('sf_grtr1', models.IntegerField()),
                ('sf_grtr3', models.IntegerField()),
                ('sf_grtr6', models.IntegerField()),
                ('sf_grtr12', models.IntegerField()),
                ('sf_grtr18', models.IntegerField()),
                ('grtst_sd', models.DecimalField(decimal_places=3, max_digits=8)),
                ('grtst_sd_dates', django.contrib.postgres.fields.ArrayField(base_field=django.contrib.postgres.fields.ArrayField(base_field=models.DateField(), size=None), size=None)),
                ('sd_grtrT', models.IntegerField()),
                ('sd_grtr1', models.IntegerField()),
                ('sd_grtr3', models.IntegerField()),
                ('sd_grtr6', models.IntegerField()),
                ('sd_grtr12', models.IntegerField()),
                ('sd_grtr18', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='PeakFoliage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='SnowSeason',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('season', models.CharField(max_length=16)),
                ('oct', models.DecimalField(decimal_places=3, max_digits=8)),
                ('nov', models.DecimalField(decimal_places=3, max_digits=8)),
                ('dec', models.DecimalField(decimal_places=3, max_digits=8)),
                ('jan', models.DecimalField(decimal_places=3, max_digits=8)),
                ('feb', models.DecimalField(decimal_places=3, max_digits=8)),
                ('mar', models.DecimalField(decimal_places=3, max_digits=8)),
                ('apr', models.DecimalField(decimal_places=3, max_digits=8)),
                ('may', models.DecimalField(decimal_places=3, max_digits=8)),
                ('total', models.DecimalField(decimal_places=1, max_digits=8)),
            ],
        ),
        migrations.CreateModel(
            name='SunsetLakeIceInIceOut',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('season', models.CharField(max_length=16)),
                ('icein_date', models.DateField()),
                ('iceout_date', models.DateField()),
                ('duration', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='AnnualSummary',
            fields=[
                ('generalsummary_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='api.GeneralSummary')),
                ('year', models.IntegerField()),
            ],
            bases=('api.generalsummary',),
        ),
        migrations.CreateModel(
            name='MonthlySummary',
            fields=[
                ('generalsummary_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='api.GeneralSummary')),
                ('date', models.DateField()),
                ('remarks', models.TextField()),
                ('csv_filepath', models.CharField(max_length=512)),
                ('precip_todate', models.DecimalField(decimal_places=3, max_digits=8)),
                ('precip_todate_dfn', models.DecimalField(decimal_places=3, max_digits=8)),
                ('sf_todate', models.DecimalField(decimal_places=3, max_digits=8)),
                ('sf_todate_dfn', models.DecimalField(decimal_places=3, max_digits=8)),
            ],
            bases=('api.generalsummary',),
        ),
    ]
