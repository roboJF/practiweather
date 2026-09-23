(() => {
    const list = document.querySelector('.saved-list');
    if (!list) {
        return;
    }

    const csrfToken = list.querySelector('[name=csrfmiddlewaretoken]').value;
    list.querySelectorAll('.saved-temperature').forEach(async (element) => {
        try {
            const response = await fetch(list.dataset.weatherUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken,
                },
                body: new URLSearchParams({
                    latitude: element.dataset.latitude,
                    longitude: element.dataset.longitude,
                }),
            });
            if (!response.ok) {
                return;
            }

            const {weather_data: weather} = await response.json();
            if (typeof weather.temperature === 'number'
                && Number.isFinite(weather.temperature)) {
                element.textContent = `${Math.round(weather.temperature)}°F`;
            }
        } catch (error) {
            // Keep the city available when its weather cannot be loaded.
        }
    });
})();
