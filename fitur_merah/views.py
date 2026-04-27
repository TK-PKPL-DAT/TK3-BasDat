from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def report_dashboard(request):
    """View untuk dashboard laporan"""
    context = {
        'page_title': 'Dashboard Laporan'
    }
    return render(request, 'fitur_merah/report_dashboard.html', context)
