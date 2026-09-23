from django.contrib.auth import views as auth_views
from django.urls import path

from . import account_views, views

app_name = 'weatherApp'

urlpatterns = [
    path('', views.index, name='index'),
    path('weather/city/', views.weather_by_city, name='weather_by_city'),
    path(
        'weather/coordinates/',
        views.weather_by_coordinates,
        name='weather_by_coordinates',
    ),
    path('accounts/sign-up/', account_views.sign_up, name='sign_up'),
    path(
        'accounts/login/',
        auth_views.LoginView.as_view(template_name='weatherApp/login.html'),
        name='login',
    ),
    path(
        'accounts/logout/',
        auth_views.LogoutView.as_view(next_page='weatherApp:index'),
        name='logout',
    ),
    path('saved/', account_views.saved_cities, name='saved_cities'),
    path('saved/add/', account_views.save_city, name='save_city'),
    path(
        'saved/<int:city_id>/delete/',
        account_views.delete_saved_city,
        name='delete_saved_city',
    ),
]
