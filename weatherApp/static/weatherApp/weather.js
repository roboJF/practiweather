(() => {
    const searchForm = document.getElementById('citySearchForm');
    const cityInput = document.getElementById('citySearch');
    const mapElement = document.getElementById('weatherMap');
    const statusElement = document.getElementById('mapStatus');
    const saveButton = document.getElementById('saveCityButton');
    const saveStatus = document.getElementById('saveStatus');
    const csrfToken = searchForm.querySelector('[name=csrfmiddlewaretoken]').value;

    let map = null;
    let marker = null;
    let activeRequest = null;
    let hasUserInteracted = false;
    let selectedWeather = null;

    if (typeof maplibregl !== 'undefined') {
        try {
            map = new maplibregl.Map({
                container: mapElement,
                style: 'https://tiles.openfreemap.org/styles/positron',
                center: [-98.5795, 39.8283],
                zoom: 4,
                attributionControl: true,
            });
            map.addControl(new maplibregl.NavigationControl(), 'top-right');
            map.on('click', (event) => {
                hasUserInteracted = true;
                setMarker(event.lngLat.lng, event.lngLat.lat);
                requestWeather(mapElement.dataset.weatherUrl, {
                    latitude: event.lngLat.lat.toString(),
                    longitude: event.lngLat.lng.toString(),
                }, false);
            });
        } catch (error) {
            map = null;
            mapElement.textContent = 'Map unavailable. City search still works.';
        }
    } else {
        mapElement.textContent = 'Map unavailable. City search still works.';
    }

    searchForm.addEventListener('submit', (event) => {
        event.preventDefault();
        hasUserInteracted = true;
        requestWeather(searchForm.dataset.weatherUrl, {
            city: cityInput.value,
        }, true);
    });

    if (saveButton) {
        saveButton.addEventListener('click', saveSelectedCity);
    }

    const locationParams = new URLSearchParams(window.location.search);
    const savedLatitude = Number(locationParams.get('lat'));
    const savedLongitude = Number(locationParams.get('lon'));
    if (locationParams.has('lat') && locationParams.has('lon')
        && Number.isFinite(savedLatitude) && Number.isFinite(savedLongitude)
        && Math.abs(savedLatitude) <= 90 && Math.abs(savedLongitude) <= 180) {
        requestWeather(mapElement.dataset.weatherUrl, {
            latitude: savedLatitude.toString(),
            longitude: savedLongitude.toString(),
        }, true);
    } else {
        locateUser();
    }

    function locateUser() {
        if (!navigator.geolocation) {
            loadApproximateLocation();
            return;
        }

        statusElement.textContent = 'Finding your location...';
        navigator.geolocation.getCurrentPosition(
            (position) => {
                if (hasUserInteracted) {
                    return;
                }

                requestWeather(mapElement.dataset.weatherUrl, {
                    latitude: position.coords.latitude.toString(),
                    longitude: position.coords.longitude.toString(),
                }, true);
            },
            () => {
                if (!hasUserInteracted) {
                    loadApproximateLocation();
                }
            },
            {
                enableHighAccuracy: false,
                timeout: 10000,
                maximumAge: 300000,
            },
        );
    }

    function loadApproximateLocation() {
        requestWeather(searchForm.dataset.weatherUrl, {city: ''}, true);
    }

    async function requestWeather(url, fields, centerMap) {
        if (activeRequest) {
            activeRequest.abort();
        }

        const controller = new AbortController();
        activeRequest = controller;
        statusElement.textContent = 'Loading weather...';

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken,
                },
                body: new URLSearchParams(fields),
                signal: controller.signal,
            });
            if (!response.ok) {
                throw new Error('Unable to load weather. Please try again.');
            }

            const {weather_data: weather} = await response.json();
            if (activeRequest !== controller) {
                return;
            }
            updateWeather(weather);

            if (centerMap && Number.isFinite(weather.latitude)
                && Number.isFinite(weather.longitude)) {
                map?.flyTo({
                    center: [weather.longitude, weather.latitude],
                    zoom: 8,
                });
                setMarker(weather.longitude, weather.latitude);
            }

            statusElement.textContent = weather.temperature === 'N/A'
                ? weather.conditions
                : `Weather updated for ${weather.city}.`;
        } catch (error) {
            if (activeRequest === controller && error.name !== 'AbortError') {
                statusElement.textContent = (
                    error.message || 'Unable to load weather. Please try again.'
                );
            }
        } finally {
            if (activeRequest === controller) {
                activeRequest = null;
            }
        }
    }

    function setMarker(longitude, latitude) {
        if (!map) {
            return;
        }

        const coordinates = [longitude, latitude];
        if (marker) {
            marker.setLngLat(coordinates);
        } else {
            marker = new maplibregl.Marker()
                .setLngLat(coordinates)
                .addTo(map);
        }
    }

    function updateWeather(weather) {
        document.getElementById('cityName').textContent = weather.city;
        document.getElementById('temperature').textContent = (
            formatTemperature(weather.temperature)
        );
        document.getElementById('conditions').textContent = (
            toTitleCase(weather.conditions)
        );

        if (saveButton) {
            const canSave = Number.isInteger(weather.city_id)
                && weather.city_id > 0
                && Number.isFinite(weather.latitude)
                && Number.isFinite(weather.longitude);
            selectedWeather = canSave ? weather : null;
            saveButton.hidden = !canSave;
            saveButton.disabled = false;
            saveButton.textContent = 'Save city';
            saveStatus.textContent = '';
        }
    }

    async function saveSelectedCity() {
        const weather = selectedWeather;
        if (!weather) {
            return;
        }

        saveButton.disabled = true;
        saveStatus.textContent = 'Saving...';

        try {
            const response = await fetch(saveButton.dataset.saveUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken,
                },
                body: new URLSearchParams({
                    latitude: weather.latitude.toString(),
                    longitude: weather.longitude.toString(),
                }),
            });
            if (response.redirected) {
                throw new Error('Session expired. Please log in again.');
            }
            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.error || 'Unable to save this city.');
            }
            if (selectedWeather === weather) {
                saveButton.textContent = 'Saved';
                saveStatus.textContent = result.created
                    ? 'City added to your saved list.'
                    : 'Already in your saved list.';
            }
        } catch (error) {
            if (selectedWeather === weather) {
                saveButton.disabled = false;
                saveStatus.textContent = (
                    error.message || 'Unable to save this city.'
                );
            }
        }
    }

    function formatTemperature(temperature) {
        const numericTemperature = Number(temperature);
        const displayedTemperature = Number.isFinite(numericTemperature)
            ? numericTemperature.toFixed(1)
            : temperature;
        return `${displayedTemperature}°F`;
    }

    function toTitleCase(value) {
        return value.toLowerCase().replace(
            /\b\w/g,
            (character) => character.toUpperCase(),
        );
    }
})();
