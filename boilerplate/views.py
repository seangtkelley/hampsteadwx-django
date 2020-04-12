from django.shortcuts import render


def index(request):
    return render(request, 'index.html', { 'title': "Home" })

def info(request):
    return render(request, 'index.html', { 'title': "Home" })

def normals(request):
    return render(request, 'index.html', { 'title': "Home" })


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

    return render(request, 'index.html', { 'title': "Home" })

def summaries_monthly_home(request):
    return render(request, 'index.html', { 'title': "Home" })

def summaries_monthly_view(request):
    if request.method == 'POST':
        # edit remarks
        pass

    else:
        # display form
        pass

    return render(request, 'index.html', { 'title': "Home" })

def summaries_monthly_text(request):
    return render(request, 'index.html', { 'title': "Home" })

def summaries_monthly_csv(request):
    return render(request, 'index.html', { 'title': "Home" })

def summaries_monthly_html(request):
    return render(request, 'index.html', { 'title': "Home" })


def summaries_annual_home(request):
    return render(request, 'index.html', { 'title': "Home" })

def summaries_annual_view(request):
    return render(request, 'index.html', { 'title': "Home" })

def summaries_annual_text(request):
    return render(request, 'index.html', { 'title': "Home" })

def summaries_annual_table(request):
    return render(request, 'index.html', { 'title': "Home" })

def summaries_annual_html(request):
    return render(request, 'index.html', { 'title': "Home" })


def summaries_snowseason_view(request):
    return render(request, 'index.html', { 'title': "Home" })

def summaries_snowseason_season(request):
    return render(request, 'index.html', { 'title': "Home" })


def summaries_peakfoliage_view(request):
    return render(request, 'index.html', { 'title': "Home" })

def summaries_peakfoliage_submit(request):
    if request.method == 'POST':
        # add peak foliage
        pass

    else:
        # display form
        pass

    return render(request, 'index.html', { 'title': "Home" })


def summaries_sunsetlake_view(request):
    return render(request, 'index.html', { 'title': "Home" })

def summaries_sunsetlake_submit(request):
    if request.method == 'POST':
        # add ice in ice out
        pass
        
    else:
        # display form
        pass

    return render(request, 'index.html', { 'title': "Home" })


def summaries_precip_view(request):
    return render(request, 'index.html', { 'title': "Home" })