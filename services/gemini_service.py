import json
import os
import sys

from database.db import list_hotels, list_restaurants
from services.recommendation import build_budget_breakdown, build_packing_list

PROMPT_TEMPLATE = """You are a travel planning assistant. You must only use the destination data
provided below as grounding. Never invent facts, hotels, or attractions that are not present
in the data. If something cannot be determined from the data, use the exact string
"Information unavailable." for that value instead of guessing.

Traveler preferences (raw form input):
{preferences}

Ranked candidate destinations (already scored 0-1 by a hybrid recommendation engine that
weighs budget 30%, interest match 30%, distance 15%, weather 10%, ratings 10%, travel
history 5%; the first item is the top match):
{dataset}

Respond with strict JSON only, no markdown fences, matching exactly this shape:
{{
  "trip_summary": "one sentence summary of the recommended trip",
  "confidence_score": 0.0,
  "why_selected": ["reason 1", "reason 2", "reason 3"],
  "alternative_destinations": ["name of 2nd best match", "name of 3rd best match"],
  "safety_note": "one short safety or advisory note"
}}
"""


def _fallback_narrative(form_data, ranked):
    top = ranked[0]
    travel_type = form_data.get('travel_type', 'custom')
    return {
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


def _gemini_narrative(form_data, ranked, api_key, model_name):
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    dataset = [
        {k: d[k] for k in ('name', 'state', 'category', 'budget', 'rating', 'weather_text', 'nearby_attractions', 'score')}
        for d in ranked[:5]
    ]
    prompt = PROMPT_TEMPLATE.format(
        preferences=json.dumps(form_data),
        dataset=json.dumps(dataset),
    )
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"},
    )
    data = json.loads(response.text)

    required = {'trip_summary', 'confidence_score', 'why_selected', 'alternative_destinations', 'safety_note'}
    if not required.issubset(data):
        raise ValueError('Gemini response missing required fields')
    return data


def build_ai_plan(form_data, ranked):
    if not ranked:
        return {
            'trip_summary': 'Information unavailable.',
            'confidence_score': 0,
            'why_selected': ['Information unavailable.'],
            'alternative_destinations': [],
            'safety_note': 'Information unavailable.',
            'packing_list': [],
            'local_customs': [],
            'emergency_numbers': {'Police': '100', 'Ambulance': '108', 'Tourist Helpline': '1363'},
            'hotel_recommendations': [],
            'restaurant_recommendations': [],
            'source': 'unavailable',
        }

    api_key = os.getenv('GEMINI_API_KEY', '')
    model_name = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')

    source = 'fallback'
    if api_key:
        try:
            narrative = _gemini_narrative(form_data, ranked, api_key, model_name)
            source = 'gemini'
        except Exception as exc:
            print(f"[gemini_service] Falling back to local narrative: {exc}", file=sys.stderr)
            narrative = _fallback_narrative(form_data, ranked)
    else:
        narrative = _fallback_narrative(form_data, ranked)

    top = ranked[0]
    hotels = list_hotels(top['id'])
    restaurants = list_restaurants(top['id'])
    accommodation_pref = form_data.get('accommodation', '')
    matching_hotels = [h for h in hotels if h['category'] == accommodation_pref] or hotels

    return {
        **narrative,
        'packing_list': build_packing_list(ranked, form_data),
        'local_customs': [
            'Dress modestly when visiting religious or historical sites.',
            'Negotiate prices politely at local markets.',
            'Carry small cash for local vendors and rural areas.',
        ],
        'emergency_numbers': {'Police': '100', 'Ambulance': '108', 'Tourist Helpline': '1363'},
        'budget_breakdown': build_budget_breakdown(ranked, form_data),
        'hotel_recommendations': matching_hotels[:3],
        'restaurant_recommendations': restaurants[:3],
        'source': source,
    }
