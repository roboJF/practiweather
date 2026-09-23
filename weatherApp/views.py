from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .forms import CoordinatesForm
from .services import (
    format_location,
    get_current_location,
    get_weather,
    get_weather_by_coordinates,
)


@require_GET
def index(request):
    return render(request, 'weatherApp/weatherApp.html')


@require_POST
def weather_by_city(request):
    city = request.POST.get('city', '').strip()
    if not city:
        city = format_location(get_current_location())

    return JsonResponse({'weather_data': get_weather(city)})


@require_POST
def weather_by_coordinates(request):
    form = CoordinatesForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'error': 'Invalid coordinates'}, status=400)

    weather_data = get_weather_by_coordinates(
        form.cleaned_data['latitude'],
        form.cleaned_data['longitude'],
    )
    return JsonResponse({'weather_data': weather_data})
