import os

from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404

from boilerplate.settings import BASE_DIR
from . import utils
from . import workflow
from . import forms
from . import models


def index(request):
    return render(request, 'index.html', { 'title': "Home" })

def info_view(request):
    return render(request, 'info.html', { 'title': "Info" })

def normals_view(request):
    return render(request, 'normals.html', { 'title': "Normals" })


def photos_home(request):
    return render(request, 'photos/home.html', { 'title': "Photos" })

def photos_submit(request):
    if request.method == 'POST':
        # save photo
        pass

    else:
        # display form
        pass

    return render(request, 'photos/submit.html', { 'title': "Submit Photos" })


def summaries_monthly_submit(request):
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
                    year, month = workflow.process_csv(filepath)
                except Exception as e:
                    return render(request, 'summaries/monthly/submit.html', { 
                        'title': "Submit Monthly Summary",
                        'alerts': [ utils.create_alert('danger', f"Error occurred while processing csv: <code>{str(e)}</code>") ]
                        })
                
                # prompt redirect
                return render(request, 'summaries/monthly/submit.html', { 
                    'title': "Submit Monthly Summary",
                    'alerts': [ utils.create_alert('success', f"{utils.get_month_name(month)} {year} monthly data successfully processed. <a href='/summaries/monthly/{year}/{month}'>View summary <i class='fa fa-external-link'></i></a>") ]
                    })
            
            else:
                return render(request, 'summaries/monthly/submit.html', { 
                    'title': "Submit Monthly Summary",
                    'alerts': [ utils.create_alert('danger', "Incorrect password") ]
                    })
        
        else:
            return render(request, 'summaries/monthly/submit.html', { 
                    'title': "Submit Monthly Summary",
                    'alerts': [ utils.create_alert('danger', "Form data invalid.") ]
                    })

    return render(request, 'summaries/monthly/submit.html', { 'title': "Submit Monthly Summary" })

def summaries_monthly_home(request):
    return render(request, 'summaries/monthly/view.html', { 'title': "View Monthly Summary" })

def summaries_monthly_view(request, year, month):
    if request.method == 'POST':
        # edit remarks
        pass

    else:
        # display form
        pass

    # get monthly summary
    if models.MonthlyOb.objects.filter(date__year=year, date__month=month).exists():
        # from database
        summary = models.MonthlyOb.objects.filter(date__year=year, date__month=month)
    else:
        # calc
        summary = workflow.calc_monthly_summary(year, month)

    return render(request, 'summaries/monthly/view.html', { 
        'title': f"{utils.get_month_name(month)} {year} Monthly Summary",
        'monthly_summary': summary,
        'daily_obs': models.DailyOb.objects.filter(date__year=year, date__month=month).order_by('date')
        })

def summaries_monthly_text(request, year, month):
    # get monthly summary
    if models.MonthlyOb.objects.filter(date__year=year, date__month=month).exists():
        # from database
        summary = models.MonthlyOb.objects.filter(date__year=year, date__month=month)
    else:
        # calc
        summary = workflow.calc_monthly_summary(year, month)

    normals = workflow.get_normals()
    return render(request, 'summaries/monthly/text.html', { 
        'title': f"{utils.get_month_name(month)} {year} Monthly Summary",
        'monthly_summary': summary,
        'AVG_TEMP': normals['temp'][month-1],
        'AVG_PRECIP': normals['precip'][month-1],
        'AVG_SNFL': normals['sf'][month-1],
        })

def summaries_monthly_csv(request, year, month):
    # get summary
    if models.MonthlyOb.objects.filter(date__year=year, date__month=month).exists():
        # from database
        summary = models.MonthlyOb.objects.filter(date__year=year, date__month=month)
    else:
        # calc
        summary = workflow.calc_monthly_summary(year, month)

    if os.path.exists(summary['csv_filepath']):
        # read csv and build response
        with open(summary['csv_filepath'], 'r') as fh:
            response = HttpResponse(fh.read(), content_type="text/csv")
            response['Content-Disposition'] = f"attachment; filename={summary['csv_filepath'].split('/')[-1]}"
            return response
    # csv not found
    raise Http404


def summaries_annual_home(request):
    return render(request, 'summaries/annual/view.html', { 'title': "View Annual Summary" })

def summaries_annual_view(request, year):
    # get annual summary
    if None is not None: # models.AnnualSummary.objects.filter(date__year=year).exists():
        # from database: TODO
        # summary = models.AnnualSummary.objects.filter(date__year=year)
        pass
    else:
        # calc
        annual_summary = workflow.calc_annual_summary(year)

    # get monthly summaries
    monthly_summaries = []
    for month in range(1, 13):
        if models.MonthlyOb.objects.filter(date__year=year, date__month=month).exists():
            # from database
            monthly_summaries.append(models.MonthlyOb.objects.filter(date__year=year, date__month=month))
        elif models.DailyOb.objects.filter(date__year=year, date__month=month).count() > 0:
            # calc
            monthly_summaries.append(workflow.calc_monthly_summary(year, month))

    return render(request, 'summaries/annual/view.html', { 
        'title': f"{year} Annual Summary",
        'annual_summary': annual_summary,
        'monthly_summaries': monthly_summaries,
        })

def summaries_annual_text(request, year):
    # get annual summary
    if None is not None: # models.AnnualSummary.objects.filter(date__year=year).exists():
        # from database: TODO
        # summary = models.AnnualSummary.objects.filter(date__year=year)
        pass
    else:
        # calc
        annual_summary = workflow.calc_annual_summary(year)

    normals = workflow.get_normals()
    return render(request, 'summaries/annual/text.html', {
        'title': f"{year} Annual Summary",
        'annual_summary': annual_summary,
        'AVG_TEMP': normals['temp'][12],
        'AVG_PRECIP': normals['precip'][12],
        'AVG_SNFL': normals['sf'][12],
        })

def summaries_annual_table(request, year):
    all_summaries = []

    # get monthly summaries    
    for month in range(1, 13):
        if models.MonthlyOb.objects.filter(date__year=year, date__month=month).exists():
            # from database
            all_summaries.append(models.MonthlyOb.objects.filter(date__year=year, date__month=month))
        elif models.DailyOb.objects.filter(date__year=year, date__month=month).count() > 0:
            # calc
            all_summaries.append(workflow.calc_monthly_summary(year, month))

    # get annual summary
    if None is not None: # models.AnnualSummary.objects.filter(date__year=year).exists():
        # from database: TODO
        # all_summaries.append(models.AnnualSummary.objects.filter(date__year=year))
        pass
    else:
        # calc
        all_summaries.append(workflow.calc_annual_summary(year))

    return render(request, 'summaries/annual/table.html', {
        'title': f"{year} Annual Summary",
        'all_summaries': all_summaries
        })


def summaries_snowseason_view(request):
    return render(request, 'summaries/snowseason/view.html', { 'title': "Snow Season" })

def summaries_snowseason_season(request, season):
    month_names = ['October', 'November', 'December', 'January', 'February', 'March', 'April', 'May']
    month_abbrs = ['oct', 'nov', 'dec', 'jan', 'feb', 'mar', 'apr', 'may']
    return render(request, 'summaries/snowseason/season.html', { 
        'title': f"{season} Snow Season",
        'month_names': month_names,
        'month_abbrs': month_abbrs
        })


def summaries_peakfoliage_view(request):
    return render(request, 'summaries/peakfoliage/view.html', { 'title': "Peak Foliage" })

def summaries_peakfoliage_submit(request):
    if request.method == 'POST':
        # add peak foliage
        pass

    else:
        # display form
        pass

    return render(request, 'summaries/peakfoliage/submit.html', { 'title': "Submit Peak Foliage" })


def summaries_sunsetlake_view(request):
    return render(request, 'summaries/sunsetlake/view.html', { 'title': "Sunset Lake Ice In/Ice Out" })

def summaries_sunsetlake_submit(request):
    if request.method == 'POST':
        # add ice in ice out
        pass
        
    else:
        # display form
        pass

    return render(request, 'summaries/sunsetlake/submit.html', { 'title': "Submit Sunset Lake Ice In/Ice Out" })


def summaries_precip_view(request):
    return render(request, 'summaries/precip/view.html', { 'title': "Precipitation" })