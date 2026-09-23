# PractiWeather

A Django weather app with city search, map-based lookup, and optional accounts for saved cities. Weather data comes from OpenWeatherMap; account and saved-city data is stored in PostgreSQL.

## Local setup

1. Create and activate a Python virtual environment, then install dependencies:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Create a local PostgreSQL database named `practiweather` (or choose another name and set `POSTGRES_DB` accordingly).
3. Copy `.env.example` to `.env` and set `OPENWEATHER_API_KEY`, `DJANGO_SECRET_KEY`, and your PostgreSQL connection values. Keep `.env` private; it is ignored by Git.
4. Apply migrations and start the development server:

   ```powershell
   python manage.py migrate
   python manage.py runserver
   ```

Open `http://127.0.0.1:8000/`. Guests can search and use the map. Create an account to save the city currently displayed and revisit it from **Saved cities**.

## Tests

```powershell
python manage.py test
node --test weatherApp/tests_js/weather.test.js
```

The Django test suite creates and removes a separate PostgreSQL test database; the configured database user must be able to create databases.
