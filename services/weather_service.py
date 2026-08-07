import os

import requests

OPENWEATHER_URL = 'https://api.openweathermap.org/data/2.5/weather'


def _fallback_snapshot(city):
    return {
        'city': city,
        'temperature': 26,
        'humidity': 65,
        'forecast': 'Sunny with occasional clouds.',
        'rain_alert': False,
        'icon': 'fa-cloud-sun',
        'source': 'fallback',
    }


def get_weather_snapshot(city):
    api_key = os.getenv('WEATHER_API_KEY', '')
    if not api_key:
        return _fallback_snapshot(city)

    try:
        response = requests.get(
            OPENWEATHER_URL,
            params={'q': city, 'appid': api_key, 'units': 'metric'},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
        condition = (data.get('weather') or [{}])[0]
        main = condition.get('main', 'Clear')
        rain_alert = main.lower() in ('rain', 'thunderstorm', 'drizzle')
        icon_map = {
            'Clear': 'fa-sun', 'Clouds': 'fa-cloud', 'Rain': 'fa-cloud-showers-heavy',
            'Thunderstorm': 'fa-bolt', 'Snow': 'fa-snowflake', 'Drizzle': 'fa-cloud-rain',
        }
        return {
            'city': data.get('name', city),
            'temperature': round(data['main']['temp']),
            'humidity': data['main']['humidity'],
            'forecast': condition.get('description', main).capitalize(),
            'rain_alert': rain_alert,
            'icon': icon_map.get(main, 'fa-cloud-sun'),
            'source': 'openweather',
        }
    except Exception:
        return _fallback_snapshot(city)
