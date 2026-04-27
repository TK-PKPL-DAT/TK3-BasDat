from django.urls import path
from . import views

app_name = 'fitur_merah'

urlpatterns = [
    path('report/', views.report_dashboard, name='report_dashboard'),
]