from django.shortcuts import render


def index(request):
    return render(request, 'index.html', { 'title': "Home" })

def info(request):
    return render(request, 'info.html', { 'title': "Info" })

def normals(request):
    return render(request, 'normals.html', { 'title': "Normals" })


def photos_home(request):
    return render(request, 'index.html', { 'title': "Home" })

def photos_submit(request):
    if request.method == 'POST':
        # calc monthly summary
        pass

    else:
        # display form
        pass

    return render(request, 'index.html', { 'title': "Home" })


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

def summaries_monthly_view(request):
    if request.method == 'POST':
        # edit remarks
        pass

    else:
        # display form
        pass

    return render(request, 'summaries/monthly/view.html', { 'title': "\%b \%d Monthly Summary" })

def summaries_monthly_text(request):
    return render(request, 'summaries/monthly/text.html', { 'title': "\%b \%d Monthly Summary" })

def summaries_monthly_csv(request):
    return render(request, 'index.html', { 'title': "Home" })

def summaries_monthly_html(request):
    return render(request, 'index.html', { 'title': "Home" })


def summaries_annual_home(request):
    return render(request, 'summaries/annual/view.html', { 'title': "View Annual Summary" })

def summaries_annual_view(request):
    return render(request, 'summaries/annual/view.html', { 'title': "\%d Annual Summary" })

def summaries_annual_text(request):
    return render(request, 'summaries/annual/text.html', { 'title': "\%d Annual Summary" })

def summaries_annual_table(request):
    return render(request, 'summaries/annual/table.html', { 'title': "\%d Annual Summary" })

def summaries_annual_html(request):
    return render(request, 'index.html', { 'title': "Home" })


def summaries_snowseason_view(request):
    return render(request, 'summaries/snowseason/view.html', { 'title': "Snow Season" })

def summaries_snowseason_season(request):
    return render(request, 'summaries/snowseason/season.html', { 'title': "<Season> Snow Season" })


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