from unittest.mock import Mock, call, patch

import requests
from django.test import SimpleTestCase, override_settings
from django.urls import reverse

from .location_queries import normalize_location_query
from .services import get_current_location, get_weather


class IndexViewTests(SimpleTestCase):
    location = {
        'city': 'Baltimore',
        'region': 'Maryland',
        'country': 'United States',
    }
    default_city = 'Baltimore, Maryland, United States'
    weather = {
        'city': default_city,
        'temperature': 72,
        'conditions': 'clear sky',
    }

    @patch('weatherApp.views.get_weather')
    @patch('weatherApp.views.get_current_location')
    def test_get_uses_location_as_default_city(self, get_location, get_weather):
        get_location.return_value = self.location
        get_weather.return_value = self.weather

        response = self.client.get(reverse('weatherApp:index'))

        self.assertEqual(response.status_code, 200)
        get_weather.assert_called_once_with(self.default_city)
        self.assertEqual(response.context['weather_data'], self.weather)
        self.assertTemplateUsed(response, 'weatherApp/weatherApp.html')

    @patch('weatherApp.views.get_weather')
    @patch('weatherApp.views.get_current_location')
    def test_post_strips_and_uses_submitted_city(
        self,
        get_location,
        get_weather,
    ):
        get_location.return_value = self.location
        get_weather.return_value = {
            **self.weather,
            'city': 'Boston',
        }

        response = self.client.post(
            reverse('weatherApp:index'),
            {'city': '  Boston  '},
        )

        self.assertEqual(response.status_code, 200)
        get_weather.assert_called_once_with('Boston')

    @patch('weatherApp.views.get_weather')
    @patch('weatherApp.views.get_current_location')
    def test_blank_post_uses_location_as_default_city(
        self,
        get_location,
        get_weather,
    ):
        get_location.return_value = self.location
        get_weather.return_value = self.weather

        response = self.client.post(
            reverse('weatherApp:index'),
            {'city': '   '},
        )

        self.assertEqual(response.status_code, 200)
        get_weather.assert_called_once_with(self.default_city)


class LocationServiceTests(SimpleTestCase):
    @patch('weatherApp.services.requests.get')
    def test_get_current_location_uses_public_ip(self, get):
        ip_response = Mock(text='203.0.113.5')
        location_response = Mock()
        location_response.json.return_value = {
            'city': 'Baltimore',
            'regionName': 'Maryland',
            'country': 'United States',
        }
        get.side_effect = [ip_response, location_response]

        location = get_current_location()

        self.assertEqual(
            location,
            {
                'city': 'Baltimore',
                'region': 'Maryland',
                'country': 'United States',
            },
        )
        self.assertEqual(
            get.call_args_list,
            [
                call('http://api.ipify.org'),
                call('http://ip-api.com/json/203.0.113.5'),
            ],
        )


class LocationQueryTests(SimpleTestCase):
    def test_normalizes_us_state_name_without_commas(self):
        self.assertEqual(
            normalize_location_query('Charlotte North Carolina'),
            'Charlotte,NC,US',
        )

    def test_normalizes_comma_separated_full_names(self):
        self.assertEqual(
            normalize_location_query(
                'Charlotte, North Carolina, United States'
            ),
            'Charlotte,NC,US',
        )

    def test_leaves_city_only_query_unchanged(self):
        self.assertEqual(normalize_location_query('Paris'), 'Paris')


@override_settings(OPENWEATHER_API_KEY='test-key')
class WeatherServiceTests(SimpleTestCase):
    @patch('weatherApp.services.requests.get')
    def test_successful_response_returns_weather_data(self, get):
        geocoding_response = Mock(status_code=200)
        geocoding_response.json.return_value = [
            {
                'name': 'Charlotte',
                'lat': 35.2272,
                'lon': -80.8431,
                'country': 'US',
                'state': 'North Carolina',
            }
        ]
        weather_response = Mock(status_code=200)
        weather_response.json.return_value = {
            'name': 'Charlotte',
            'main': {'temp': 72.25},
            'weather': [{'description': 'clear sky'}],
        }
        get.side_effect = [geocoding_response, weather_response]

        weather = get_weather('Charlotte North Carolina')

        self.assertEqual(
            weather,
            {
                'city': 'Charlotte',
                'temperature': 72.25,
                'conditions': 'clear sky',
            },
        )
        self.assertEqual(
            get.call_args_list,
            [
                call(
                    'https://api.openweathermap.org/geo/1.0/direct',
                    params={
                        'q': 'Charlotte,NC,US',
                        'limit': 1,
                        'appid': 'test-key',
                    },
                ),
                call(
                    'https://api.openweathermap.org/data/2.5/weather',
                    params={
                        'lat': 35.2272,
                        'lon': -80.8431,
                        'units': 'imperial',
                        'appid': 'test-key',
                    },
                ),
            ],
        )

    @patch('weatherApp.services.requests.get')
    def test_unsuccessful_response_returns_existing_error_message(self, get):
        get.return_value = Mock(status_code=404)

        weather = get_weather('Unknown')

        self.assertEqual(
            weather,
            {
                'city': 'Unknown',
                'temperature': 'N/A',
                'conditions': (
                    'City is either not found or the request is invalid'
                ),
            },
        )

    @patch('weatherApp.services.requests.get')
    def test_no_geocoding_matches_returns_existing_error_message(self, get):
        response = Mock(status_code=200)
        response.json.return_value = []
        get.return_value = response

        weather = get_weather('Unknown')

        self.assertEqual(
            weather,
            {
                'city': 'Unknown',
                'temperature': 'N/A',
                'conditions': (
                    'City is either not found or the request is invalid'
                ),
            },
        )
        self.assertEqual(get.call_count, 1)

    @patch('weatherApp.services.requests.get')
    def test_connection_error_returns_existing_error_message(self, get):
        get.side_effect = requests.exceptions.ConnectionError

        weather = get_weather('Baltimore')

        self.assertEqual(
            weather,
            {
                'city': 'Baltimore',
                'temperature': 'N/A',
                'conditions': 'Could not connect to weather service',
            },
        )

    @patch('weatherApp.services.requests.get')
    def test_response_parsing_error_returns_existing_error_message(self, get):
        response = Mock(status_code=200)
        response.json.side_effect = requests.exceptions.JSONDecodeError(
            'Invalid JSON',
            '',
            0,
        )
        get.return_value = response

        weather = get_weather('Baltimore')

        self.assertEqual(
            weather,
            {
                'city': 'Baltimore',
                'temperature': 'N/A',
                'conditions': 'Could not connect to weather service',
            },
        )
