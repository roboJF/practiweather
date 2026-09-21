from django.shortcuts import render

from .services import format_location, get_current_location, get_weather


def index(request):
    location = get_current_location()
    default_city = format_location(location)
    city = default_city

    if request.method == 'POST':
        city = request.POST.get('city', '').strip()
        if not city:
            city = default_city

    context = {'weather_data': get_weather(city)}
    return render(request, 'weatherApp/weatherApp.html', context)
