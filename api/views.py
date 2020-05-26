import os
from datetime import datetime

from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404

from boilerplate.settings import BASE_DIR
from . import utils
from . import forms
from . import models


def index(request):
    return render(request, 'index.html', { 'title': "Home" })

def info_view(request):
    return render(request, 'info.html', { 'title': "Info" })

def normals_view(request):
    return render(request, 'normals.html', { 'title': "Normals" })


def summaries_monthly_submit(request):
    payload = { 'title': f"Submit Monthly Summary" }

    if request.method == 'POST':
        # calc monthly summary
        form = forms.SubmitMonthlyCSV(request.POST, request.FILES)
        if form.is_valid():
            if form.cleaned_data['password'] == os.environ['SITE_PASS']:
                # move csv file
                filepath = os.path.join(BASE_DIR, 'assets', 'csv', request.FILES['csv_file'].name)
                with open(filepath, 'wb+') as dest:
                    for chunk in request.FILES['csv_file'].chunks():
                        dest.write(chunk)

                # process csv
                try:
                    year, month = utils.process_csv(filepath)
                except Exception as e:
                    payload = utils.add_alert(payload, 'danger', f"Error occurred while processing csv: <code>{str(e)}</code>")
                    return render(request, 'summaries/monthly/submit.html', payload)

                # calculate and save summaries
                try:
                    utils.calc_monthly_summary(year, month, save_to_db=True)
                    utils.calc_annual_summary(year, save_to_db=True)
                except Exception as e:
                    payload = utils.add_alert(payload, 'danger', f"Error occurred while calculating summary: <code>{str(e)}</code>")
                    return render(request, 'summaries/monthly/submit.html', payload)

                # prompt redirect
                payload = utils.add_alert(payload, 'success', f"{utils.get_month_name(month)} {year} monthly data successfully processed. <a href='/summaries/monthly/{year}/{month}'>View summary <i class='fa fa-external-link'></i></a>")
            
            else:
                payload = utils.add_alert(payload, 'danger', "Incorrect password")
        
        else:
            payload = utils.add_alert(payload, 'danger', "Form data invalid.")

    return render(request, 'summaries/monthly/submit.html', payload)

def summaries_monthly_home(request):
    return render(request, 'summaries/monthly/view.html', { 'title': "View Monthly Summary" })

def summaries_monthly_view(request, year, month):
    payload = { 'title': f"{utils.get_month_name(month)} {year} Monthly Summary" }

    if request.method == 'POST':
        # edit remarks
        form = forms.EditRemarks(request.POST)
        if form.is_valid():
            if form.cleaned_data['password'] == os.environ['SITE_PASS']:
                # find summary
                if models.MonthlySummary.objects.filter(date__year=year, date__month=month).exists():
                    summary = models.MonthlySummary.objects.filter(date__year=year, date__month=month).first()
                else:
                    payload = utils.add_alert(payload, 'danger', "Incorrect password")

                # edit remarks
                summary.remarks = form.cleaned_data['remarks']
                summary.save()
                
                # display alert
                payload = utils.add_alert(payload, 'success', f"{utils.get_month_name(month)} {year} remarks saved.")
            
            else:
                payload = utils.add_alert(payload, 'danger', "Incorrect password")
        
        else:
            payload = utils.add_alert(payload, 'danger', "Form data invalid.")
    
    # get monthly summary
    if models.MonthlySummary.objects.filter(date__year=year, date__month=month).exists():
        payload['monthly_summary'] = models.MonthlySummary.objects.filter(date__year=year, date__month=month).first()
    else:
        payload = utils.add_alert(payload, 'warning', f"{utils.get_month_name(month)} {year} Summary not found.")

    # get daily obs
    payload['daily_obs'] = models.DailyOb.objects.filter(date__year=year, date__month=month).order_by('date')

    return render(request, 'summaries/monthly/view.html', payload)

def summaries_monthly_text(request, year, month):
    payload = { 'title': f"{utils.get_month_name(month)} {year} Monthly Summary" }

    # get monthly summary
    if models.MonthlySummary.objects.filter(date__year=year, date__month=month).exists():
        # from database
        payload['monthly_summary'] = models.MonthlySummary.objects.filter(date__year=year, date__month=month).first()
    else:
        # summary not found
        raise Http404

    normals = utils.get_normals()
    payload['AVG_TEMP'] = normals['temp'][month-1]
    payload['AVG_PRECIP'] = normals['precip'][month-1]
    payload['AVG_SNFL'] = normals['sf'][month-1]

    return render(request, 'summaries/monthly/text.html', payload)

def summaries_monthly_csv(request, year, month):
    # get summary
    if models.MonthlySummary.objects.filter(date__year=year, date__month=month).exists():
        # from database
        summary = models.MonthlySummary.objects.filter(date__year=year, date__month=month).first()
    else:
        # calc
        summary = utils.calc_monthly_summary(year, month)

    if summary is not None and os.path.exists(getattr(summary, 'csv_filepath')):
        # read csv and build response
        with open(getattr(summary, 'csv_filepath'), 'r') as fh:
            response = HttpResponse(fh.read(), content_type="text/csv")
            response['Content-Disposition'] = f"attachment; filename={getattr(summary, 'csv_filepath').split('/')[-1]}"
            return response

    # csv not found
    raise Http404


def summaries_annual_home(request):
    return render(request, 'summaries/annual/view.html', { 'title': "View Annual Summary" })

def summaries_annual_view(request, year):
    payload = { 'title': f"{year} Annual Summary" }

    # get annual summary
    if models.AnnualSummary.objects.filter(year=year).exists():
        payload['annual_summary'] = models.AnnualSummary.objects.filter(year=year).first()

        # get monthly summaries
        payload['monthly_summaries'] = models.MonthlySummary.objects.filter(date__year=year).order_by('date')
    else:
        payload = utils.add_alert(payload, 'warning', f"{year} Summary not found.")

    return render(request, 'summaries/annual/view.html', payload)

def summaries_annual_text(request, year):
    payload = { 'title': f"{year} Annual Summary" }

    # get annual summary
    if models.AnnualSummary.objects.filter(year=year).exists():
        payload['annual_summary'] = models.AnnualSummary.objects.filter(year=year).first()
    else:
        raise Http404

    normals = utils.get_normals()
    payload['AVG_TEMP'] = normals['temp'][12]
    payload['AVG_PRECIP'] = normals['precip'][12]
    payload['AVG_SNFL'] = normals['sf'][12]

    return render(request, 'summaries/annual/text.html', payload)

def summaries_annual_table(request, year):
    payload = { 'title': f"{year} Annual Summary" }

    # get annual summary
    if models.AnnualSummary.objects.filter(year=year).exists():
        # get monthly summaries
        payload['all_summaries'] = list(models.MonthlySummary.objects.filter(date__year=year).order_by('date'))

        # get annual
        payload['all_summaries'].append(models.AnnualSummary.objects.filter(year=year).first())
    else:
        raise Http404

    return render(request, 'summaries/annual/table.html', payload)


def summaries_snowseason_view(request):
    payload = { 'title': "Snow Season" }

    # get snow seasons
    payload['summaries'] = models.SnowSeason.objects.all().order_by('season')

    return render(request, 'summaries/snowseason/view.html', payload)

def summaries_snowseason_season(request, season):
    payload = { 'title': f"{season} Snow Season" }

    # get snow season
    payload['summary'] = models.SnowSeason.objects.filter(season=season).first()

    # loop help
    payload['month_names'] = ['October', 'November', 'December', 'January', 'February', 'March', 'April', 'May']
    payload['month_abbrs'] = ['oct', 'nov', 'dec', 'jan', 'feb', 'mar', 'apr', 'may']

    return render(request, 'summaries/snowseason/season.html', payload)


def summaries_peakfoliage_view(request):
    payload = { 'title': "Peak Foliage" }

    # get peak foliage dates
    payload['peaks'] = models.PeakFoliage.objects.all().order_by('date')

    return render(request, 'summaries/peakfoliage/view.html', payload)


def summaries_sunsetlake_view(request):
    payload = { 'title': "Sunset Lake Ice In/Ice Out" }

    # get sunset lake summaries
    payload['summaries'] = models.SunsetLakeIceInIceOut.objects.all().order_by('season')

    return render(request, 'summaries/sunsetlake/view.html', payload)


def summaries_precip_view(request):
    payload = { 'title': "Precipitation" }

    # get monthly summaries
    payload['summaries'] = models.MonthlySummary.objects.all().order_by('date')

    return render(request, 'summaries/precip/view.html', payload)