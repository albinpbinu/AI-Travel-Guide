import json
import os
import sys

from database.db import list_hotels, list_restaurants
from services.recommendation import (
    _safe_int, _safe_float, build_budget_breakdown, build_packing_list, build_itinerary,
    rank_destinations, resolve_start_date, resolve_duration,
)


def _env_int(name, default):
    try:
        return int(os.getenv(name, '') or default)
    except ValueError:
        return default


PROMPT_TEMPLATE = """You are an expert travel planner. Suggest real, well-known destinations that
genuinely fit the traveler's preferences below, then build a PRACTICAL day-by-day itinerary.

Practicality rules (important):
- Only schedule activities that are geographically close enough to fit in the same time slot;
  do not put attractions on opposite sides of a region back-to-back without travel time.
- Respect the traveler's preferred pace if given (relaxed = 1-2 activities/day, balanced = 2-3,
  packed = 3-4).
- If the trip is longer than a few days and more than one destination genuinely fits, split the
  days across them logically (e.g. days 1-3 in one place, days 4-5 in another) rather than
  forcing every single day into one destination.
- Use the exact start date given below for day 1, and increment by one calendar day for each
  subsequent day, formatted YYYY-MM-DD.
- Keep budget estimates realistic for the destinations, trip length, and traveler count.
- Real, well-known hotel/restaurant names are fine to suggest; don't invent hyper-specific
  unverifiable details (e.g. an exact founding year) — use a realistic generic description if unsure.
- The "itinerary" array must contain exactly {duration} entries, one per day, no more, no fewer.

Traveler preferences (raw form input, may include budget, starting location, travel type,
transportation, accommodation, food preference, adventure level, pace, accessibility needs,
languages, interests, a free-text mood description, and special requests):
{preferences}

Trip length: {duration} day(s), starting {start_date}.

Respond with strict JSON only, no markdown fences, matching exactly this shape:
{{
  "destinations": [
    {{"name": "...", "state": "...", "category": "Hill Station|Beach|Historical|Adventure|Nature|Wildlife|Religious|Shopping|Food",
      "lat": 0.0, "lng": 0.0, "rating": 4.5, "weather_text": "Pleasant|Sunny|Warm|Cold|Humid",
      "description": "...", "nearby_attractions": ["...", "..."], "budget": 0, "why_included": "..."}}
  ],
  "itinerary": [
    {{"day": 1, "date": "YYYY-MM-DD", "destination": "...", "morning": "...", "afternoon": "...",
      "evening": "...", "night": "...", "reason": "..."}}
  ],
  "hotel_recommendations": [
    {{"name": "...", "category": "Budget|Luxury|Hostel|Resort|Camping", "price_per_night": 0, "rating": 4.5}}
  ],
  "restaurant_recommendations": [
    {{"name": "...", "cuisine": "...", "price_range": "Budget|Mid|Premium", "rating": 4.5}}
  ],
  "trip_summary": "one or two sentence summary of the recommended trip",
  "confidence_score": 0.0,
  "why_selected": ["reason 1", "reason 2", "reason 3"],
  "alternative_destinations": ["alternative destination 1", "alternative destination 2"],
  "safety_note": "one short safety or advisory note"
}}
"""

# "gemini-flash-latest" now resolves to a reasoning model that spends 110s+ on a
# full itinerary — far longer than a serverless request can live, so the function
# was timing out before anything rendered. The lite model returns the same shape
# in ~5s. Override with GEMINI_MODEL if you want to trade speed for depth.
DEFAULT_MODEL = 'gemini-flash-lite-latest'

# Hard ceiling on a single Gemini call. Without one the SDK waits indefinitely,
# so a slow call hangs the whole request instead of falling back to the local
# engine. Must stay comfortably under the hosting platform's request timeout.
PLAN_TIMEOUT_SECONDS = _env_int('GEMINI_TIMEOUT', 25)
CHAT_TIMEOUT_SECONDS = _env_int('GEMINI_CHAT_TIMEOUT', 15)

EMERGENCY_NUMBERS = {'Police': '100', 'Ambulance': '108', 'Tourist Helpline': '1363'}
LOCAL_CUSTOMS = [
    'Dress modestly when visiting religious or historical sites.',
    'Negotiate prices politely at local markets.',
    'Carry small cash for local vendors and rural areas.',
]


def _unavailable_plan():
    return {
        'trip_summary': 'Information unavailable.',
        'confidence_score': 0,
        'why_selected': ['Information unavailable.'],
        'alternative_destinations': [],
        'safety_note': 'Information unavailable.',
        'packing_list': [],
        'local_customs': [],
        'emergency_numbers': EMERGENCY_NUMBERS,
        'hotel_recommendations': [],
        'restaurant_recommendations': [],
        'destinations': [],
        'itinerary': [],
        'budget_breakdown': {'total': 0, 'categories': {}, 'remaining': 0},
        'source': 'unavailable',
    }


def _assemble(narrative, itinerary, destinations, hotels, restaurants, form_data, source):
    return {
        **narrative,
        'itinerary': itinerary,
        'destinations': destinations,
        'packing_list': build_packing_list(destinations, form_data),
        'local_customs': LOCAL_CUSTOMS,
        'emergency_numbers': EMERGENCY_NUMBERS,
        'budget_breakdown': build_budget_breakdown(destinations, form_data),
        'hotel_recommendations': hotels,
        'restaurant_recommendations': restaurants,
        'source': source,
    }


def _fallback_plan(form_data, search_history):
    """Deterministic, local-database-driven plan used when Gemini is unavailable
    or fails. Limited to the internal destination dataset."""
    ranked = rank_destinations(form_data, duration=resolve_duration(form_data), search_history=search_history)
    if not ranked:
        return _unavailable_plan()

    top = ranked[0]
    travel_type = form_data.get('travel_type', 'custom')
    itinerary = build_itinerary(ranked, form_data)
    hotels = list_hotels(top['id'])
    restaurants = list_restaurants(top['id'])
    accommodation_pref = form_data.get('accommodation', '')
    matching_hotels = [h for h in hotels if h['category'] == accommodation_pref] or hotels

    narrative = {
        'trip_summary': f"AI-generated recommendation for a {travel_type} trip to {top['name']}, {top['state']}.",
        'confidence_score': round(min(0.97, top['score'] + 0.1), 2),
        'why_selected': [
            f"Budget alignment is strong for a ₹{form_data.get('budget', top['budget'])} preference.",
            f"{top['name']} scores {top['rating']}/5 with high {top['category'].lower()} interest match.",
            f"Weather ({top['weather_text']}) and popularity signals support an enjoyable itinerary.",
        ],
        'alternative_destinations': [d['name'] for d in ranked[1:3]],
        'safety_note': 'Follow local advisories and keep emergency contacts handy.',
    }
    return _assemble(narrative, itinerary, ranked, matching_hotels[:3], restaurants[:3], form_data, source='fallback')


def _gemini_plan(form_data, api_key, model_name):
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    duration = resolve_duration(form_data)
    start_date = resolve_start_date(form_data)
    prompt = PROMPT_TEMPLATE.format(
        preferences=json.dumps(form_data),
        duration=duration,
        start_date=start_date.strftime('%Y-%m-%d'),
    )
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"},
        request_options={"timeout": PLAN_TIMEOUT_SECONDS},
    )
    data = json.loads(response.text)

    required = {'destinations', 'itinerary', 'trip_summary', 'confidence_score', 'why_selected',
                'alternative_destinations', 'safety_note'}
    if not required.issubset(data) or not data['destinations'] or not data['itinerary']:
        raise ValueError('Gemini response missing required fields')

    default_budget = _safe_int(form_data.get('budget'), 30000)
    destinations = [
        {
            'name': d.get('name') or 'Information unavailable.',
            'state': d.get('state', ''),
            'category': d.get('category', ''),
            'lat': _safe_float(d.get('lat'), None),
            'lng': _safe_float(d.get('lng'), None),
            'rating': _safe_float(d.get('rating'), 4.5),
            'weather_text': d.get('weather_text') or 'Pleasant',
            'description': d.get('description', ''),
            'nearby_attractions': d.get('nearby_attractions') or [],
            'budget': _safe_int(d.get('budget'), default_budget),
            'why_included': d.get('why_included', ''),
        }
        for d in data['destinations']
    ]

    hotels = [
        {
            'name': h.get('name') or 'Information unavailable.',
            'category': h.get('category', ''),
            'price_per_night': _safe_int(h.get('price_per_night'), 0),
            'rating': _safe_float(h.get('rating'), 4.5),
        }
        for h in (data.get('hotel_recommendations') or [])[:3]
    ]
    restaurants = [
        {
            'name': r.get('name') or 'Information unavailable.',
            'cuisine': r.get('cuisine', ''),
            'price_range': r.get('price_range', ''),
            'rating': _safe_float(r.get('rating'), 4.5),
        }
        for r in (data.get('restaurant_recommendations') or [])[:3]
    ]

    itinerary = [
        {
            'day': _safe_int(item.get('day'), index + 1),
            'date': item.get('date', ''),
            'destination': item.get('destination') or 'Information unavailable.',
            'morning': item.get('morning', 'Information unavailable.'),
            'afternoon': item.get('afternoon', 'Information unavailable.'),
            'evening': item.get('evening', 'Information unavailable.'),
            'night': item.get('night', 'Information unavailable.'),
            'reason': item.get('reason', ''),
        }
        for index, item in enumerate(data['itinerary'])
    ]

    narrative = {
        'trip_summary': data.get('trip_summary') or 'Information unavailable.',
        'confidence_score': _safe_float(data.get('confidence_score'), 0.75),
        'why_selected': data.get('why_selected') or [],
        'alternative_destinations': data.get('alternative_destinations') or [],
        'safety_note': data.get('safety_note') or 'Follow local advisories and keep emergency contacts handy.',
    }
    return _assemble(narrative, itinerary, destinations, hotels, restaurants, form_data, source='gemini')


def build_ai_plan(form_data, search_history=None):
    api_key = os.getenv('GEMINI_API_KEY', '')
    model_name = os.getenv('GEMINI_MODEL') or DEFAULT_MODEL

    if api_key:
        try:
            return _gemini_plan(form_data, api_key, model_name)
        except Exception as exc:
            print(f"[gemini_service] Falling back to local engine: {exc}", file=sys.stderr)

    return _fallback_plan(form_data, search_history)


def chat_reply(message, history=None):
    """Real Gemini-backed travel assistant reply, with a lightweight canned
    fallback if no key is configured or the call fails."""
    api_key = os.getenv('GEMINI_API_KEY', '')
    if not api_key:
        return _chat_fallback(message)

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model_name = os.getenv('GEMINI_MODEL') or DEFAULT_MODEL
        model = genai.GenerativeModel(
            model_name,
            system_instruction=(
                "You are a concise, friendly travel assistant for TravelGuide AI. "
                "Answer questions about itineraries, packing, weather, budgets, and safety. "
                "Keep replies short (2-4 sentences) and practical. If asked something unrelated "
                "to travel, gently redirect to travel topics."
            ),
        )
        chat = model.start_chat(history=history or [])
        response = chat.send_message(
            message, request_options={"timeout": CHAT_TIMEOUT_SECONDS}
        )
        return response.text.strip()
    except Exception as exc:
        print(f"[gemini_service] Chat falling back: {exc}", file=sys.stderr)
        return _chat_fallback(message)


def _chat_fallback(message):
    lower = message.lower()
    if 'weather' in lower:
        return 'Check the weather widget on your dashboard for live forecasts and packing tips.'
    if 'budget' in lower:
        return 'Your itinerary page has a full budget breakdown with hotel, food, transport and ticket costs.'
    if 'pack' in lower:
        return "Your packing list adapts to the destination's weather and trip duration — see the itinerary page."
    if 'emergency' in lower or 'safety' in lower:
        return 'Emergency numbers and safety notes are included with every generated itinerary.'
    return 'I can help with itinerary questions, packing, weather, and budget — ask away!'
