from decimal import Decimal

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import CoordinatesForm, SignUpForm
from .models import SavedCity
from .services import get_weather_by_coordinates


@require_http_methods(['GET', 'POST'])
def sign_up(request):
    if request.user.is_authenticated:
        return redirect('weatherApp:index')

    form = SignUpForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('weatherApp:index')

    return render(request, 'weatherApp/sign_up.html', {'form': form})


@login_required
@require_GET
def saved_cities(request):
    cities = SavedCity.objects.filter(user=request.user)
    return render(request, 'weatherApp/saved_cities.html', {'cities': cities})


@login_required
@require_POST
def save_city(request):
    form = CoordinatesForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'error': 'Invalid coordinates'}, status=400)

    weather = get_weather_by_coordinates(
        form.cleaned_data['latitude'],
        form.cleaned_data['longitude'],
    )
    city_id = weather.get('city_id')
    if type(city_id) is not int or city_id <= 0:
        return JsonResponse({'error': 'This city could not be saved'}, status=400)

    city, created = SavedCity.objects.get_or_create(
        user=request.user,
        city_id=city_id,
        defaults={
            'name': weather['city'],
            'country': weather['country'],
            'latitude': _stored_coordinate(form.cleaned_data['latitude']),
            'longitude': _stored_coordinate(form.cleaned_data['longitude']),
        },
    )
    return JsonResponse({'saved': True, 'created': created, 'city': city.name})


@login_required
@require_POST
def delete_saved_city(request, city_id):
    city = get_object_or_404(SavedCity, pk=city_id, user=request.user)
    city.delete()
    return redirect('weatherApp:saved_cities')


def _stored_coordinate(value):
    return Decimal(str(value)).quantize(Decimal('0.000001'))
