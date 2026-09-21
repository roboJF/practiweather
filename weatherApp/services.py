"""External location and weather service integrations."""

import requests
from django.conf import settings

IP_ADDRESS_URL = 'http://api.ipify.org'
GEOLOCATION_URL = 'http://ip-api.com/json/{ip_address}'
WEATHER_URL = (
    'https://api.openweathermap.org/data/2.5/weather'
    '?q={city}&units=imperial&appid={api_key}'
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
    url = WEATHER_URL.format(
        city=city,
        api_key=settings.OPENWEATHER_API_KEY,
    )

    try:
        response = requests.get(url)
        if response.status_code != 200:
            return {
                'city': city,
                'temperature': 'N/A',
                'conditions': (
                    'City is either not found or the request is invalid'
                ),
            }

        data = response.json()
        return {
            'city': city,
            'temperature': data['main']['temp'],
            'conditions': data['weather'][0]['description'],
        }
    except requests.exceptions.RequestException:
        return {
            'city': city,
            'temperature': 'N/A',
            'conditions': 'Could not connect to weather service',
        }
