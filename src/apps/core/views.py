from django.http import JsonResponse
from django.shortcuts import render


def landing_view(request):
    return render(request, 'landing.html')


def health_view(request):
    return JsonResponse({'status': 'ok'})
