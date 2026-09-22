"""External location and weather service integrations."""

import requests
from django.conf import settings

from .location_queries import normalize_location_query

IP_ADDRESS_URL = 'http://api.ipify.org'
GEOLOCATION_URL = 'http://ip-api.com/json/{ip_address}'
OPENWEATHER_GEOCODING_URL = (
    'https://api.openweathermap.org/geo/1.0/direct'
)
OPENWEATHER_WEATHER_URL = (
    'https://api.openweathermap.org/data/2.5/weather'
)


def get_current_location():
    """Return the city, region, and country associated with the public IP."""
    ip_address = requests.get(IP_ADDRESS_URL).text
    ip_data = requests.get(
        GEOLOCATION_URL.format(ip_address=ip_address)
    ).json()

    return {
        'city': ip_data['city'],
        'region': ip_data['regionName'],
        'country': ip_data['country'],
    }


def format_location(location):
    """Format location data for OpenWeather and for display."""
    return (
        f"{location['city']}, {location['region']}, {location['country']}"
    )


def get_weather(city):
    """Return the existing template-friendly weather data for a city."""
    try:
        geocoding_response = requests.get(
            OPENWEATHER_GEOCODING_URL,
            params={
                'q': normalize_location_query(city),
                'limit': 1,
                'appid': settings.OPENWEATHER_API_KEY,
            },
        )
        if geocoding_response.status_code != 200:
            return _invalid_city_weather(city)

        locations = geocoding_response.json()
        if not locations:
            return _invalid_city_weather(city)
    except requests.exceptions.RequestException:
        return _connection_error_weather(city)

    location = locations[0]
    return get_weather_by_coordinates(
        location['lat'],
        location['lon'],
        fallback_city=city,
    )


def get_weather_by_coordinates(latitude, longitude, fallback_city='Selected location'):
    """Return weather for a geographic point without a geocoding request."""
    try:
        response = requests.get(
            OPENWEATHER_WEATHER_URL,
            params={
                'lat': latitude,
                'lon': longitude,
                'units': 'imperial',
                'appid': settings.OPENWEATHER_API_KEY,
            },
        )
        if response.status_code != 200:
            return _invalid_city_weather(fallback_city)

        data = response.json()
        return {
            'city': data['name'],
            'temperature': data['main']['temp'],
            'conditions': data['weather'][0]['description'],
            'latitude': latitude,
            'longitude': longitude,
        }
    except requests.exceptions.RequestException:
        return _connection_error_weather(fallback_city)


def _invalid_city_weather(city):
    return {
        'city': city,
        'temperature': 'N/A',
        'conditions': 'City is either not found or the request is invalid',
    }


def _connection_error_weather(city):
    return {
        'city': city,
        'temperature': 'N/A',
        'conditions': 'Could not connect to weather service',
    }
