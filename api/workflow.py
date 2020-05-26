import os
from decimal import Decimal
from datetime import datetime

import numpy as np
import pandas as pd
from django.db.models import Sum

from . import models
from boilerplate.settings import BASE_DIR, TRACE_VAL


def get_normals():
    normals = {}
    filepath = os.path.join(BASE_DIR, 'assets', 'csv', 'HMPN3-Monthly-Climate-Normals.csv')
    with open(filepath) as f:
        lines = f.readlines()
        normals['temp'] = list(map(Decimal, lines[0].split(',')))
        normals['precip'] = list(map(Decimal, lines[1].split(',')))
        normals['sf'] = list(map(Decimal, lines[2].split(',')))

    return normals


def process_csv(filepath):
    # load file
    df = pd.read_csv(filepath, parse_dates=['DATE'])

    # save daily obs
    for _, row in df.iterrows():
        # check if ob exists
        if models.DailyOb.objects.filter(date=row['DATE'].date()).exists():
            ob = models.DailyOb.objects.filter(date=row['DATE'].date()).first()
            ob.csv_filepath = filepath
            ob.max_temp = Decimal(row['TX'])
            ob.min_temp = Decimal(row['TN'])
            ob.atob_temp = Decimal(row['TA'])

            # 0.001 for trace values
            ob.precip = Decimal(TRACE_VAL) if row['PP'] == 'T' else Decimal(row['PP'])
            ob.snowfall = Decimal(TRACE_VAL) if row['SF'] == 'T' else Decimal(row['SF'])
            ob.snowdepth = Decimal(TRACE_VAL) if row['SD'] == 'T' else Decimal(row['SD'])
            
            ob.save()
        else:
            ob = models.DailyOb(
                date=row['DATE'].date(),
                csv_filepath=filepath,
                max_temp=Decimal(row['TX']),
                min_temp=Decimal(row['TN']),
                atob_temp=Decimal(row['TA']),

                # 0.001 for trace values
                precip=Decimal(TRACE_VAL) if row['PP'] == 'T' else Decimal(row['PP']),
                snowfall=Decimal(TRACE_VAL) if row['SF'] == 'T' else Decimal(row['SF']),
                snowdepth=Decimal(TRACE_VAL) if row['SD'] == 'T' else Decimal(row['SD'])
            )

            ob.save()

    return df.iloc[0]['DATE'].year, df.iloc[0]['DATE'].month


def calc_monthly_summary(year, month, save_to_db=False):
    # get all daily obs from month
    obs = models.DailyOb.objects.filter(date__year=year, date__month=month).order_by('date')
    if obs.count() == 0:
        return None

    # convert to dataframe
    df = pd.DataFrame.from_records(obs.values())

    # calc general
    summary = calc_general_summary(df)

    # add meta
    summary['csv_filepath'] = df.iloc[0].csv_filepath

    # add month specific fields
    normals = get_normals()
    summary['avg_temp_dfn'] = summary['avg_temp'] - normals['temp'][month-1]
    summary['precip_dfn'] = summary['precip'] - normals['precip'][month-1]
    summary['sf_dfn'] = summary['sf'] - normals['sf'][month-1]

    # precip to date
    precip_todate = models.DailyOb.objects.filter(date__year=year, date__month__in=list(range(1, month+1))).exclude(precip=TRACE_VAL).aggregate(Sum('precip'))['precip__sum'] # sum over all precip except traces
    summary['precip_todate'] = precip_todate
    summary['precip_todate_dfn'] = precip_todate - sum(normals['precip'][:month])

    # snowfall to date
    if month >= 10:
        summary['sf_todate'] = models.DailyOb.objects.filter(date__year=year, date__month__in=list(range(10, month+1))).exclude(snowfall=TRACE_VAL).aggregate(Sum('snowfall'))['snowfall__sum'] # same as above

        summary['sf_todate_dfn'] = summary['sf_todate'] - sum(normals['sf'][9:month])

    elif month <= 5:
        # get last year's snow
        prev_year_sf = models.DailyOb.objects.filter(date__year=year-1, date__month__in=[10, 11, 12]).exclude(snowfall=TRACE_VAL).aggregate(Sum('snowfall'))['snowfall__sum']
        summary['sf_todate'] = 0 if not prev_year_sf else prev_year_sf # small check if we don't have prev year snowfall
        
        # get this year's snow
        summary['sf_todate'] += models.DailyOb.objects.filter(date__year=year, date__month__in=list(range(1, month+1))).exclude(snowfall=TRACE_VAL).aggregate(Sum('snowfall'))['snowfall__sum']

        summary['sf_todate_dfn'] = summary['sf_todate'] - sum(normals['sf'][9:12]) - sum(normals['sf'][:month])
    else:
        summary['sf_todate'] = 0
        summary['sf_todate_dfn'] = 0
    
    if save_to_db:
        if models.MonthlySummary.objects.filter(date=summary['date']).exists():
            db_summary = models.MonthlySummary.objects.filter(date=summary['date']).update(**summary)
        else:
            db_summary = models.MonthlySummary.objects.create(**summary)
        
        return db_summary
    else:
        return summary


def get_all_monthly_summaries():
    all_summaries = []
    for year in range(2010, datetime.now().year+1):
        for month in range(1, 13):
            if models.MonthlySummary.objects.filter(date__year=year, date__month=month).exists():
                # from database
                all_summaries.append(models.MonthlySummary.objects.filter(date__year=year, date__month=month).first())
            elif models.DailyOb.objects.filter(date__year=year, date__month=month).count() > 0:
                # calc
                all_summaries.append(calc_monthly_summary(year, month))
    return all_summaries


def calc_annual_summary(year):
    # get all daily obs from year
    obs = models.DailyOb.objects.filter(date__year=year).order_by('date')
    if obs.count() == 0:
        return None

    # convert to dataframe
    df = pd.DataFrame.from_records(obs.values())

    # calc general
    summary = calc_general_summary(df)

    # add annual specific fields
    normals = get_normals()
    summary['avg_temp_dfn'] = summary['avg_temp'] - normals['temp'][12]
    summary['precip_dfn'] = summary['precip'] - normals['precip'][12]
    summary['sf_dfn'] = summary['sf'] - normals['sf'][12]

    return summary


def calc_general_summary(df):
    return {
        'date': df.iloc[0].date,

        # abrv key:
        # grtr = greater
        # grtst = greatest
        # hdd = heating degree days
        # cdd = cooling degree days

        # temp fields
        'max_temp': Decimal(df.max_temp.max()),
        'max_temp_dates': list(df[df.max_temp == df.max_temp.max()].date),
        'max_temp_avg': Decimal(df.max_temp.mean()),
        'max_temp_grtr90_count': len(df[df.max_temp > 90]),
        'max_temp_less32_count': len(df[df.max_temp < 32]),

        'min_temp': Decimal(df.min_temp.min()),
        'min_temp_dates': list(df[df.min_temp == df.min_temp.min()].date),
        'min_temp_avg': Decimal(df.min_temp.mean()),
        'min_temp_less32_count': len(df[df.min_temp < 32]),
        'min_temp_less0_count': len(df[df.min_temp < 0]),

        'avg_temp': Decimal(df[['max_temp', 'min_temp']].mean(axis=1).mean()),

        'hdd_count': round(sum(df[(df[['max_temp', 'min_temp']].mean(axis=1) - 65) > 0][['max_temp', 'min_temp']].mean(axis=1) - 65)),
        'cdd_count': abs(round(sum(df[(df[['max_temp', 'min_temp']].mean(axis=1) - 65) < 0][['max_temp', 'min_temp']].mean(axis=1) - 65))),

        # precip fields
        'precip': TRACE_VAL if Decimal(df.precip.max()) == TRACE_VAL else Decimal(sum(df[df.precip != TRACE_VAL].precip)),
        
        'grtst_precip': Decimal(df.precip.max()),
        'grtst_precip_dates': [] if df.precip.max() == 0 else list(df[df.precip == df.precip.max()].date),
        'precip_grtrT': len(df[df.precip > TRACE_VAL]), # trace (T)
        'precip_grtr01': len(df[df.precip > 0.01]), # 01 = 0.01"
        'precip_grtr10': len(df[df.precip > 0.10]), # 10 = 0.10"
        'precip_grtr50': len(df[df.precip > 0.50]),
        'precip_grtr100': len(df[df.precip > 1.00]),

        # snowfall and snowdepth fields
        'sf': TRACE_VAL if Decimal(df.snowfall.max()) == TRACE_VAL else Decimal(sum(df[df.snowfall != TRACE_VAL].snowfall)),

        'grtst_sf': Decimal(df.snowfall.max()),
        'grtst_sf_dates': [] if df.snowfall.max() == 0 else list(df[df.snowfall == df.snowfall.max()].date),
        'sf_grtrT': len(df[df.snowfall > TRACE_VAL]),
        'sf_grtr1': len(df[df.snowfall > 1]), # in.
        'sf_grtr3': len(df[df.snowfall > 3]),
        'sf_grtr6': len(df[df.snowfall > 6]),
        'sf_grtr12': len(df[df.snowfall > 12]),
        'sf_grtr18': len(df[df.snowfall > 18]),

        'grtst_sd': Decimal(df.snowdepth.max()),
        'grtst_sd_dates': [] if df.snowdepth.max() == 0 else list(df[df.snowdepth == df.snowdepth.max()].date),
        'sd_grtrT': len(df[df.snowdepth > TRACE_VAL]),
        'sd_grtr1': len(df[df.snowdepth > 1]), # in.
        'sd_grtr3': len(df[df.snowdepth > 3]),
        'sd_grtr6': len(df[df.snowdepth > 6]),
        'sd_grtr12': len(df[df.snowdepth > 12]),
        'sd_grtr18': len(df[df.snowdepth > 18])
    }