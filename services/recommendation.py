from database.db import list_destinations, MOOD_KEYWORDS


def _as_text(value):
    if isinstance(value, (list, tuple, set)):
        return ' '.join(str(v) for v in value)
    return str(value or '')


def rank_destinations(profile, duration=5, search_history=None):
    """Hybrid scoring: budget 30%, interest match 30%, distance 15%, weather 10%,
    ratings 10%, travel history 5%. Interest/history are boosted when the traveler's
    mood prompt or recent searches match a destination's category (lightweight
    content-based personalization)."""
    dataset = list_destinations()
    budget = _safe_int(profile.get('budget'), 30000)

    signal_text = ' '.join(filter(None, [
        _as_text(profile.get('mood_prompt')), _as_text(profile.get('interests')),
        _as_text(profile.get('destination_preference')),
        *(search_history or []),
    ])).lower()
    matched_categories = {category for keyword, category in MOOD_KEYWORDS.items() if keyword in signal_text}

    results = []
    for item in dataset:
        budget_score = max(0, 1 - abs(item['budget'] - budget) / max(1, budget))
        interest_score = item['interest_match']
        history_score = item['history']
        matched = item['category'] in matched_categories
        if matched:
            interest_score = min(1.0, interest_score + 0.15)
            history_score = min(1.0, history_score + 0.2)
        score = (
            0.30 * budget_score +
            0.30 * interest_score +
            0.15 * item['distance'] +
            0.10 * item['weather'] +
            0.10 * (item['rating'] / 5) +
            0.05 * history_score
        )
        results.append({**item, 'score': round(score, 3), 'mood_matched': matched})
    return sorted(results, key=lambda d: d['score'], reverse=True)


def _safe_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


SLOT_TEMPLATES = {
    'morning': 'Start the day exploring {attraction} and soaking in {name}\'s morning atmosphere.',
    'afternoon': 'Enjoy curated {state} experiences, local cuisine, and a visit to {attraction}.',
    'evening': 'Relax at a scenic viewpoint near {name} and browse the local markets.',
    'night': 'Check in to a recommended stay in {name} and rest ahead of the next day.',
}


def build_itinerary(ranked, form_data):
    duration = _safe_int(form_data.get('duration'), 3)
    duration = max(1, min(duration, 7))
    itinerary = []
    for day in range(1, duration + 1):
        destination = ranked[(day - 1) % len(ranked)] if ranked else None
        if not destination:
            continue
        attractions = destination.get('nearby_attractions') or ['Information unavailable.']
        attraction = attractions[(day - 1) % len(attractions)]
        itinerary.append({
            'day': day,
            'destination': destination['name'],
            'morning': SLOT_TEMPLATES['morning'].format(attraction=attraction, name=destination['name']),
            'afternoon': SLOT_TEMPLATES['afternoon'].format(state=destination['state'], attraction=attraction),
            'evening': SLOT_TEMPLATES['evening'].format(name=destination['name']),
            'night': SLOT_TEMPLATES['night'].format(name=destination['name']),
            'budget': destination['budget'],
            'reason': f"Rated highly for {form_data.get('travel_type', 'balanced')} travel style and matching budget.",
        })
    return itinerary


def build_budget_breakdown(ranked, form_data):
    total = _safe_int(form_data.get('budget'), ranked[0]['budget'] if ranked else 30000)
    weights = {
        'Accommodation': 0.32,
        'Transport': 0.20,
        'Food': 0.18,
        'Entry Tickets': 0.10,
        'Shopping': 0.10,
        'Emergency Reserve': 0.10,
    }
    breakdown = {label: round(total * weight) for label, weight in weights.items()}
    spent = sum(breakdown.values())
    return {
        'total': total,
        'categories': breakdown,
        'remaining': max(0, total - spent),
    }


def build_packing_list(ranked, form_data):
    destination = ranked[0] if ranked else None
    base = ['Comfortable walking shoes', 'Reusable water bottle', 'Power bank', 'ID proof / documents', 'First-aid essentials']
    if destination and destination['weather_text'] in ('Cold',):
        base += ['Thermal jacket', 'Woolen cap and gloves']
    elif destination and destination['weather_text'] in ('Sunny', 'Warm'):
        base += ['Sunscreen', 'Sunglasses', 'Light cotton clothing']
    elif destination and destination['weather_text'] == 'Humid':
        base += ['Rain jacket', 'Insect repellent']
    if form_data.get('adventure_level') == 'High':
        base.append('Sports/trekking gear')
    return base
