const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const script = fs.readFileSync(
    path.join(__dirname, '..', 'static', 'weatherApp', 'weather.js'),
    'utf8',
);

function startPage() {
    const requests = [];
    const handlers = {};
    const elements = {
        citySearchForm: {
            dataset: {weatherUrl: '/weather/city/'},
            querySelector: () => ({value: 'csrf-token'}),
            addEventListener: (name, handler) => { handlers[name] = handler; },
        },
        citySearch: {value: ''},
        weatherMap: {dataset: {weatherUrl: '/weather/coordinates/'}},
        mapStatus: {textContent: ''},
        cityName: {textContent: ''},
        temperature: {textContent: ''},
        conditions: {textContent: ''},
    };
    const geolocation = {};
    const context = {
        document: {getElementById: (id) => elements[id]},
        navigator: {
            geolocation: {
                getCurrentPosition: (success, failure) => {
                    geolocation.success = success;
                    geolocation.failure = failure;
                },
            },
        },
        URLSearchParams,
        AbortController,
        fetch: async (url, options) => {
            requests.push({url, options});
            return {
                ok: true,
                json: async () => ({
                    weather_data: {
                        city: 'Boston',
                        temperature: 70.25,
                        conditions: 'clear sky',
                        latitude: 42.36,
                        longitude: -71.06,
                    },
                }),
            };
        },
    };

    vm.runInNewContext(script, context);
    return {elements, geolocation, handlers, requests};
}

test('city search prevents navigation and updates the page from JSON', async () => {
    const page = startPage();
    page.elements.citySearch.value = '  Boston  ';
    let prevented = false;

    page.handlers.submit({preventDefault: () => { prevented = true; }});
    await new Promise(setImmediate);

    assert.equal(prevented, true);
    assert.equal(page.requests.length, 1);
    assert.equal(page.requests[0].url, '/weather/city/');
    assert.equal(page.requests[0].options.method, 'POST');
    assert.equal(page.requests[0].options.headers['X-CSRFToken'], 'csrf-token');
    assert.equal(page.requests[0].options.body.get('city'), '  Boston  ');
    assert.equal(page.elements.cityName.textContent, 'Boston');
    assert.equal(page.elements.temperature.textContent, '70.3°F');
    assert.equal(page.elements.conditions.textContent, 'Clear Sky');
});

test('initial location falls back to the city endpoint when denied', async () => {
    const page = startPage();

    page.geolocation.failure();
    await new Promise(setImmediate);

    assert.equal(page.requests.length, 1);
    assert.equal(page.requests[0].url, '/weather/city/');
    assert.equal(page.requests[0].options.body.get('city'), '');
    assert.equal(page.elements.cityName.textContent, 'Boston');
});

test('initial browser location uses the coordinate endpoint', async () => {
    const page = startPage();

    page.geolocation.success({
        coords: {latitude: 42.36, longitude: -71.06},
    });
    await new Promise(setImmediate);

    assert.equal(page.requests.length, 1);
    assert.equal(page.requests[0].url, '/weather/coordinates/');
    assert.equal(page.requests[0].options.body.get('latitude'), '42.36');
    assert.equal(page.requests[0].options.body.get('longitude'), '-71.06');
});

test('search submitted during geolocation is not replaced by its result', async () => {
    const page = startPage();
    page.elements.citySearch.value = 'Boston';

    page.handlers.submit({preventDefault() {}});
    page.geolocation.success({
        coords: {latitude: 42.36, longitude: -71.06},
    });
    await new Promise(setImmediate);

    assert.equal(page.requests.length, 1);
    assert.equal(page.requests[0].url, '/weather/city/');
});
