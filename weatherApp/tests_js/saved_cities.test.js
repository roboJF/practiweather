const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const script = fs.readFileSync(
    path.join(__dirname, '..', 'static', 'weatherApp', 'saved_cities.js'),
    'utf8',
);

test('saved cities display only rounded temperatures beside their names', async () => {
    const requests = [];
    const temperatures = [
        {dataset: {latitude: '35.227200', longitude: '-80.843100'}, textContent: ''},
        {dataset: {latitude: '42.360000', longitude: '-71.060000'}, textContent: ''},
    ];
    const list = {
        dataset: {weatherUrl: '/weather/coordinates/'},
        querySelector: () => ({value: 'csrf-token'}),
        querySelectorAll: () => temperatures,
    };

    vm.runInNewContext(script, {
        document: {querySelector: () => list},
        URLSearchParams,
        fetch: async (url, options) => {
            requests.push({url, options});
            const temperature = options.body.get('latitude') === '35.227200'
                ? 72.6 : 48.2;
            return {
                ok: true,
                json: async () => ({weather_data: {temperature}}),
            };
        },
    });
    await new Promise(setImmediate);

    assert.equal(requests.length, 2);
    assert.equal(requests[0].url, '/weather/coordinates/');
    assert.equal(requests[0].options.headers['X-CSRFToken'], 'csrf-token');
    assert.equal(requests[0].options.body.get('longitude'), '-80.843100');
    assert.equal(temperatures[0].textContent, '73°F');
    assert.equal(temperatures[1].textContent, '48°F');
});

test('unavailable weather leaves the city name unchanged', async () => {
    const temperature = {
        dataset: {latitude: '35.227200', longitude: '-80.843100'},
        textContent: '',
    };
    const list = {
        dataset: {weatherUrl: '/weather/coordinates/'},
        querySelector: () => ({value: 'csrf-token'}),
        querySelectorAll: () => [temperature],
    };

    vm.runInNewContext(script, {
        document: {querySelector: () => list},
        URLSearchParams,
        fetch: async () => ({
            ok: true,
            json: async () => ({weather_data: {temperature: 'N/A'}}),
        }),
    });
    await new Promise(setImmediate);

    assert.equal(temperature.textContent, '');
});
