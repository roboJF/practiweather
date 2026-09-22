from django.urls import path

from . import views

app_name = 'weatherApp'

urlpatterns = [
    path('', views.index, name='index'),
    path('weather/city/', views.weather_by_city, name='weather_by_city'),
    path(
        'weather/coordinates/',
        views.weather_by_coordinates,
        name='weather_by_coordinates',
    ),
]
