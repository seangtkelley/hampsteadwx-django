from django.shortcuts import render
from . import utils


def index(request):
    return render(request, 'index.html', { 'title': "Home" })

def info(request):
    return render(request, 'info.html', { 'title': "Info" })

def normals(request):
    return render(request, 'normals.html', { 'title': "Normals" })


def photos_home(request):
    return render(request, 'photos/home.html', { 'title': "Photos" })

def photos_submit(request):
    if request.method == 'POST':
        # calc monthly summary
        pass

    else:
        # display form
        pass

    return render(request, 'photos/submit.html', { 'title': "Submit Photos" })


def summaries_monthly_submit(request):
    if request.method == 'POST':
        # calc monthly summary
        pass

    else:
        # display form
        pass

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

    return render(request, 'summaries/monthly/view.html', { 'title': f"{utils.get_month_name(month)} {year} Monthly Summary" })

def summaries_monthly_text(request, year, month):
    return render(request, 'summaries/monthly/text.html', { 'title': f"{utils.get_month_name(month)} {year} Monthly Summary" })

def summaries_monthly_csv(request, year, month):
    return render(request, 'index.html', { 'title': "Home" })

def summaries_monthly_html(request, year, month):
    return render(request, 'index.html', { 'title': "Home" })


def summaries_annual_home(request):
    return render(request, 'summaries/annual/view.html', { 'title': "View Annual Summary" })

def summaries_annual_view(request, year):
    return render(request, 'summaries/annual/view.html', { 'title': f"{year} Annual Summary" })

def summaries_annual_text(request, year):
    return render(request, 'summaries/annual/text.html', { 'title': f"{year} Annual Summary" })

def summaries_annual_table(request, year):
    return render(request, 'summaries/annual/table.html', { 'title': f"{year} Annual Summary" })

def summaries_annual_html(request, year):
    return render(request, 'index.html', { 'title': "Home" })


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