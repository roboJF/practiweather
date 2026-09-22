(() => {
    const mapElement = document.getElementById('weatherMap');
    const statusElement = document.getElementById('mapStatus');

    if (!mapElement || typeof maplibregl === 'undefined') {
        if (statusElement) {
            statusElement.textContent = 'The map could not be loaded.';
        }
        return;
    }

    const initialLatitude = Number.parseFloat(mapElement.dataset.latitude);
    const initialLongitude = Number.parseFloat(mapElement.dataset.longitude);
    const hasInitialLocation = (
        Number.isFinite(initialLatitude) && Number.isFinite(initialLongitude)
    );
    const initialCenter = hasInitialLocation
        ? [initialLongitude, initialLatitude]
        : [-98.5795, 39.8283];

    const map = new maplibregl.Map({
        container: mapElement,
        style: 'https://tiles.openfreemap.org/styles/positron',
        center: initialCenter,
        zoom: hasInitialLocation ? 8 : 4,
        attributionControl: true,
    });
    map.addControl(new maplibregl.NavigationControl(), 'top-right');

    let marker = hasInitialLocation
        ? new maplibregl.Marker().setLngLat(initialCenter).addTo(map)
        : null;
    let activeRequest = null;
    let hasUserInteracted = false;

    map.on('click', (event) => {
        hasUserInteracted = true;
        setMarker(event.lngLat.lng, event.lngLat.lat);
        loadWeather(event.lngLat.lat, event.lngLat.lng);
    });

    if (mapElement.dataset.useBrowserLocation === 'true') {
        locateUser();
    }

    function locateUser() {
        if (!navigator.geolocation) {
            statusElement.textContent = (
                'Using your approximate location. Click the map to explore.'
            );
            return;
        }

        statusElement.textContent = 'Finding your location...';
        navigator.geolocation.getCurrentPosition(
            (position) => {
                if (hasUserInteracted) {
                    return;
                }

                const latitude = position.coords.latitude;
                const longitude = position.coords.longitude;
                map.flyTo({center: [longitude, latitude], zoom: 8});
                setMarker(longitude, latitude);
                loadWeather(latitude, longitude);
            },
            () => {
                statusElement.textContent = (
                    'Using your approximate location. Click the map to explore.'
                );
            },
            {
                enableHighAccuracy: false,
                timeout: 10000,
                maximumAge: 300000,
            },
        );
    }

    function setMarker(longitude, latitude) {
        const coordinates = [longitude, latitude];
        if (marker) {
            marker.setLngLat(coordinates);
        } else {
            marker = new maplibregl.Marker()
                .setLngLat(coordinates)
                .addTo(map);
        }
    }

    async function loadWeather(latitude, longitude) {
        if (activeRequest) {
            activeRequest.abort();
        }
        activeRequest = new AbortController();
        statusElement.textContent = 'Loading weather...';

        const requestBody = new URLSearchParams({
            latitude: latitude.toString(),
            longitude: longitude.toString(),
        });
        const csrfToken = document.querySelector(
            '[name=csrfmiddlewaretoken]',
        ).value;

        try {
            const response = await fetch(mapElement.dataset.weatherUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken,
                },
                body: requestBody,
                signal: activeRequest.signal,
            });
            const payload = await response.json();

            if (!response.ok) {
                throw new Error(payload.error || 'Unable to load weather.');
            }

            updateWeather(payload.weather_data);
            statusElement.textContent = payload.weather_data.temperature === 'N/A'
                ? payload.weather_data.conditions
                : `Weather updated for ${payload.weather_data.city}.`;
        } catch (error) {
            if (error.name !== 'AbortError') {
                statusElement.textContent = (
                    error.message || 'Unable to load weather.'
                );
            }
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
