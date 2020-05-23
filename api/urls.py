from django.urls import path

from . import views


urlpatterns = [
    # public site
    
    # basic pages
    path('', views.index, name='index'),
    path('home', views.index, name='home'),
    path('info', views.info_view, name='info'),
    path('normals', views.normals_view, name='normals'),

    # photos
    path('photos', views.photos_home, name='photos_home'),
    path('photos/submit', views.photos_submit, name='photos_submit'),

    # summaries
    path('summaries/monthly', views.summaries_monthly_home, name='summaries_monthly_home'),
    path('summaries/monthly/<int:year>/<int:month>/', views.summaries_monthly_view, name='summaries_monthly_view'),
    path('summaries/monthly/<int:year>/<int:month>/text', views.summaries_monthly_text, name='summaries_monthly_text'),
    path('summaries/monthly/<int:year>/<int:month>/csv', views.summaries_monthly_csv, name='summaries_monthly_csv'),
    path('summaries/monthly/submit', views.summaries_monthly_submit, name='summaries_monthly_submit'),

    path('summaries/annual', views.summaries_annual_home, name='summaries_annual_home'),
    path('summaries/annual/<int:year>', views.summaries_annual_view, name='summaries_annual_view'),
    path('summaries/annual/<int:year>/text', views.summaries_annual_text, name='summaries_annual_text'),
    path('summaries/annual/<int:year>/table', views.summaries_annual_table, name='summaries_annual_table'),

    path('summaries/snowseason', views.summaries_snowseason_view, name='summaries_snowseason_view'),
    path('summaries/snowseason/<slug:season>', views.summaries_snowseason_season, name='summaries_snowseason_season'),

    path('summaries/peakfoliage', views.summaries_peakfoliage_view, name='summaries_peakfoliage_view'),

    path('summaries/sunsetlake', views.summaries_sunsetlake_view, name='summaries_sunsetlake_view'),

    path('summaries/precip', views.summaries_precip_view, name='summaries_precip_view'),
    
]