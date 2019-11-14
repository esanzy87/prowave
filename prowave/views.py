"""
prowave.views
"""
from django.shortcuts import render


def home(request):
    """
    Landing Page (https://www.prowave.org/)
    """
    return render(request, 'index.html')
