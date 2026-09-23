from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse

from .models import SavedCity

User = get_user_model()


class AccountTests(TestCase):
    def test_signup_logs_user_in_and_rejects_username_in_different_case(self):
        credentials = {
            'username': 'robot',
            'password1': 'ExamplePass123!',
            'password2': 'ExamplePass123!',
        }

        response = self.client.post(reverse('weatherApp:sign_up'), credentials)

        self.assertRedirects(response, reverse('weatherApp:index'))
        self.assertTrue(User.objects.filter(username='robot').exists())
        self.assertEqual(
            self.client.get(reverse('weatherApp:saved_cities')).status_code,
            200,
        )

        second_client = Client()
        response = second_client.post(
            reverse('weatherApp:sign_up'),
            {**credentials, 'username': 'ROBOT'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('username', response.context['form'].errors)
        self.assertEqual(User.objects.count(), 1)

    def test_database_rejects_case_variant_username(self):
        User.objects.create_user(username='robot', password='ExamplePass123!')

        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user(
                username='ROBOT',
                password='AnotherPass123!',
            )

    def test_login_accepts_username_in_different_case(self):
        User.objects.create_user(username='robot', password='ExamplePass123!')

        response = self.client.post(
            reverse('weatherApp:login'),
            {'username': 'ROBOT', 'password': 'ExamplePass123!'},
        )

        self.assertRedirects(response, reverse('weatherApp:index'))
        self.assertEqual(
            self.client.get(reverse('weatherApp:saved_cities')).status_code,
            200,
        )

    def test_guests_can_search_but_cannot_access_saved_cities(self):
        with patch('weatherApp.views.get_weather') as get_weather:
            get_weather.return_value = {
                'city': 'Boston',
                'temperature': 70,
                'conditions': 'clear sky',
            }
            response = self.client.post(
                reverse('weatherApp:weather_by_city'),
                {'city': 'Boston'},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['weather_data']['city'], 'Boston')
        self.assertRedirects(
            self.client.get(reverse('weatherApp:saved_cities')),
            f"{reverse('weatherApp:login')}?next={reverse('weatherApp:saved_cities')}",
        )
        self.assertEqual(
            self.client.post(reverse('weatherApp:save_city')).status_code,
            302,
        )


class SavedCityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='robot',
            password='ExamplePass123!',
        )
        self.client.force_login(self.user)

    @patch('weatherApp.account_views.get_weather_by_coordinates')
    def test_save_and_reopen_city_without_duplicates(self, get_weather):
        get_weather.return_value = {
            'city': 'Charlotte',
            'city_id': 4460243,
            'country': 'US',
            'temperature': 72,
            'conditions': 'clear sky',
            'latitude': 35.2272,
            'longitude': -80.8431,
        }
        coordinates = {'latitude': '35.2272', 'longitude': '-80.8431'}

        first = self.client.post(reverse('weatherApp:save_city'), coordinates)
        second = self.client.post(reverse('weatherApp:save_city'), coordinates)
        saved_page = self.client.get(reverse('weatherApp:saved_cities'))

        self.assertEqual(first.status_code, 200)
        self.assertTrue(first.json()['created'])
        self.assertFalse(second.json()['created'])
        self.assertEqual(SavedCity.objects.count(), 1)
        self.assertContains(saved_page, 'Charlotte')
        self.assertNotContains(saved_page, 'Charlotte, US')
        self.assertContains(saved_page, '?lat=35.227200&amp;lon=-80.843100')
        self.assertContains(saved_page, 'data-latitude="35.227200"')
        self.assertContains(saved_page, 'data-longitude="-80.843100"')
        self.assertContains(saved_page, 'style="margin-left: 20px;"')
        self.assertContains(saved_page, 'weatherApp/saved_cities.js')
        self.assertRegex(
            saved_page.content.decode(),
            r'Charlotte</a>\s*<strong\s+class="saved-temperature"',
        )

    @patch('weatherApp.account_views.get_weather_by_coordinates')
    def test_unrecognized_location_is_not_saved(self, get_weather):
        get_weather.return_value = {
            'city': 'Selected location',
            'temperature': 'N/A',
            'conditions': 'Could not connect to weather service',
        }

        response = self.client.post(
            reverse('weatherApp:save_city'),
            {'latitude': '35.2272', 'longitude': '-80.8431'},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(SavedCity.objects.count(), 0)

    def test_saved_cities_are_private_and_only_owner_can_remove_them(self):
        city = SavedCity.objects.create(
            user=self.user,
            city_id=4460243,
            name='Charlotte',
            country='US',
            latitude=35.2272,
            longitude=-80.8431,
        )
        other_user = User.objects.create_user(
            username='someone_else',
            password='ExamplePass123!',
        )
        self.client.force_login(other_user)

        self.assertNotContains(
            self.client.get(reverse('weatherApp:saved_cities')),
            'Charlotte',
        )
        self.assertEqual(
            self.client.post(
                reverse('weatherApp:delete_saved_city', args=[city.pk])
            ).status_code,
            404,
        )
        self.assertTrue(SavedCity.objects.filter(pk=city.pk).exists())

        self.client.force_login(self.user)
        response = self.client.post(
            reverse('weatherApp:delete_saved_city', args=[city.pk])
        )

        self.assertRedirects(response, reverse('weatherApp:saved_cities'))
        self.assertFalse(SavedCity.objects.filter(pk=city.pk).exists())
