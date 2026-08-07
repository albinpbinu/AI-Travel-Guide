import requests

OVERPASS_URL = 'https://overpass-api.de/api/interpreter'

POI_CATEGORIES = {
    'Hospitals': ('amenity', 'hospital', 'fa-hospital'),
    'Police Stations': ('amenity', 'police', 'fa-shield-halved'),
    'ATMs': ('amenity', 'atm', 'fa-money-bill-wave'),
    'Fuel Stations': ('amenity', 'fuel', 'fa-gas-pump'),
}


def get_nearby_essentials(lat, lng, radius=4000, timeout=6):
    """Live lookup of nearby essentials via the public OpenStreetMap Overpass API.
    Returns None (never fabricated data) if coordinates are missing or the
    lookup fails/times out, so the caller can show 'Information unavailable.'"""
    if lat is None or lng is None:
        return None

    filters = ''.join(
        f'node["{tag_key}"="{tag_value}"](around:{radius},{lat},{lng});'
        for tag_key, tag_value, _ in POI_CATEGORIES.values()
    )
    query = f'[out:json][timeout:{timeout}];({filters});out center 20;'

    try:
        response = requests.post(OVERPASS_URL, data={'data': query}, timeout=timeout)
        response.raise_for_status()
        elements = response.json().get('elements', [])
    except Exception:
        return None

    results = {label: [] for label in POI_CATEGORIES}
    for element in elements:
        tags = element.get('tags', {})
        for label, (tag_key, tag_value, icon) in POI_CATEGORIES.items():
            if tags.get(tag_key) == tag_value and len(results[label]) < 4:
                results[label].append({'name': tags.get('name', 'Unnamed'), 'icon': icon})
    return results
