from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .services import (
    format_location,
    get_current_location,
    get_weather,
    get_weather_by_coordinates,
)


def index(request):
    location = get_current_location()
    default_city = format_location(location)
    city = default_city

    if request.method == 'POST':
        city = request.POST.get('city', '').strip()
        if not city:
            city = default_city

    context = {
        'weather_data': get_weather(city),
        'use_browser_location': request.method == 'GET',
    }
    return render(request, 'weatherApp/weatherApp.html', context)


@require_POST
def weather_by_coordinates(request):
    try:
        latitude = float(request.POST['latitude'])
        longitude = float(request.POST['longitude'])
    except (KeyError, TypeError, ValueError):
        return JsonResponse({'error': 'Invalid coordinates'}, status=400)

    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return JsonResponse({'error': 'Invalid coordinates'}, status=400)

    weather_data = get_weather_by_coordinates(latitude, longitude)
    return JsonResponse({'weather_data': weather_data})
