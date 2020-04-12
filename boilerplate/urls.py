"""hampsteadwx URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    # public site
    
    # basic pages
    path('', views.index, name='index'),
    path('home', views.index, name='home'),
    path('info', views.info, name='info'),
    path('normals', views.normals, name='normals'),

    # photos
    path('photos', views.photos_home, name='photos_home'),
    path('photos/submit', views.photos_submit, name='photos_submit'),

    # summaries
    path('summaries/monthly', views.summaries_monthly_home, name='summaries_monthly_home'),
    path('summaries/monthly/<int:year>/<int:month>/', views.summaries_monthly_view, name='summaries_monthly_view'),
    path('summaries/monthly/<int:year>/<int:month>/text', views.summaries_monthly_text, name='summaries_monthly_text'),
    path('summaries/monthly/<int:year>/<int:month>/csv', views.summaries_monthly_csv, name='summaries_monthly_csv'),
    path('summaries/monthly/<int:year>/<int:month>/html', views.summaries_monthly_html, name='summaries_monthly_html'),
    path('summaries/monthly/submit', views.summaries_monthly_submit, name='summaries_monthly_submit'),

    path('summaries/annual', views.summaries_annual_home, name='summaries_annual_home'),
    path('summaries/annual/<int:year>', views.summaries_annual_view, name='summaries_annual_view'),
    path('summaries/annual/<int:year>/text', views.summaries_annual_text, name='summaries_annual_text'),
    path('summaries/annual/<int:year>/table', views.summaries_annual_table, name='summaries_annual_table'),
    path('summaries/annual/<int:year>/html', views.summaries_annual_html, name='summaries_annual_html'),

    path('summaries/snowseason', views.summaries_snowseason_view, name='summaries_snowseason_view'),
    path('summaries/snowseason/<slug:season>', views.summaries_snowseason_season, name='summaries_snowseason_season'),

    path('summaries/peakfoliage', views.summaries_peakfoliage_view, name='summaries_peakfoliage_view'),
    path('summaries/peakfoliage/submit', views.summaries_peakfoliage_submit, name='summaries_peakfoliage_submit'),

    path('summaries/sunsetlake', views.summaries_sunsetlake_view, name='summaries_sunsetlake_view'),
    path('summaries/sunsetlake/submit', views.summaries_sunsetlake_submit, name='summaries_sunsetlake_submit'),

    path('summaries/precip', views.summaries_precip_view, name='summaries_precip_view'),

    # autogen
    path('api/', include('api.urls')),
    path('admin/', admin.site.urls),
]
